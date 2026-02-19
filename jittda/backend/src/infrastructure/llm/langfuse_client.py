"""
Langfuse 프롬프트 관리 클라이언트.

Langfuse-first 아키텍처: 런타임 프롬프트를 Langfuse에서 풀링한다.
YAML 프롬프트는 백업/초기값일 뿐, Langfuse가 런타임 우선.
"""
from langfuse import Langfuse


class LangfusePromptManager:
    """Langfuse 프롬프트 관리."""

    def __init__(
        self,
        *,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com",
    ):
        self._langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )

    def get_prompt(
        self,
        name: str,
        *,
        label: str = "production",
        fallback: list[dict[str, str]] | None = None,
    ) -> dict:
        """Langfuse에서 프롬프트를 가져온다.

        Args:
            name: 프롬프트 이름.
            label: 프롬프트 라벨 (production, staging 등).
            fallback: Langfuse 연결 실패 시 대체 프롬프트.

        Returns:
            {"messages": [...], "config": {...}} 형태.
        """
        try:
            prompt = self._langfuse.get_prompt(name, label=label)
            return {
                "messages": prompt.get_langchain_prompt() if hasattr(prompt, "get_langchain_prompt") else [],
                "config": prompt.config if hasattr(prompt, "config") else {},
                "raw": prompt,
            }
        except Exception:
            if fallback:
                return {"messages": fallback, "config": {}, "raw": None}
            raise

    def compile_prompt(
        self,
        name: str,
        *,
        label: str = "production",
        **variables: str,
    ) -> list[dict[str, str]]:
        """프롬프트를 가져와 변수를 치환한다.

        Args:
            name: 프롬프트 이름.
            label: 프롬프트 라벨.
            **variables: 치환할 변수.

        Returns:
            OpenAI 형식 메시지 리스트.
        """
        prompt = self._langfuse.get_prompt(name, label=label)
        return prompt.compile(**variables)
