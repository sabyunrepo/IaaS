"""
Datasketch Adapter 테스트 — MinHash/LSH 기반 코드 유사도 탐지.

datasketch 패키지가 없으면 전체 모듈을 건너뛴다.
"""
pytest = __import__("pytest")
pytest.importorskip("datasketch")

import pytest  # noqa: E402 (importorskip 이후 재임포트)

from infrastructure.analysis.datasketch_adapter import DatasketchAdapter, SimilarityResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def adapter() -> DatasketchAdapter:
    """기본 설정 어댑터 (threshold=0.5, num_perm=128)."""
    return DatasketchAdapter(num_perm=128, threshold=0.5)


@pytest.fixture()
def strict_adapter() -> DatasketchAdapter:
    """낮은 임계값 어댑터 — 유사 코드 탐지가 더 쉽다."""
    return DatasketchAdapter(num_perm=128, threshold=0.3)


# ---------------------------------------------------------------------------
# create_minhash
# ---------------------------------------------------------------------------


class TestCreateMinhash:
    def test_same_code_produces_equal_jaccard(self, adapter: DatasketchAdapter) -> None:
        """동일한 코드는 Jaccard 유사도 1.0을 반환한다."""
        code = "def add(a, b): return a + b"
        mh1 = adapter.create_minhash(code)
        mh2 = adapter.create_minhash(code)
        assert mh1.jaccard(mh2) == pytest.approx(1.0)

    def test_empty_code_does_not_raise(self, adapter: DatasketchAdapter) -> None:
        """빈 코드도 예외 없이 MinHash를 반환한다."""
        mh = adapter.create_minhash("")
        assert mh is not None

    def test_single_token_does_not_raise(self, adapter: DatasketchAdapter) -> None:
        """토큰이 1개인 코드도 예외 없이 처리한다."""
        mh = adapter.create_minhash("return")
        assert mh is not None

    def test_two_tokens_does_not_raise(self, adapter: DatasketchAdapter) -> None:
        """토큰이 2개인 코드도 예외 없이 처리한다."""
        mh = adapter.create_minhash("return None")
        assert mh is not None

    def test_different_codes_have_different_hashes(self, adapter: DatasketchAdapter) -> None:
        """완전히 다른 코드는 낮은 Jaccard 유사도를 가진다."""
        mh_a = adapter.create_minhash("def foo(): pass")
        mh_b = adapter.create_minhash(
            "import os sys json re pathlib datetime collections itertools functools"
        )
        assert mh_a.jaccard(mh_b) < 0.5


# ---------------------------------------------------------------------------
# compute_pairwise_similarity
# ---------------------------------------------------------------------------


class TestComputePairwiseSimilarity:
    def test_identical_code_similarity_is_one(self, adapter: DatasketchAdapter) -> None:
        """동일한 코드는 유사도 ~1.0을 반환한다."""
        code = "for i in range(10): print(i)"
        sim = adapter.compute_pairwise_similarity(code, code)
        assert sim == pytest.approx(1.0)

    def test_completely_different_code_has_low_similarity(
        self, adapter: DatasketchAdapter
    ) -> None:
        """완전히 다른 코드는 낮은 유사도를 반환한다."""
        code_a = "def add(a, b): return a + b"
        code_b = (
            "import tensorflow as tf "
            "model = tf.keras.Sequential layers Dense Dropout Flatten "
            "optimizer adam loss sparse categorical crossentropy metrics accuracy"
        )
        sim = adapter.compute_pairwise_similarity(code_a, code_b)
        assert sim < 0.3

    def test_partially_similar_code_has_medium_similarity(
        self, adapter: DatasketchAdapter
    ) -> None:
        """일부 토큰을 공유하는 코드는 중간 유사도를 반환한다."""
        base = "def calculate(x, y): result = x + y return result"
        modified = "def calculate(x, y): result = x * y return result"
        sim = adapter.compute_pairwise_similarity(base, modified)
        # 두 코드는 대부분 동일하므로 높은 유사도 기대
        assert sim > 0.5

    def test_similarity_is_commutative(self, adapter: DatasketchAdapter) -> None:
        """유사도는 교환 가능하다 (a↔b = b↔a)."""
        code_a = "def foo(x): return x * 2"
        code_b = "def bar(y): return y + 1"
        sim_ab = adapter.compute_pairwise_similarity(code_a, code_b)
        sim_ba = adapter.compute_pairwise_similarity(code_b, code_a)
        assert sim_ab == pytest.approx(sim_ba)

    def test_empty_codes_do_not_raise(self, adapter: DatasketchAdapter) -> None:
        """빈 코드도 예외 없이 처리한다."""
        sim = adapter.compute_pairwise_similarity("", "")
        assert 0.0 <= sim <= 1.0


# ---------------------------------------------------------------------------
# index_code + query_similar
# ---------------------------------------------------------------------------


