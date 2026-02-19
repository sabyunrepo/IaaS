"""
E2E 통합 테스트 Fixtures — MetaGraph 파이프라인.

외부 의존성(DB, LLM, Redis, 서브그래프) 없이 전체 파이프라인을 테스트하기 위한
In-Memory Mock 인프라와 샘플 데이터 Fixture를 정의한다.
"""
from __future__ import annotations

import sys
import uuid
from types import ModuleType
from typing import Any, Type
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# langfuse import 문제 우회 (Python 3.14 + pydantic v1 호환 문제)
# ---------------------------------------------------------------------------
_langfuse_modules = [
    "langfuse",
    "langfuse.api",
    "langfuse.api.core",
    "langfuse.api.core.pydantic_utilities",
    "langfuse.api.resources",
    "langfuse.api.resources.annotation_queues",
    "langfuse.api.resources.annotation_queues.types",
    "langfuse.api.resources.commons",
    "langfuse.api.resources.commons.types",
    "langfuse.batch_evaluation",
    "langfuse.decorators",
]
for _mod_name in _langfuse_modules:
    if _mod_name not in sys.modules:
        _m = ModuleType(_mod_name)
        if _mod_name == "langfuse":
            _m.Langfuse = MagicMock  # type: ignore[attr-defined]
        sys.modules[_mod_name] = _m


# ===========================================================================
# In-Memory Store — 모든 Repository를 대체하는 메모리 저장소
# ===========================================================================


class InMemoryStore:
    """DB 없이 데이터 흐름을 테스트하기 위한 In-Memory 저장소."""

    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self.analysis_results: dict[str, dict[str, Any]] = {}
        self.identity_results: dict[str, dict[str, Any]] = {}
        self.scores: dict[str, dict[str, Any]] = {}


# ===========================================================================
# Mock Repository 클래스들 — InMemoryStore 기반
# ===========================================================================


class MockJobRepository:
    """JobRepository Mock — InMemoryStore 기반."""

    def __init__(self, conninfo: str = "", *, store: InMemoryStore | None = None) -> None:
        self._store = store or InMemoryStore()

    async def create(self, input_data: dict[str, Any], user_id: str | None = None) -> str:
        job_id = str(uuid.uuid4())
        self._store.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_data,
            "result_data": None,
            "error_message": None,
        }
        return job_id

    async def get(self, job_id: str) -> dict[str, Any] | None:
        return self._store.jobs.get(job_id)

    async def update_status(
        self, job_id: str, status: str, progress: float | None = None
    ) -> None:
        if job_id in self._store.jobs:
            self._store.jobs[job_id]["status"] = status
            if progress is not None:
                self._store.jobs[job_id]["progress"] = progress

    async def save_result_data(self, job_id: str, result_data: dict[str, Any]) -> None:
        if job_id in self._store.jobs:
            self._store.jobs[job_id]["result_data"] = result_data
            self._store.jobs[job_id]["status"] = "completed"
            self._store.jobs[job_id]["progress"] = 1.0

    async def save_error(self, job_id: str, error_message: str) -> None:
        if job_id in self._store.jobs:
            self._store.jobs[job_id]["error_message"] = error_message
            self._store.jobs[job_id]["status"] = "failed"


class MockAnalysisRepository:
    """AnalysisRepository Mock — InMemoryStore 기반."""

    def __init__(self, conninfo: str = "", *, store: InMemoryStore | None = None) -> None:
        self._store = store or InMemoryStore()

    async def save_result(
        self,
        job_id: str,
        worker_name: str,
        supervisor_name: str,
        result_data: dict[str, Any],
        metrics: dict[str, Any] | None = None,
    ) -> str:
        result_id = str(uuid.uuid4())
        self._store.analysis_results[result_id] = {
            "id": result_id,
            "job_id": job_id,
            "worker_name": worker_name,
            "supervisor_name": supervisor_name,
            "result_data": result_data,
            "metrics": metrics,
        }
        return result_id

    async def get_result(self, result_id: str) -> dict[str, Any] | None:
        return self._store.analysis_results.get(result_id)

    async def get_results_by_job(
        self, job_id: str, supervisor_name: str | None = None
    ) -> list[dict[str, Any]]:
        results = []
        for r in self._store.analysis_results.values():
            if r["job_id"] == job_id:
                if supervisor_name is None or r["supervisor_name"] == supervisor_name:
                    results.append(r)
        return results


