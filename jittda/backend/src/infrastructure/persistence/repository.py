"""
Persistence Repository — Reference Passing 패턴 저장소.

노드가 분석 결과를 DB에 저장하고 UUID만 State에 반환하는 패턴의 핵심.
psycopg 3 async 기반 CRUD.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg


class UserRepository:
    """users 테이블 CRUD — OAuth 사용자 관리."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def upsert_oauth_user(
        self,
        email: str,
        name: str,
        oauth_provider: str,
        oauth_id: str,
    ) -> dict[str, Any]:
        """OAuth 사용자를 생성하거나 기존 사용자를 반환한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            row = await conn.execute(
                """
                INSERT INTO users (email, name, oauth_provider, oauth_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    name = EXCLUDED.name,
                    oauth_provider = EXCLUDED.oauth_provider,
                    oauth_id = EXCLUDED.oauth_id
                RETURNING id, email, name, oauth_provider
                """,
                (email, name, oauth_provider, oauth_id),
            )
            result = await row.fetchone()
            return {
                "id": str(result[0]),
                "email": result[1],
                "name": result[2],
                "oauth_provider": result[3],
            }

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        """사용자 ID로 조회한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            row = await conn.execute(
                "SELECT id, email, name, oauth_provider FROM users WHERE id = %s::uuid",
                (user_id,),
            )
            result = await row.fetchone()
            if result is None:
                return None
            return {
                "id": str(result[0]),
                "email": result[1],
                "name": result[2],
                "oauth_provider": result[3],
            }


class AnalysisRepository:
    """analysis_results 테이블 CRUD — Worker별 분석 결과 저장소."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def save_result(
        self,
        job_id: str,
        worker_name: str,
        supervisor_name: str,
        result_data: dict[str, Any],
        metrics: dict[str, Any] | None = None,
    ) -> str:
        """분석 결과를 DB에 저장하고 UUID를 반환한다."""
        result_id = str(uuid.uuid4())
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute(
                """
                INSERT INTO analysis_results (id, job_id, worker_name, supervisor_name, result_data, metrics)
                VALUES (%s, %s::uuid, %s, %s, %s::jsonb, %s::jsonb)
                """,
                (
                    result_id,
                    job_id,
                    worker_name,
                    supervisor_name,
                    json.dumps(result_data, default=str),
                    json.dumps(metrics, default=str) if metrics else None,
                ),
            )
        return result_id

    async def get_result(self, result_id: str) -> dict[str, Any] | None:
        """UUID로 분석 결과를 조회한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            row = await conn.execute(
                "SELECT result_data, metrics FROM analysis_results WHERE id = %s",
                (result_id,),
            )
            result = await row.fetchone()
            if result is None:
                return None
            return {"result_data": result[0], "metrics": result[1]}

    async def get_results_by_job(
        self, job_id: str, supervisor_name: str | None = None
    ) -> list[dict[str, Any]]:
        """Job ID로 분석 결과 목록을 조회한다."""
        query = "SELECT id, worker_name, supervisor_name, result_data, metrics FROM analysis_results WHERE job_id = %s::uuid"
        params: list[Any] = [job_id]
        if supervisor_name:
            query += " AND supervisor_name = %s"
            params.append(supervisor_name)
        query += " ORDER BY created_at"
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            rows = await conn.execute(query, params)
            return [
                {
                    "id": str(r[0]),
                    "worker_name": r[1],
                    "supervisor_name": r[2],
                    "result_data": r[3],
                    "metrics": r[4],
                }
                async for r in rows
            ]


class JobRepository:
    """jobs 테이블 CRUD."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def create(self, input_data: dict[str, Any], user_id: str | None = None) -> str:
        """새 Job을 생성하고 UUID를 반환한다."""
        job_id = str(uuid.uuid4())
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute(
                """
                INSERT INTO jobs (id, user_id, input_data, status)
                VALUES (%s, %s::uuid, %s::jsonb, 'pending')
                """,
                (job_id, user_id, json.dumps(input_data, default=str)),
            )
        return job_id

    async def get(self, job_id: str) -> dict[str, Any] | None:
        """Job ID로 조회한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            row = await conn.execute(
                "SELECT id, status, progress, input_data, result_data, error_message FROM jobs WHERE id = %s::uuid",
                (job_id,),
            )
            result = await row.fetchone()
            if result is None:
                return None
            return {
                "id": str(result[0]),
                "status": result[1],
                "progress": result[2],
                "input_data": result[3],
                "result_data": result[4],
                "error_message": result[5],
            }

    async def update_status(
        self, job_id: str, status: str, progress: float | None = None
    ) -> None:
        """Job 상태를 업데이트한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            if progress is not None:
                await conn.execute(
                    "UPDATE jobs SET status = %s, progress = %s, updated_at = NOW() WHERE id = %s::uuid",
                    (status, progress, job_id),
                )
            else:
                await conn.execute(
                    "UPDATE jobs SET status = %s, updated_at = NOW() WHERE id = %s::uuid",
                    (status, job_id),
                )

    async def save_result_data(self, job_id: str, result_data: dict[str, Any]) -> None:
        """Job 최종 결과를 저장한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute(
                "UPDATE jobs SET result_data = %s::jsonb, status = 'completed', progress = 1.0, updated_at = NOW() WHERE id = %s::uuid",
                (json.dumps(result_data, default=str), job_id),
            )

    async def save_error(self, job_id: str, error_message: str) -> None:
        """Job 오류를 저장한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute(
                "UPDATE jobs SET error_message = %s, status = 'failed', updated_at = NOW() WHERE id = %s::uuid",
                (error_message, job_id),
            )


class IdentityRepository:
    """identity_resolutions 테이블 CRUD."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def save(
        self,
        job_id: str,
        github_node_id: str,
        canonical_name: str,
        canonical_email: str,
        mailmap_entries: list[dict[str, Any]],
        total_commits: int,
        verified_commits: int,
        pure_logic_lines: int = 0,
    ) -> str:
        """Identity Resolution 결과를 저장하고 UUID를 반환한다."""
        result_id = str(uuid.uuid4())
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute(
                """
                INSERT INTO identity_resolutions
                    (id, job_id, github_node_id, canonical_name, canonical_email,
                     mailmap_entries, total_commits, verified_commits, pure_logic_lines)
                VALUES (%s, %s::uuid, %s, %s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (job_id) DO UPDATE SET
                    github_node_id = EXCLUDED.github_node_id,
                    canonical_name = EXCLUDED.canonical_name,
                    canonical_email = EXCLUDED.canonical_email,
                    mailmap_entries = EXCLUDED.mailmap_entries,
                    total_commits = EXCLUDED.total_commits,
                    verified_commits = EXCLUDED.verified_commits,
                    pure_logic_lines = EXCLUDED.pure_logic_lines
                """,
                (
                    result_id,
                    job_id,
                    github_node_id,
                    canonical_name,
                    canonical_email,
                    json.dumps(mailmap_entries, default=str),
                    total_commits,
                    verified_commits,
                    pure_logic_lines,
                ),
            )
        return result_id

    async def get_by_job(self, job_id: str) -> dict[str, Any] | None:
        """Job ID로 Identity Resolution 결과를 조회한다."""
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            row = await conn.execute(
                """
                SELECT id, github_node_id, canonical_name, canonical_email,
                       mailmap_entries, total_commits, verified_commits, pure_logic_lines
                FROM identity_resolutions WHERE job_id = %s::uuid
                """,
                (job_id,),
            )
            result = await row.fetchone()
            if result is None:
                return None
            return {
                "id": str(result[0]),
                "github_node_id": result[1],
                "canonical_name": result[2],
                "canonical_email": result[3],
                "mailmap_entries": result[4],
                "total_commits": result[5],
                "verified_commits": result[6],
                "pure_logic_lines": result[7],
            }


class ScoreRepository:
    """candidate_scores 테이블 CRUD."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def save(
        self,
        job_id: str,
        logic_score: float,
        mastery_score: float,
        stability_score: float,
        authenticity_score: float,
        weighted_total: float,
        confidence: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        """4대 지표 점수를 저장하고 UUID를 반환한다."""
        result_id = str(uuid.uuid4())
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute(
                """
                INSERT INTO candidate_scores
                    (id, job_id, logic_score, mastery_score, stability_score,
                     authenticity_score, weighted_total, confidence, details)
                VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (job_id) DO UPDATE SET
                    logic_score = EXCLUDED.logic_score,
                    mastery_score = EXCLUDED.mastery_score,
                    stability_score = EXCLUDED.stability_score,
                    authenticity_score = EXCLUDED.authenticity_score,
                    weighted_total = EXCLUDED.weighted_total,
                    confidence = EXCLUDED.confidence,
                    details = EXCLUDED.details
                """,
                (
                    result_id,
                    job_id,
                    logic_score,
                    mastery_score,
                    stability_score,
                    authenticity_score,
                    weighted_total,
                    confidence,
                    json.dumps(details, default=str) if details else None,
                ),
            )
        return result_id