class TestIndexAndQuerySimilar:
    def test_indexed_identical_code_is_found(self, strict_adapter: DatasketchAdapter) -> None:
        """인덱스에 추가한 코드와 동일한 코드로 쿼리하면 해당 ID가 반환된다."""
        code = "def greet(name): return f'Hello {name} welcome to our service platform'"
        strict_adapter.index_code("chunk_0", code)

        results = strict_adapter.query_similar(code)

        assert len(results) > 0
        target_ids = {r.target_id for r in results}
        assert "chunk_0" in target_ids

    def test_results_are_sorted_by_similarity_descending(
        self, strict_adapter: DatasketchAdapter
    ) -> None:
        """결과는 유사도 내림차순으로 정렬된다."""
        base = "def process(data): result = transform(data) validate(result) return result"
        similar = "def process(data): result = transform(data) check(result) return result"
        different = (
            "import numpy pandas matplotlib seaborn sklearn tensorflow "
            "keras torch torchvision transformers datasets"
        )

        strict_adapter.index_code("similar", similar)
        strict_adapter.index_code("different", different)

        results = strict_adapter.query_similar(base)
        for i in range(len(results) - 1):
            assert results[i].similarity >= results[i + 1].similarity

    def test_query_returns_similarity_result_type(
        self, strict_adapter: DatasketchAdapter
    ) -> None:
        """반환값은 SimilarityResult 타입이다."""
        code = "def hello(): print('hello world from our application service')"
        strict_adapter.index_code("id_0", code)
        results = strict_adapter.query_similar(code)
        for r in results:
            assert isinstance(r, SimilarityResult)
            assert r.source_id == "query"
            assert 0.0 <= r.similarity <= 1.0

    def test_empty_index_returns_empty_list(self, adapter: DatasketchAdapter) -> None:
        """인덱스가 비어 있으면 빈 리스트를 반환한다."""
        results = adapter.query_similar("def foo(): pass")
        assert results == []

    def test_duplicate_index_does_not_raise(self, adapter: DatasketchAdapter) -> None:
        """동일한 code_id를 두 번 추가해도 예외가 발생하지 않는다."""
        code = "def foo(): return 42"
        adapter.index_code("dup", code)
        adapter.index_code("dup", code)  # ValueError 내부 처리

    def test_top_k_limits_results(self, strict_adapter: DatasketchAdapter) -> None:
        """top_k 파라미터로 반환 결과 수를 제한한다."""
        base = "def compute(x, y, z): return x + y + z"
        for i in range(20):
            strict_adapter.index_code(f"chunk_{i}", base)

        results = strict_adapter.query_similar(base, top_k=5)
        assert len(results) <= 5


# ---------------------------------------------------------------------------
# compute_plagiarism_ratio
# ---------------------------------------------------------------------------


class TestComputePlagiarismRatio:
    def test_empty_candidate_returns_zero(self, adapter: DatasketchAdapter) -> None:
        """candidate_chunks가 비어 있으면 0.0을 반환한다."""
        ratio = adapter.compute_plagiarism_ratio([], ["def foo(): pass"])
        assert ratio == 0.0

    def test_copied_code_has_high_ratio(self, adapter: DatasketchAdapter) -> None:
        """참조 코드와 동일한 청크가 많으면 높은 표절 비율을 반환한다."""
        reference = [
            "def add(a, b): return a + b",
            "def subtract(x, y): return x - y",
            "def multiply(p, q): return p * q",
        ]
        # 후보자가 참조 코드를 그대로 복사
        candidates = list(reference)
        ratio = adapter.compute_plagiarism_ratio(candidates, reference)
        assert ratio > 0.5

    def test_original_code_has_low_ratio(self, adapter: DatasketchAdapter) -> None:
        """참조 코드와 전혀 다른 청크는 낮은 표절 비율을 반환한다."""
        reference = [
            "def add(a, b): return a + b",
            "def subtract(x, y): return x - y",
        ]
        candidates = [
            "import asyncio aiohttp aiofiles uvicorn fastapi starlette pydantic sqlalchemy",
            "class EventLoop running tasks futures coroutines generators send throw close",
            "SELECT * FROM users WHERE id = 1 AND status = active ORDER BY created_at DESC",
        ]
        ratio = adapter.compute_plagiarism_ratio(candidates, reference)
        assert ratio < 0.5

    def test_ratio_is_between_zero_and_one(self, adapter: DatasketchAdapter) -> None:
        """반환값은 항상 0.0 ~ 1.0 범위다."""
        candidates = ["def foo(): pass", "def bar(): return 1"]
        reference = ["def foo(): pass"]
        ratio = adapter.compute_plagiarism_ratio(candidates, reference)
        assert 0.0 <= ratio <= 1.0

    def test_empty_reference_yields_zero_ratio(self, adapter: DatasketchAdapter) -> None:
        """참조 코드가 없으면 표절 비율은 0.0이다."""
        candidates = ["def foo(): pass", "def bar(): return 1"]
        ratio = adapter.compute_plagiarism_ratio(candidates, [])
        assert ratio == 0.0

    def test_does_not_mutate_instance_index(self, adapter: DatasketchAdapter) -> None:
        """compute_plagiarism_ratio는 인스턴스의 LSH 인덱스에 영향을 주지 않는다."""
        adapter.index_code("existing", "def foo(): pass")

        adapter.compute_plagiarism_ratio(
            ["def bar(): return 1"],
            ["def baz(): return 2"],
        )

        # 인스턴스 인덱스에는 'existing'만 남아 있어야 한다
        results = adapter.query_similar("def foo(): pass", top_k=20)
        target_ids = {r.target_id for r in results}
        assert not any(tid.startswith("ref_") for tid in target_ids)
