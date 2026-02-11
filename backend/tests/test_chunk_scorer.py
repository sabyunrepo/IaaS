"""
backend/tests/test_chunk_scorer.py
JD-Aware Chunk Relevance Scoring Engine 단위 테스트 [JIT-22]

테스트 항목:
- CS-01: JD 키워드 매칭 (FastAPI import → JD "FastAPI" 고점수)
- CS-02: 구조적 복잡도 (Lizard CC + fallback)
- CS-03: 면접 잠재력 (try/except, async, API decorator)
- CS-04: 후보자 기여 (명시적 비율 vs 기본값)
- CS-05: 가중 합산 총점 (0.4*jd + 0.25*cx + 0.20*ip + 0.15*ct)
- CS-06: rank_chunks 정렬 + 토큰 예산 제한
- CS-07: 엣지 케이스 (빈 입력, 빈 JD, 소스 없음)
- CS-08: select_top_files 하위 호환
"""
import sys
from unittest.mock import MagicMock

# pgvector가 설치되지 않은 환경에서도 테스트 가능하도록 mock
if "pgvector" not in sys.modules:
    sys.modules["pgvector"] = MagicMock()
    sys.modules["pgvector.sqlalchemy"] = MagicMock()

import pytest


# ============================================================
# Helper: 테스트용 청크 팩토리
# ============================================================

def _make_chunk(
    name: str = "test_func",
    chunk_type: str = "function",
    file_path: str = "main.py",
    source_code: str = "",
    identifiers: list[str] | None = None,
    imports: list[str] | None = None,
    decorators: list[str] | None = None,
    char_count: int | None = None,
) -> dict:
    """테스트용 청크 dict 생성"""
    src = source_code if source_code is not None else "def test_func():\n    pass"
    return {
        "name": name,
        "type": chunk_type,
        "file_path": file_path,
        "source_code": src,
        "identifiers": identifiers or [],
        "imports": imports or [],
        "decorators": decorators or [],
        "char_count": char_count if char_count is not None else len(src),
    }


# ============================================================
# CS-01: JD 키워드 매칭
# ============================================================

class TestJDKeywordMatching:
    """JD 키워드 매칭 점수 테스트"""

    def test_exact_import_match(self):
        """FastAPI import가 있으면 JD 'FastAPI'에 고점수"""
        from app.services.chunk_scorer import _calculate_jd_keyword_score

        chunk = _make_chunk(
            imports=["from fastapi import APIRouter"],
            identifiers=["APIRouter", "router"],
        )
        score, evidence = _calculate_jd_keyword_score(chunk, ["FastAPI"])
        assert score > 0.0
        assert any("FastAPI" in e or "fastapi" in e for e in evidence)

    def test_multiple_jd_skills(self):
        """여러 JD 스킬 중 일부 매칭 → 비례 점수"""
        from app.services.chunk_scorer import _calculate_jd_keyword_score

        chunk = _make_chunk(
            imports=["from fastapi import APIRouter", "import sqlalchemy"],
            identifiers=["APIRouter", "Session", "sqlalchemy"],
        )
        score, evidence = _calculate_jd_keyword_score(chunk, ["FastAPI", "PostgreSQL", "Redis"])
        # FastAPI, sqlalchemy 매칭 → 2/3 이상은 아닐 수 있지만 0보다 큼
        assert score > 0.0
        assert score <= 1.0

    def test_no_match(self):
        """JD 스킬과 전혀 무관한 청크 → 0점"""
        from app.services.chunk_scorer import _calculate_jd_keyword_score

        chunk = _make_chunk(
            imports=["import os"],
            identifiers=["path", "join"],
        )
        score, evidence = _calculate_jd_keyword_score(chunk, ["React", "TypeScript"])
        assert score == 0.0

    def test_empty_jd(self):
        """빈 JD → 0점"""
        from app.services.chunk_scorer import _calculate_jd_keyword_score

        chunk = _make_chunk(imports=["import fastapi"])
        score, evidence = _calculate_jd_keyword_score(chunk, [])
        assert score == 0.0

    def test_decorator_matching(self):
        """데코레이터에 JD 키워드가 포함되면 매칭"""
        from app.services.chunk_scorer import _calculate_jd_keyword_score

        chunk = _make_chunk(
            decorators=["app.get", "pytest.fixture"],
            identifiers=[],
        )
        score, evidence = _calculate_jd_keyword_score(chunk, ["pytest"])
        assert score > 0.0


