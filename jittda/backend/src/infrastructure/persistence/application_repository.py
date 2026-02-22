"""
Application Repository — 지원 CRUD.

psycopg_pool AsyncConnectionPool 기반. 기존 repository.py 패턴 준수.
"""

from __future__ import annotations

import uuid
from typing import Any

from infrastructure.persistence.pool import get_pool


class ApplicationRepository:
    """applications 테이블 CRUD."""

    async def create(
        self,
        posting_id: str,
        candidate_name: str | None = None,
        candidate_email: str | None = None,
        github_username: str | None = None,
        github_urls: list[str] | None = None,
        linkedin_url: str | None = None,
        resume_path: str | None = None,
        cover_letter_path: str | None = None,
        portfolio_path: str | None = None,
        memo: str | None = None,
        source: str = "admin_manual",
    ) -> str:
        """새 지원을 생성하고 UUID를 반환한다."""
        app_id = str(uuid.uuid4())
        async with get_pool().connection() as conn:
            await conn.execute(
                """
                INSERT INTO applications
                    (id, posting_id, candidate_name, candidate_email, github_username,
                     github_urls, linkedin_url, resume_path, cover_letter_path,
                     portfolio_path, memo, source)
                VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    app_id,
                    posting_id,
                    candidate_name,
                    candidate_email,
                    github_username,
                    github_urls or [],
                    linkedin_url,
                    resume_path,
                    cover_letter_path,
                    portfolio_path,
                    memo,
                    source,
                ),
            )
            await conn.commit()
        return app_id

    async def get(self, app_id: str) -> dict[str, Any] | None:
        """지원 ID로 조회한다."""
        async with get_pool().connection() as conn:
            row = await conn.execute(
                """
                SELECT id, posting_id, candidate_name, candidate_email, github_username,
                       github_urls, linkedin_url, resume_path, cover_letter_path,
                       portfolio_path, memo, source, status, job_id,
                       created_at, updated_at
                FROM applications WHERE id = %s::uuid
                """,
                (app_id,),
            )
            result = await row.fetchone()
            if result is None:
                return None
            return self._row_to_dict(result)

    async def list_by_posting(
        self, posting_id: str, status: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """공고별 지원 목록을 조회한다."""
        query = """
            SELECT id, posting_id, candidate_name, candidate_email, github_username,
                   github_urls, linkedin_url, resume_path, cover_letter_path,
                   portfolio_path, memo, source, status, job_id,
                   created_at, updated_at
            FROM applications WHERE posting_id = %s::uuid
        """
        params: list[Any] = [posting_id]
        if status:
            query += " AND status = %s"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        async with get_pool().connection() as conn:
            rows = await conn.execute(query, params)
            return [self._row_to_dict(r) async for r in rows]

    async def update(self, app_id: str, **fields: Any) -> bool:
        """지원 정보를 업데이트한다."""
        if not fields:
            return False
        allowed = {
            "candidate_name", "candidate_email", "github_username",
            "github_urls", "linkedin_url", "resume_path", "cover_letter_path",
            "portfolio_path", "memo", "status", "job_id",
        }
        filtered = {k: v for k, v in fields.items() if k in allowed}
        if not filtered:
            return False

        set_clauses = []
        params: list[Any] = []
        for key, val in filtered.items():
            set_clauses.append(f"{key} = %s")
            params.append(val)
        set_clauses.append("updated_at = NOW()")
        params.append(app_id)

        async with get_pool().connection() as conn:
            result = await conn.execute(
                f"UPDATE applications SET {', '.join(set_clauses)} WHERE id = %s::uuid",
                params,
            )
            await conn.commit()
            return result.rowcount > 0

    async def link_job(self, app_id: str, job_id: str) -> bool:
        """지원에 분석 Job을 연결한다."""
        return await self.update(app_id, job_id=job_id, status="analyzing")

    async def update_status(self, app_id: str, status: str) -> bool:
        """지원 상태를 업데이트한다."""
        return await self.update(app_id, status=status)

    async def delete(self, app_id: str) -> bool:
        """지원을 삭제한다."""
        async with get_pool().connection() as conn:
            result = await conn.execute(
                "DELETE FROM applications WHERE id = %s::uuid",
                (app_id,),
            )
            await conn.commit()
            return result.rowcount > 0

    @staticmethod
    def _row_to_dict(row: tuple) -> dict[str, Any]:
        return {
            "id": str(row[0]),
            "posting_id": str(row[1]),
            "candidate_name": row[2],
            "candidate_email": row[3],
            "github_username": row[4],
            "github_urls": row[5] or [],
            "linkedin_url": row[6],
            "resume_path": row[7],
            "cover_letter_path": row[8],
            "portfolio_path": row[9],
            "memo": row[10],
            "source": row[11],
            "status": row[12],
            "job_id": str(row[13]) if row[13] else None,
            "created_at": row[14].isoformat() if row[14] else None,
            "updated_at": row[15].isoformat() if row[15] else None,
        }


class FileUploadRepository:
    """file_uploads 테이블 CRUD."""

    async def save_metadata(
        self,
        uploader_type: str,
        uploader_ref: str | None,
        file_type: str,
        file_name: str,
        file_path: str,
        content_type: str | None = None,
        size_bytes: int | None = None,
    ) -> str:
        """파일 메타데이터를 저장하고 UUID를 반환한다."""
        upload_id = str(uuid.uuid4())
        async with get_pool().connection() as conn:
            await conn.execute(
                """
                INSERT INTO file_uploads
                    (id, uploader_type, uploader_ref, file_type, file_name,
                     file_path, content_type, size_bytes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    upload_id,
                    uploader_type,
                    uploader_ref,
                    file_type,
                    file_name,
                    file_path,
                    content_type,
                    size_bytes,
                ),
            )
            await conn.commit()
        return upload_id

    async def get_by_ref(
        self, uploader_ref: str, file_type: str | None = None
    ) -> list[dict[str, Any]]:
        """업로더 참조로 파일 목록을 조회한다."""
        query = """
            SELECT id, uploader_type, uploader_ref, file_type, file_name,
                   file_path, content_type, size_bytes, created_at
            FROM file_uploads WHERE uploader_ref = %s
        """
        params: list[Any] = [uploader_ref]
        if file_type:
            query += " AND file_type = %s"
            params.append(file_type)
        query += " ORDER BY created_at DESC"

        async with get_pool().connection() as conn:
            rows = await conn.execute(query, params)
            return [
                {
                    "id": str(r[0]),
                    "uploader_type": r[1],
                    "uploader_ref": r[2],
                    "file_type": r[3],
                    "file_name": r[4],
                    "file_path": r[5],
                    "content_type": r[6],
                    "size_bytes": r[7],
                    "created_at": r[8].isoformat() if r[8] else None,
                }
                async for r in rows
            ]