class MockIdentityRepository:
    """IdentityRepository Mock — InMemoryStore 기반."""

    def __init__(self, conninfo: str = "", *, store: InMemoryStore | None = None) -> None:
        self._store = store or InMemoryStore()

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
        result_id = str(uuid.uuid4())
        self._store.identity_results[result_id] = {
            "id": result_id,
            "job_id": job_id,
            "github_node_id": github_node_id,
            "canonical_name": canonical_name,
            "canonical_email": canonical_email,
            "mailmap_entries": mailmap_entries,
            "total_commits": total_commits,
            "verified_commits": verified_commits,
            "pure_logic_lines": pure_logic_lines,
        }
        return result_id

    async def get_by_job(self, job_id: str) -> dict[str, Any] | None:
        for r in self._store.identity_results.values():
            if r["job_id"] == job_id:
                return r
        return None


class MockScoreRepository:
    """ScoreRepository Mock — InMemoryStore 기반."""

    def __init__(self, conninfo: str = "", *, store: InMemoryStore | None = None) -> None:
        self._store = store or InMemoryStore()

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
        result_id = str(uuid.uuid4())
        self._store.scores[result_id] = {
            "id": result_id,
            "job_id": job_id,
            "logic_score": logic_score,
            "mastery_score": mastery_score,
            "stability_score": stability_score,
            "authenticity_score": authenticity_score,
            "weighted_total": weighted_total,
            "confidence": confidence,
            "details": details,
        }
        return result_id


# ===========================================================================
# Mock LLM Client — InstructorClient 대체
# ===========================================================================


class MockInstructorClient:
    """InstructorClient Mock — response_model별 고정 응답 반환."""

    def __init__(
        self,
        *,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        max_retries: int = 3,
        responses: dict[str, Any] | None = None,
    ) -> None:
        self._responses = responses or {}
        self._call_count = 0

    async def create(
        self,
        *,
        response_model: Type[BaseModel],
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_retries: int | None = None,
    ) -> BaseModel:
        self._call_count += 1
        model_name = response_model.__name__
        if model_name in self._responses:
            response = self._responses[model_name]
            if callable(response):
                return response(self._call_count)
            return response
        raise ValueError(f"No mock response configured for {model_name}")


# ===========================================================================
# Mock Sub-Graph — build_*_graph 대체
# ===========================================================================


def make_mock_graph(result: dict[str, Any]) -> MagicMock:
    """서브그래프 빌드 결과를 모킹한다. graph.compile().ainvoke(input) → result."""
    mock_compiled = MagicMock()
    mock_compiled.ainvoke = AsyncMock(return_value=result)
    mock_builder = MagicMock()
    mock_builder.compile.return_value = mock_compiled
    return mock_builder


# ===========================================================================
# Mock Embedding / Vector — question_orchestrator 전용
# ===========================================================================


class MockEmbeddingService:
    """EmbeddingService Mock — 고정 임베딩 반환."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    @property
    def dimensions(self) -> int:
        return 1536

    async def embed(self, text: str) -> list[float]:
        return [0.1] * 1536


class MockPgvectorStore:
    """PgvectorStore Mock — 빈 검색 결과 반환."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    async def search_similar(self, **kwargs: Any) -> list[Any]:
        return []


# ===========================================================================
# Sample Data Fixtures
# ===========================================================================


def make_full_input_data() -> dict[str, Any]:
    """Happy Path용 전체 입력 데이터."""
    return {
        "github_urls": [
            "https://github.com/candidate/repo-1",
            "https://github.com/candidate/repo-2",
            "https://github.com/candidate/repo-3",
        ],
        "candidate_username": "candidate",
        "linkedin_url": "https://linkedin.com/in/candidate",
        "resume_text": "5 years of backend development experience with Python and Go...",
        "jd_text": "Senior Backend Engineer position requiring Python, FastAPI, PostgreSQL...",
        "jd_languages": ["Python", "Go"],
        "jd_tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
    }


def make_github_only_input_data() -> dict[str, Any]:
    """Partial Data용 GitHub만 있는 입력 데이터."""
    return {
        "github_urls": ["https://github.com/candidate/solo-repo"],
        "candidate_username": "candidate",
        "jd_text": "Junior Developer position...",
        "jd_languages": ["Python"],
        "jd_tech_stack": ["Python", "Django"],
    }


