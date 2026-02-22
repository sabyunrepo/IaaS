"""
Posting Repository — 채용 공고 CRUD.

psycopg_pool AsyncConnectionPool 기반. 기존 repository.py 패턴 준수.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from infrastructure.persistence.pool import get_pool


class PostingRepository:
    """postings 테이블 CRUD."""

    async def create(
        self,
        user_id: str,
        title: str,
        department: str | None = None,
        jd_description: str | None = None,
        jd_languages: list[str] | None = None,
        jd_tech_stack: list[str] | None = None,
        jd_experience_years: int | None = None,
        auto_analyze: bool = False,
        status: str = "draft",
    ) -> str:
        """새 채용 공고를 생성하고 UUID를 반환한다."""
        posting_id = str(uuid.uuid4())
        async with get_pool().connection() as conn:
            await conn.execute(
                """
                INSERT INTO postings (id, user_id, title, department, jd_description,
                    jd_languages, jd_tech_stack, jd_experience_years, auto_analyze, status)
                VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    posting_id,
                    user_id,
                    title,
                    department,
                    jd_description,
                    jd_languages or [],
                    jd_tech_stack or [],
                    jd_experience_years,
                    auto_analyze,
                    status,
                ),
            )
            await conn.commit()
        return posting_id

    async def get(self, posting_id: str) -> dict[str, Any] | None:
        """공고 ID로 조회한다."""
        async with get_pool().connection() as conn:
            row = await conn.execute(
                """
                SELECT id, user_id, title, department, jd_description,
                       jd_languages, jd_tech_stack, jd_experience_years,
                       auto_analyze, status, created_at, updated_at
                FROM postings WHERE id = %s::uuid
                """,
                (posting_id,),
            )
            result = await row.fetchone()
            if result is None:
                return None
            return self._row_to_dict(result)

    async def list_by_user(
        self, user_id: str, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """사용자의 공고 목록을 조회한다. application_count 포함."""
        query = """
            SELECT p.id, p.user_id, p.title, p.department, p.jd_description,
                   p.jd_languages, p.jd_tech_stack, p.jd_experience_years,
                   p.auto_analyze, p.status, p.created_at, p.updated_at,
                   COUNT(a.id) AS application_count
            FROM postings p
            LEFT JOIN applications a ON a.posting_id = p.id
            WHERE p.user_id = %s::uuid
        """
        params: list[Any] = [user_id]
        if status:
            query += " AND p.status = %s"
            params.append(status)
        query += """
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT %s
        """
        params.append(limit)
        async with get_pool().connection() as conn:
            rows = await conn.execute(query, params)
            results = []
            async for r in rows:
                d = self._row_to_dict(r)
                d["application_count"] = r[12]
                results.append(d)
            return results

    async def list_active_by_slug(self, company_slug: str) -> list[dict[str, Any]]:
        """회사 slug로 활성 공고 목록을 조회한다 (public careers 페이지)."""
        async with get_pool().connection() as conn:
            rows = await conn.execute(
                """
                SELECT p.id, p.user_id, p.title, p.department, p.jd_description,
                       p.jd_languages, p.jd_tech_stack, p.jd_experience_years,
                       p.auto_analyze, p.status, p.created_at, p.updated_at
                FROM postings p
                JOIN users u ON u.id = p.user_id
                WHERE u.company_slug = %s AND p.status = 'active'
                ORDER BY p.created_at DESC
                """,
                (company_slug,),
            )
            return [self._row_to_dict(r) async for r in rows]

    async def update(self, posting_id: str, **fields: Any) -> bool:
        """공고를 업데이트한다. 변경된 필드만 전달."""
        if not fields:
            return False
        allowed = {
            "title", "department", "jd_description", "jd_languages",
            "jd_tech_stack", "jd_experience_years", "auto_analyze", "status",
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
        params.append(posting_id)

        async with get_pool().connection() as conn:
            result = await conn.execute(
                f"UPDATE postings SET {', '.join(set_clauses)} WHERE id = %s::uuid",
                params,
            )
            await conn.commit()
            return result.rowcount > 0

    async def delete(self, posting_id: str) -> bool:
        """공고를 삭제한다."""
        async with get_pool().connection() as conn:
            result = await conn.execute(
                "DELETE FROM postings WHERE id = %s::uuid",
                (posting_id,),
            )
            await conn.commit()
            return result.rowcount > 0

    @staticmethod
    def _row_to_dict(row: tuple) -> dict[str, Any]:
        return {
            "id": str(row[0]),
            "user_id": str(row[1]),
            "title": row[2],
            "department": row[3],
            "jd_description": row[4],
            "jd_languages": row[5] or [],
            "jd_tech_stack": row[6] or [],
            "jd_experience_years": row[7],
            "auto_analyze": row[8],
            "status": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
            "updated_at": row[11].isoformat() if row[11] else None,
        }