# ============================================================
# CS-02: 구조적 복잡도
# ============================================================

class TestComplexityScore:
    """구조적 복잡도 점수 테스트"""

    def test_simple_function_low_complexity(self):
        """단순 함수 → 낮은 복잡도 점수"""
        from app.services.chunk_scorer import _calculate_complexity_score

        chunk = _make_chunk(source_code="def hello():\n    return 'world'")
        score, evidence = _calculate_complexity_score(chunk)
        assert 0.0 <= score <= 1.0

    def test_complex_function(self):
        """분기가 많은 함수 → 높은 복잡도 점수"""
        from app.services.chunk_scorer import _calculate_complexity_score

        complex_source = """def process(data):
    if data is None:
        return None
    result = []
    for item in data:
        if item > 0:
            if item % 2 == 0:
                result.append(item * 2)
            else:
                result.append(item * 3)
        elif item == 0:
            continue
        else:
            for sub in range(abs(item)):
                if sub % 3 == 0:
                    result.append(sub)
                elif sub % 5 == 0:
                    result.append(-sub)
    return result
"""
        chunk = _make_chunk(source_code=complex_source)
        score, evidence = _calculate_complexity_score(chunk)
        assert score > 0.0

    def test_empty_source_fallback(self):
        """소스 없음 → 0점"""
        from app.services.chunk_scorer import _calculate_complexity_score

        chunk = _make_chunk(source_code="")
        score, evidence = _calculate_complexity_score(chunk)
        assert score == 0.0

    def test_line_count_fallback(self):
        """Lizard 실패 시 라인수 기반 휴리스틱"""
        from app.services.chunk_scorer import _calculate_complexity_score

        # 일부러 파싱 불가 소스 (Lizard가 함수를 못 찾음)
        chunk = _make_chunk(source_code="x = 1\n" * 50)
        score, evidence = _calculate_complexity_score(chunk)
        assert 0.0 <= score <= 1.0
        assert any("라인수" in e or "source" in e for e in evidence)


# ============================================================
# CS-03: 면접 잠재력
# ============================================================

class TestInterviewPotential:
    """면접 잠재력 점수 테스트"""

    def test_try_except_pattern(self):
        """try/except 패턴 감지"""
        from app.services.chunk_scorer import _calculate_interview_potential

        source = """def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0
"""
        chunk = _make_chunk(source_code=source)
        score, evidence = _calculate_interview_potential(chunk)
        assert score > 0.0
        assert any("try" in e or "except" in e for e in evidence)

    def test_async_pattern(self):
        """async/await 패턴 감지"""
        from app.services.chunk_scorer import _calculate_interview_potential

        source = """async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url)
        return await resp.json()
"""
        chunk = _make_chunk(source_code=source)
        score, evidence = _calculate_interview_potential(chunk)
        assert score > 0.0
        assert any("async" in e or "await" in e for e in evidence)

    def test_api_decorator_pattern(self):
        """API 데코레이터 패턴 감지"""
        from app.services.chunk_scorer import _calculate_interview_potential

        source = """@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
"""
        chunk = _make_chunk(
            source_code=source,
            decorators=["app.get"],
        )
        score, evidence = _calculate_interview_potential(chunk)
        assert score > 0.0

    def test_plain_function_low_potential(self):
        """단순 함수 → 낮은 면접 잠재력"""
        from app.services.chunk_scorer import _calculate_interview_potential

        chunk = _make_chunk(source_code="def add(a, b):\n    return a + b")
        score, evidence = _calculate_interview_potential(chunk)
        # 단순 함수여도 0 이상일 수 있지만 낮아야 함
        assert score < 0.5

    def test_deep_nesting(self):
        """깊은 중첩 → 추가 점수"""
        from app.services.chunk_scorer import _calculate_interview_potential

        source = "def deep():\n" + "    " * 1 + "if True:\n"
        source += "    " * 2 + "for i in range(10):\n"
        source += "    " * 3 + "if i > 0:\n"
        source += "    " * 4 + "while i > 0:\n"
        source += "    " * 5 + "i -= 1\n"
        chunk = _make_chunk(source_code=source)
        score, evidence = _calculate_interview_potential(chunk)
        assert 0.0 <= score <= 1.0


