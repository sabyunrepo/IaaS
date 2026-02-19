"""
벤치마크 테스트 Fixtures.

E2E conftest의 Mock 인프라를 재사용하고, 시간 측정 유틸리티를 제공한다.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator

import pytest

# E2E Mock 인프라 재사용 (langfuse 패치 포함)
from tests.e2e.conftest import (  # noqa: F401
    InMemoryStore,
    MockAnalysisRepository,
    MockEmbeddingService,
    MockIdentityRepository,
    MockInstructorClient,
    MockJobRepository,
    MockPgvectorStore,
    MockScoreRepository,
    make_forensic_result,
    make_full_input_data,
    make_github_only_input_data,
    make_logic_result,
    make_mock_graph,
    make_sample_questions,
    make_stack_result,
)


# ---------------------------------------------------------------------------
# Timing Utilities
# ---------------------------------------------------------------------------


@dataclass
class TimingResult:
    """단일 측정 결과."""

    name: str
    elapsed_ms: float
    iterations: int = 1

    @property
    def avg_ms(self) -> float:
        return self.elapsed_ms / self.iterations


@dataclass
class BenchmarkReport:
    """벤치마크 결과 수집기."""

    results: list[TimingResult] = field(default_factory=list)

    def add(self, name: str, elapsed_ms: float, iterations: int = 1) -> None:
        self.results.append(TimingResult(name=name, elapsed_ms=elapsed_ms, iterations=iterations))

    def print_report(self) -> None:
        """벤치마크 결과를 구조화된 형식으로 출력."""
        print("\n" + "=" * 60)
        print("  Performance Benchmark Results")
        print("=" * 60)

        # 카테고리별 그룹핑
        categories: dict[str, list[TimingResult]] = {}
        for r in self.results:
            # 이름에서 카테고리 추출 (첫 번째 ':' 이전)
            parts = r.name.split(":", 1)
            cat = parts[0].strip() if len(parts) > 1 else "General"
            name = parts[1].strip() if len(parts) > 1 else r.name
            r_copy = TimingResult(name=name, elapsed_ms=r.elapsed_ms, iterations=r.iterations)
            categories.setdefault(cat, []).append(r_copy)

        for cat, items in categories.items():
            print(f"\n  {cat}:")
            is_memory = cat.lower() == "memory"
            for r in items:
                if is_memory:
                    print(f"    {r.name}: {r.elapsed_ms:.0f} bytes")
                elif r.iterations > 1:
                    print(f"    {r.name} ({r.iterations}x): {r.avg_ms:.2f}ms avg, {r.elapsed_ms:.1f}ms total")
                else:
                    print(f"    {r.name}: {r.elapsed_ms:.2f}ms")

        print("\n" + "=" * 60)


@contextmanager
def measure_time() -> Generator[dict[str, float], None, None]:
    """시간 측정 컨텍스트 매니저. result['elapsed_ms']로 결과 접근."""
    result: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield result
    finally:
        end = time.perf_counter()
        result["elapsed_ms"] = (end - start) * 1000


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def report() -> BenchmarkReport:
    """벤치마크 결과 수집기."""
    return BenchmarkReport()


@pytest.fixture
def memory_store() -> InMemoryStore:
    """독립된 In-Memory 저장소."""
    return InMemoryStore()
