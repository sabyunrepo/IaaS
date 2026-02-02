"""
backend/app/services/vector_store.py
pgvector 기반 벡터 스토어 (프로필/코드 저장 및 검색)
"""
import logging
import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.database import EmbeddingDB

logger = logging.getLogger(__name__)

# Embedding dimension from config (OpenAI text-embedding-3-small = 1536)
EMBEDDING_DIM = 1536


async def _get_embedding(content: str) -> list[float]:
    """Generate embedding vector using LiteLLM."""
    from litellm import aembedding
    from app.core.config import settings

    try:
        response = await aembedding(
            model="text-embedding-3-small",
            input=[content[:8000]],  # truncate to model limit
            api_key=settings.OPENAI_API_KEY,
        )
        return response.data[0]["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


class VectorStore:
    """Job 별 벡터 스토어 (pgvector)"""

    def __init__(self, job_id: str):
        self.job_id = job_id

    async def store_profile(self, profile: dict) -> None:
        """후보자 프로필 벡터 저장 — 각 스킬/경험을 개별 임베딩으로 저장"""
        logger.info(f"[{self.job_id}] Storing profile vectors")

        entries = []
        # Skills
        for skill in profile.get("skills", []):
            name = skill if isinstance(skill, str) else skill.get("name", str(skill))
            desc = skill if isinstance(skill, str) else skill.get("description", name)
            entries.append(("skill:" + name, str(desc)))

        # Experience summary
        if summary := profile.get("summary", profile.get("experience_summary")):
            entries.append(("summary", str(summary)))

        # Education
        for edu in profile.get("education", []):
            entries.append(("education", str(edu)))

        if not entries:
            # Store entire profile as single embedding
            entries.append(("profile", str(profile)[:4000]))

        async with async_session() as session:
            for content_key, content_text in entries:
                embedding = await _get_embedding(content_text)
                row = EmbeddingDB(
                    id=uuid.uuid4(),
                    job_id=uuid.UUID(self.job_id),
                    kind="profile",
                    content_key=content_key,
                    content_text=content_text[:4000],
                    extra_data={"source": "profile"},
                    embedding=embedding,
                )
                session.add(row)
            await session.commit()

        logger.info(f"[{self.job_id}] Stored {len(entries)} profile vectors")

    async def store_code(self, implementation: dict) -> None:
        """코드 구현 벡터 저장 — 각 파일/함수를 개별 임베딩으로 저장"""
        logger.info(f"[{self.job_id}] Storing code vectors")

        entries = []
        # Repositories
        for repo in implementation.get("repositories", []):
            repo_name = repo.get("name", "unknown")
            for file_info in repo.get("key_files", repo.get("files", [])):
                path = file_info if isinstance(file_info, str) else file_info.get("path", str(file_info))
                desc = file_info if isinstance(file_info, str) else file_info.get("description", path)
                entries.append((f"code:{repo_name}/{path}", str(desc)))

        # Contributions
        for contrib in implementation.get("contributions", []):
            entries.append(("contribution", str(contrib)[:4000]))

        if not entries:
            entries.append(("code", str(implementation)[:4000]))

        async with async_session() as session:
            for content_key, content_text in entries:
                embedding = await _get_embedding(content_text)
                row = EmbeddingDB(
                    id=uuid.uuid4(),
                    job_id=uuid.UUID(self.job_id),
                    kind="code",
                    content_key=content_key,
                    content_text=content_text[:4000],
                    extra_data={"source": "code_analysis"},
                    embedding=embedding,
                )
                session.add(row)
            await session.commit()

        logger.info(f"[{self.job_id}] Stored {len(entries)} code vectors")

    async def search_code(self, query: str, limit: int = 5) -> list[dict]:
        """코드 벡터 유사도 검색"""
        return await self._search(query, "code", limit)

    async def search_profile(self, query: str, limit: int = 5) -> list[dict]:
        """프로필 벡터 유사도 검색"""
        return await self._search(query, "profile", limit)

    async def _search(self, query: str, kind: str, limit: int) -> list[dict]:
        """pgvector cosine similarity search."""
        logger.info(f"[{self.job_id}] Searching {kind} vectors: {query[:50]}")
        query_embedding = await _get_embedding(query)

        async with async_session() as session:
            # Use pgvector cosine distance operator <=>
            stmt = text("""
                SELECT id, content_key, content_text, metadata,
                       1 - (embedding <=> :query_vec) AS similarity
                FROM embeddings
                WHERE job_id = :job_id AND kind = :kind
                ORDER BY embedding <=> :query_vec
                LIMIT :limit
            """)
            result = await session.execute(stmt, {
                "query_vec": str(query_embedding),
                "job_id": self.job_id,
                "kind": kind,
                "limit": limit,
            })
            rows = result.fetchall()

        return [
            {
                "id": str(row.id),
                "content_key": row.content_key,
                "content_text": row.content_text,
                "metadata": row.metadata,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]


def get_vector_store(job_id: str) -> VectorStore:
    return VectorStore(job_id)