# ============================================================
# CS-04: 후보자 기여
# ============================================================

class TestContributorScore:
    """후보자 기여 점수 테스트"""

    def test_explicit_ratio(self):
        """명시적 기여 비율 전달"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk()
        result = calculate_chunk_score(chunk, ["Python"], contributor_ratio=0.8)
        assert result.contributor_score == 0.8

    def test_default_ratio(self):
        """기여 비율 미지정 → 기본값 0.5"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk()
        result = calculate_chunk_score(chunk, ["Python"], contributor_ratio=None)
        assert result.contributor_score == 0.5

    def test_ratio_clamped(self):
        """기여 비율 0.0~1.0 클램핑"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk()
        result_high = calculate_chunk_score(chunk, ["Python"], contributor_ratio=1.5)
        assert result_high.contributor_score == 1.0

        result_low = calculate_chunk_score(chunk, ["Python"], contributor_ratio=-0.3)
        assert result_low.contributor_score == 0.0


# ============================================================
# CS-05: 가중 합산 총점
# ============================================================

class TestWeightedTotal:
    """가중 합산 총점 검증"""

    def test_weight_formula(self):
        """총점 = 0.4*jd + 0.25*cx + 0.20*ip + 0.15*ct"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk(
            imports=["from fastapi import FastAPI"],
            identifiers=["FastAPI"],
            source_code="async def handler():\n    try:\n        await do()\n    except Exception:\n        pass\n",
        )
        result = calculate_chunk_score(chunk, ["FastAPI"], contributor_ratio=1.0)

        expected = (
            result.jd_keyword_score * 0.40
            + result.complexity_score * 0.25
            + result.interview_potential * 0.20
            + result.contributor_score * 0.15
        )
        assert abs(result.total_score - round(expected, 4)) < 0.01

    def test_total_bounded(self):
        """총점은 항상 0.0~1.0"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk()
        result = calculate_chunk_score(chunk, ["Python", "FastAPI", "Redis"])
        assert 0.0 <= result.total_score <= 1.0

    def test_all_zeros(self):
        """모든 입력이 빈 경우에도 안전"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk(
            source_code="",
            identifiers=[],
            imports=[],
            decorators=[],
            char_count=0,
        )
        result = calculate_chunk_score(chunk, [], contributor_ratio=0.0)
        assert result.total_score == 0.0


# ============================================================
# CS-06: rank_chunks 정렬 + 토큰 예산 제한
# ============================================================

class TestRankChunks:
    """rank_chunks_by_relevance 테스트"""

    def test_sorted_by_score_desc(self):
        """결과가 점수 내림차순으로 정렬됨"""
        from app.services.chunk_scorer import rank_chunks_by_relevance

        chunks = [
            _make_chunk(name="low", source_code="x = 1", char_count=10, identifiers=["x"]),
            _make_chunk(
                name="high",
                source_code="async def handler():\n    try:\n        await do()\n    except Exception:\n        pass\n",
                char_count=100,
                imports=["from fastapi import FastAPI"],
                identifiers=["FastAPI"],
            ),
        ]
        result = rank_chunks_by_relevance(chunks, ["FastAPI"], token_budget=100_000)
        assert len(result) == 2
        scores = [r["relevance_score"]["total_score"] for r in result]
        assert scores[0] >= scores[1]

    def test_token_budget_limit(self):
        """토큰 예산 초과 시 자르기"""
        from app.services.chunk_scorer import rank_chunks_by_relevance

        # 각 1000자 청크 3개 = 3000자 ≈ 750 토큰
        chunks = [
            _make_chunk(name=f"func_{i}", source_code="x = 1\n" * 150, char_count=1000)
            for i in range(3)
        ]
        # 예산 500 토큰 = 2000자 → 2개만 선택
        result = rank_chunks_by_relevance(chunks, ["Python"], token_budget=500)
        assert len(result) <= 2

    def test_knapsack_small_after_big(self):
        """큰 청크 스킵 후 작은 고점수 청크 포함 (Knapsack)"""
        from app.services.chunk_scorer import rank_chunks_by_relevance

        chunks = [
            _make_chunk(
                name="big_low",
                source_code="x = 1\n" * 500,
                char_count=3000,  # 750 tokens
                identifiers=["x"],
            ),
            _make_chunk(
                name="small_high",
                source_code="async def handler():\n    await do()\n",
                char_count=100,  # 25 tokens
                imports=["from fastapi import FastAPI"],
                identifiers=["FastAPI"],
            ),
        ]
        # 예산 100 토큰 = 400자 → 큰 청크는 스킵, 작은 청크는 포함
        result = rank_chunks_by_relevance(chunks, ["FastAPI"], token_budget=100)
        names = [r["name"] for r in result]
        assert "small_high" in names
        assert "big_low" not in names

    def test_empty_chunks(self):
        """빈 입력 → 빈 결과"""
        from app.services.chunk_scorer import rank_chunks_by_relevance

        result = rank_chunks_by_relevance([], ["Python"])
        assert result == []


