---
title: "Embedding Strategy"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [embedding, chunking, text-embedding-3-small, ast, batch]
parent: "[[vector-search/MOC]]"
linear: [JIT-99]
---

# Embedding Strategy

## 개요

> `text-embedding-3-small` (1536차원) 모델로 코드, JD, 이력서, LinkedIn 프로필을
> 소스별 최적 청크 단위로 분할하여 임베딩을 생성한다.
> 코드 청킹은 Tree-sitter AST 기반으로 함수/클래스 단위를 사용한다.

## 상세 설계

### 임베딩 모델

| 항목 | 값 |
|------|---|
| 모델 | `text-embedding-3-small` (OpenAI) |
| 차원 | 1536 |
| 최대 입력 토큰 | 8191 tokens |
| 가격 | $0.02 / 1M tokens |
| 선택 이유 | cost-효율 최적, pgvector 1536차원과 정확히 호환 |

### 청크 전략

| 소스 | 청크 단위 | 최대 크기 | 메타데이터 |
|------|----------|---------|----------|
| 코드 | 함수/클래스 (AST 기반) | 500 tokens | file_path, language, complexity, author, commit_hash |
| JD | 섹션별 (자격요건/우대사항/담당업무) | 300 tokens | section_type, keywords |
| 이력서 | 경력/프로젝트별 | 400 tokens | company, role, duration |
| LinkedIn | 프로필 섹션별 | 300 tokens | section_type (about/experience/skills) |

### 코드 예시

#### 임베딩 클라이언트

```python
# infrastructure/embedding/embedder.py
from openai import AsyncOpenAI
from functools import lru_cache
from core.config import settings

@lru_cache(maxsize=1)
def get_embedder() -> "Embedder":
    return Embedder(
        client=AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
        )
    )

class Embedder:
    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    BATCH_SIZE = 100  # OpenAI API 배치 제한

    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def embed(self, text: str) -> list[float]:
        """단일 텍스트 임베딩"""
        response = await self.client.embeddings.create(
            model=self.MODEL,
            input=text,
            dimensions=self.DIMENSIONS,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """배치 임베딩 (최대 100개씩 분할)"""
        results = []
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i : i + self.BATCH_SIZE]
            response = await self.client.embeddings.create(
                model=self.MODEL,
                input=batch,
                dimensions=self.DIMENSIONS,
            )
            results.extend([d.embedding for d in response.data])
        return results
```

#### AST 기반 코드 청커

```python
# infrastructure/embedding/chunker.py
from dataclasses import dataclass
from infrastructure.analysis.tree_sitter_adapter import TreeSitterAdapter

@dataclass
class CodeChunk:
    file_path: str
    language: str
    chunk_type: str   # 'function' | 'class' | 'module'
    chunk_name: str
    content: str
    complexity: float | None = None
    author: str | None = None
    commit_hash: str | None = None

class CodeChunker:
    """Tree-sitter AST 기반 함수/클래스 단위 코드 청킹"""

    MAX_CHUNK_TOKENS = 500  # text-embedding-3-small 최적 크기

    def __init__(self, ast_adapter: TreeSitterAdapter):
        self.ast_adapter = ast_adapter

    def chunk_file(
        self,
        file_path: str,
        code: str,
        language: str,
    ) -> list[CodeChunk]:
        """파일을 함수/클래스 단위로 청킹"""
        tree = self.ast_adapter.parse_code(code, language)
        functions = self.ast_adapter.extract_functions(tree.root_node, language)
        classes = self.ast_adapter.extract_classes(tree.root_node, language)

        chunks = []
        for func in functions:
            chunk_code = code[func["node"].start_byte:func["node"].end_byte]
            if self._estimate_tokens(chunk_code) <= self.MAX_CHUNK_TOKENS:
                chunks.append(CodeChunk(
                    file_path=file_path,
                    language=language,
                    chunk_type="function",
                    chunk_name=func["name"],
                    content=chunk_code,
                ))
            else:
                # 큰 함수는 논리 블록으로 추가 분할
                chunks.extend(self._split_large_chunk(
                    file_path, language, func["name"], chunk_code
                ))

        for cls in classes:
            chunk_code = code[cls["node"].start_byte:cls["node"].end_byte]
            chunks.append(CodeChunk(
                file_path=file_path,
                language=language,
                chunk_type="class",
                chunk_name=cls["name"],
                content=chunk_code[:self._token_limit_bytes(chunk_code)],
            ))

        return chunks

    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 추정 (4 chars ≈ 1 token)"""
        return len(text) // 4

    def _token_limit_bytes(self, text: str) -> int:
        return self.MAX_CHUNK_TOKENS * 4  # 대략적 바이트 한계
```

