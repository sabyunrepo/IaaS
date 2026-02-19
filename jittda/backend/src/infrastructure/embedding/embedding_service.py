"""
EmbeddingService — 텍스트 임베딩 생성.

OpenAI text-embedding-3-small (1536차원) API를 호출한다.
"""
import httpx


class EmbeddingService:
    """텍스트를 벡터 임베딩으로 변환한다."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        dimensions: int = 1536,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        """텍스트를 임베딩 벡터로 변환한다."""
        if not text.strip():
            return [0.0] * self._dimensions

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                json={"input": text, "model": self._model, "dimensions": self._dimensions},
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """여러 텍스트를 배치로 임베딩."""
        if not texts:
            return []

        non_empty = [t if t.strip() else "." for t in texts]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                json={"input": non_empty, "model": self._model, "dimensions": self._dimensions},
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return [d["embedding"] for d in sorted(data["data"], key=lambda x: x["index"])]