def make_forensic_result(
    *,
    authenticity_score: float = 0.85,
    total_files: int = 42,
    ai_suspicion: float = 0.08,
    style_consistency: float = 0.92,
) -> dict[str, Any]:
    """ForensicSupervisor 서브그래프 실행 결과."""
    return {
        "forensic_summary": {
            "ai_detection": {"avg_suspicion": ai_suspicion, "flagged_files": 1},
            "style_consistency": style_consistency,
            "total_files": total_files,
        },
        "authenticity_score": authenticity_score,
        "pure_contributions": [{"file": f"file_{i}.py", "pure_logic_lines": 50} for i in range(total_files)],
        "identity_cluster": {
            "github_node_id": "MDQ6VXNlcjEyMzQ1",
            "canonical_name": "Candidate Name",
            "canonical_email": "candidate@example.com",
            "aliases": [{"name": "candidate", "email": "c@example.com"}],
            "total_commits": 350,
            "verified_commits": 320,
        },
        "repo_local_paths": ["/tmp/repos/repo-1", "/tmp/repos/repo-2", "/tmp/repos/repo-3"],
        "plagiarism_report": {"plagiarism_detected": False, "similarity_max": 0.12},
    }


def make_logic_result(
    *,
    logic_score: float = 72.0,
    avg_complexity: float = 4.2,
    avg_maintainability: float = 68.5,
    files_analyzed: int = 38,
) -> dict[str, Any]:
    """LogicSupervisor 서브그래프 실행 결과."""
    return {
        "logic_summary": {
            "avg_cyclomatic_complexity": avg_complexity,
            "avg_maintainability_index": avg_maintainability,
            "total_functions": 120,
            "high_complexity_functions": 8,
        },
        "logic_score": logic_score,
        "ast_analysis": [
            {
                "file": f"file_{i}.py",
                "functions": 3,
                "avg_complexity": avg_complexity + (i * 0.1),
            }
            for i in range(files_analyzed)
        ],
    }


def make_stack_result(
    *,
    mastery_score: float = 78.0,
    total_skills: int = 15,
    avg_api_depth: float = 3.2,
    architecture_score: float = 72.0,
) -> dict[str, Any]:
    """StackSupervisor 서브그래프 실행 결과."""
    return {
        "stack_summary": {
            "total_skills_detected": total_skills,
            "avg_api_depth": avg_api_depth,
            "architecture_score": architecture_score,
            "top_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
        },
        "mastery_score": mastery_score,
    }


def make_sample_questions(count: int = 9) -> list[dict[str, Any]]:
    """샘플 면접 질문 리스트."""
    strategies = ["negative_selection", "intentional_complexity", "code_evolution"]
    categories = [
        "technical_depth",
        "execution_ownership",
        "communication",
        "role_fit",
        "risk_flags",
    ]
    difficulties = ["easy", "medium", "hard"]

    questions = []
    for i in range(count):
        strategy = strategies[i % 3]
        category = categories[i % 5]
        difficulty = difficulties[i % 3]
        questions.append({
            "question_id": f"{strategy}_{i+1}_{uuid.uuid4().hex[:8]}",
            "category": category,
            "strategy": strategy,
            "difficulty": difficulty,
            "question_text": f"In your repository repo-{i % 3 + 1}, you used Pattern-{i} but did not use Alternative-{i}. Can you explain this design decision?",
            "intent": f"Assess understanding of design trade-off #{i+1}",
            "code_reference": f"src/module_{i}.py:42",
            "expected_answer_guide": f"A good answer should mention the trade-off between Pattern-{i} and Alternative-{i}, including performance and maintainability considerations.",
            "red_flags": [
                f"Cannot explain why Pattern-{i} was chosen",
                "Gives only vague, generic answers",
            ],
            "follow_up_triggers": [
                f"If they mention performance, ask about benchmarks for Pattern-{i}",
            ],
            "terminology": [
                {"term": f"Pattern-{i}", "explanation": f"A design approach for solving problem #{i}"},
            ],
        })
    return questions


# ===========================================================================
# Pytest Fixtures
# ===========================================================================


@pytest.fixture
def memory_store() -> InMemoryStore:
    """독립된 In-Memory 저장소 인스턴스."""
    return InMemoryStore()


@pytest.fixture
def job_repo(memory_store: InMemoryStore) -> MockJobRepository:
    """MockJobRepository 인스턴스."""
    return MockJobRepository(store=memory_store)


@pytest.fixture
def analysis_repo(memory_store: InMemoryStore) -> MockAnalysisRepository:
    """MockAnalysisRepository 인스턴스."""
    return MockAnalysisRepository(store=memory_store)