#### JD 섹션 청커

```python
# infrastructure/embedding/chunker.py (JD 섹션 분할)
class JDChunker:
    SECTION_PATTERNS = [
        ("requirements", r"(?:자격요건|Required|Requirements)"),
        ("preferred", r"(?:우대사항|Preferred|Nice to have)"),
        ("responsibilities", r"(?:담당업무|Responsibilities|What you'll do)"),
        ("about", r"(?:회사 소개|About us|About the role)"),
    ]

    def chunk_jd(self, jd_text: str) -> list[dict]:
        """JD 텍스트를 섹션별로 분할"""
        import re
        chunks = []
        current_section = "general"
        current_lines: list[str] = []

        for line in jd_text.splitlines():
            detected = self._detect_section(line)
            if detected:
                if current_lines:
                    chunks.append({
                        "section_type": current_section,
                        "content": "\n".join(current_lines),
                        "keywords": self._extract_keywords(current_lines),
                    })
                current_section = detected
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            chunks.append({
                "section_type": current_section,
                "content": "\n".join(current_lines),
                "keywords": self._extract_keywords(current_lines),
            })

        return chunks
```

#### 임베딩 파이프라인 통합

```python
# infrastructure/embedding/embedding_pipeline.py
class EmbeddingPipeline:
    """분석 완료 후 일괄 임베딩 저장 파이프라인"""

    def __init__(
        self,
        embedder: Embedder,
        store: PgVectorStore,
        code_chunker: CodeChunker,
        jd_chunker: JDChunker,
    ):
        self.embedder = embedder
        self.store = store
        self.code_chunker = code_chunker
        self.jd_chunker = jd_chunker

    async def embed_code_files(
        self,
        job_id: UUID,
        repo_files: list[dict],  # [{path, language, content, blame_info}]
    ) -> list[UUID]:
        """코드 파일 배치 임베딩 저장"""
        chunks: list[CodeChunk] = []
        for file_info in repo_files:
            file_chunks = self.code_chunker.chunk_file(
                file_path=file_info["path"],
                code=file_info["content"],
                language=file_info["language"],
            )
            # blame 정보 병합
            for chunk in file_chunks:
                chunk.author = file_info.get("primary_author")
                chunk.commit_hash = file_info.get("last_commit_hash")
            chunks.extend(file_chunks)

        # 배치 임베딩 생성
        texts = [c.content for c in chunks]
        embeddings = await self.embedder.embed_batch(texts)

        # 일괄 저장
        saved_ids = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            chunk_id = await self.store.save_code_chunk(job_id, chunk, embedding)
            saved_ids.append(chunk_id)

        return saved_ids

    async def embed_jd(self, job_id: UUID, jd_text: str) -> list[UUID]:
        """JD 섹션별 임베딩 저장"""
        sections = self.jd_chunker.chunk_jd(jd_text)
        texts = [s["content"] for s in sections]
        embeddings = await self.embedder.embed_batch(texts)

        saved_ids = []
        for section, embedding in zip(sections, embeddings, strict=True):
            emb_id = await self.store.save_embedding(
                job_id=job_id,
                kind="jd",
                content=section["content"],
                embedding=embedding,
                metadata={"section_type": section["section_type"],
                          "keywords": section["keywords"]},
            )
            saved_ids.append(emb_id)
        return saved_ids
```

### 컨텍스트 예산 관리

LLM에 전달되는 코드 청크는 토큰 예산 내에서 관리한다:

```python
# application/use_cases/context_budget.py
class ContextBudget:
    MAX_TOKENS = 8000

    ALLOCATION = {
        "system_prompt": 1500,
        "jd_context": 1500,
        "code_chunks": 3000,      # 벡터 검색된 코드 청크
        "candidate_profile": 1000,
        "topic_context": 1000,
    }

    def allocate(self, section: str, content: str) -> str:
        max_chars = self.ALLOCATION[section] * 4  # 토큰 → 문자 근사
        return content[:max_chars]
```

## 관련 문서

- 상위: [[vector-search/MOC]]
- 연관: [[vector-search/pgvector-setup]]
- 연관: [[infrastructure/tree-sitter-ast/MOC]]
