"""
backend/app/services/vector_store.py
pgvector 기반 벡터 스토어 (프로필/코드 저장 및 검색)
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class VectorStore:
    """Job 별 벡터 스토어 (pgvector)"""

    def __init__(self, job_id: str):
        self.job_id = job_id

    async def store_profile(self, profile: dict) -> None:
        """후보자 프로필 벡터 저장"""
        logger.info(f"[{self.job_id}] Storing profile vector")
        # TODO: pgvector embedding + insert
        pass

    async def store_code(self, implementation: dict) -> None:
        """코드 구현 벡터 저장"""
        logger.info(f"[{self.job_id}] Storing code vector")
        # TODO: pgvector embedding + insert
        pass

    async def search_code(self, query: str, limit: int = 5) -> list[dict]:
        """코드 벡터 유사도 검색"""
        logger.info(f"[{self.job_id}] Searching code vectors: {query}")
        # TODO: pgvector similarity search
        return []

    async def search_profile(self, query: str, limit: int = 5) -> list[dict]:
        """프로필 벡터 유사도 검색"""
        logger.info(f"[{self.job_id}] Searching profile vectors: {query}")
        # TODO: pgvector similarity search
        return []


def get_vector_store(job_id: str) -> VectorStore:
    return VectorStore(job_id)