# ============================================================
# CS-07: 엣지 케이스
# ============================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_source(self):
        """source_code 없는 청크"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk(source_code="", char_count=0)
        result = calculate_chunk_score(chunk, ["Python"])
        assert result.total_score >= 0.0

    def test_empty_jd_tech_stack(self):
        """빈 JD 기술 스택"""
        from app.services.chunk_scorer import calculate_chunk_score

        chunk = _make_chunk(
            imports=["from fastapi import FastAPI"],
            source_code="async def handler():\n    pass\n",
        )
        result = calculate_chunk_score(chunk, [])
        assert result.jd_keyword_score == 0.0
        # 다른 점수는 여전히 계산됨
        assert result.total_score >= 0.0

    def test_chunk_relevance_score_model(self):
        """ChunkRelevanceScore 모델 필드 검증"""
        from app.models.analysis import ChunkRelevanceScore

        score = ChunkRelevanceScore(
            chunk_name="test",
            chunk_type="function",
            file_path="test.py",
            jd_keyword_score=0.5,
            complexity_score=0.3,
            interview_potential=0.4,
            contributor_score=0.5,
            total_score=0.42,
            char_count=100,
            evidence=["test evidence"],
        )
        assert score.chunk_name == "test"
        assert score.total_score == 0.42

    def test_very_large_source(self):
        """매우 큰 소스 코드 처리"""
        from app.services.chunk_scorer import calculate_chunk_score

        large_source = "x = 1\n" * 5000
        chunk = _make_chunk(source_code=large_source, char_count=len(large_source))
        result = calculate_chunk_score(chunk, ["Python"])
        assert 0.0 <= result.total_score <= 1.0

    def test_unicode_in_source(self):
        """한글/유니코드 소스 처리"""
        from app.services.chunk_scorer import calculate_chunk_score

        source = "def 인사(이름: str) -> str:\n    return f'안녕하세요, {이름}'\n"
        chunk = _make_chunk(
            name="인사",
            source_code=source,
            identifiers=["이름", "str"],
            char_count=len(source),
        )
        result = calculate_chunk_score(chunk, ["Python"])
        assert 0.0 <= result.total_score <= 1.0


# ============================================================
# CS-08: select_top_files 하위 호환
# ============================================================

class TestSelectTopFilesCompat:
    """기존 select_top_files가 변경 없이 동작하는지 검증"""

    def test_select_top_files_unchanged(self):
        """select_top_files는 기존과 동일하게 복잡도 기반 정렬"""
        from app.services.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer()
        files = [
            {"filename": "simple.py", "complexity": 2, "methods": 1},
            {"filename": "complex.py", "complexity": 15, "methods": 5},
            {"filename": "medium.py", "complexity": 8, "methods": 3},
        ]
        result = analyzer.select_top_files(files, ["Python"], max_files=3)
        assert len(result) == 3
        # 복잡도 순 정렬 확인
        assert result[0]["filename"] == "complex.py"

    def test_select_top_files_max_limit(self):
        """max_files 제한 동작"""
        from app.services.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer()
        files = [
            {"filename": f"file_{i}.py", "complexity": i, "methods": 1}
            for i in range(10)
        ]
        result = analyzer.select_top_files(files, ["Python"], max_files=3)
        assert len(result) == 3

    def test_select_top_chunks_exists(self):
        """select_top_chunks 메서드가 존재하고 호출 가능"""
        from app.services.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer()
        assert hasattr(analyzer, "select_top_chunks")
        # 빈 입력으로 호출
        result = analyzer.select_top_chunks([], ["Python"])
        assert result == []
