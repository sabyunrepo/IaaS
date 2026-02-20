"""
Radon/Lizard Adapter 테스트 — 코드 복잡도 메트릭 산출.

radon 또는 lizard 패키지가 없으면 전체 모듈을 건너뛴다.
"""
pytest = __import__("pytest")
pytest.importorskip("radon")
pytest.importorskip("lizard")

import pytest  # noqa: E402 (importorskip 이후 재임포트)

from domain.analysis.models import ComplexityMetrics
from infrastructure.analysis.complexity_adapter import LizardAdapter, RadonAdapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def radon_adapter() -> RadonAdapter:
    return RadonAdapter()


@pytest.fixture()
def lizard_adapter() -> LizardAdapter:
    return LizardAdapter()


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------

# 단순 함수 — CC = 1 (분기 없음)
_SIMPLE_PYTHON = """\
def add(a, b):
    return a + b
"""

# 복잡 함수 — if + for + elif 분기로 CC > 3
_COMPLEX_PYTHON = """\
def evaluate(x, items):
    if x > 100:
        result = "high"
    elif x > 50:
        result = "medium"
    else:
        result = "low"
    for item in items:
        if item > x:
            result = "adjusted"
    return result
"""

# 간단한 JavaScript 함수
_SIMPLE_JS = """\
function greet(name) {
    return "Hello " + name;
}
"""

# JavaScript 분기 포함
_COMPLEX_JS = """\
function classify(score) {
    if (score >= 90) {
        return "A";
    } else if (score >= 80) {
        return "B";
    } else if (score >= 70) {
        return "C";
    } else {
        return "F";
    }
}
"""


# ---------------------------------------------------------------------------
# RadonAdapter
# ---------------------------------------------------------------------------


class TestRadonAdapterSimpleCode:
    def test_returns_complexity_metrics_instance(self, radon_adapter: RadonAdapter) -> None:
        """analyze()는 ComplexityMetrics 인스턴스를 반환한다."""
        result = radon_adapter.analyze(_SIMPLE_PYTHON)
        assert isinstance(result, ComplexityMetrics)

    def test_simple_function_cc_positive(self, radon_adapter: RadonAdapter) -> None:
        """단순 함수는 CC > 0을 반환한다."""
        result = radon_adapter.analyze(_SIMPLE_PYTHON)
        assert result.cyclomatic_complexity > 0

    def test_simple_function_maintainability_in_range(
        self, radon_adapter: RadonAdapter
    ) -> None:
        """단순 함수의 MI는 0~100 범위다."""
        result = radon_adapter.analyze(_SIMPLE_PYTHON)
        assert 0.0 <= result.maintainability_index <= 100.0

    def test_halstead_volume_nonnegative(self, radon_adapter: RadonAdapter) -> None:
        """Halstead volume은 0 이상이다."""
        result = radon_adapter.analyze(_SIMPLE_PYTHON)
        assert result.halstead_volume >= 0.0

    def test_halstead_difficulty_nonnegative(self, radon_adapter: RadonAdapter) -> None:
        """Halstead difficulty는 0 이상이다."""
        result = radon_adapter.analyze(_SIMPLE_PYTHON)
        assert result.halstead_difficulty >= 0.0

    def test_cognitive_complexity_is_zero(self, radon_adapter: RadonAdapter) -> None:
        """Radon은 cognitive complexity를 지원하지 않으므로 0.0을 반환한다."""
        result = radon_adapter.analyze(_SIMPLE_PYTHON)
        assert result.cognitive_complexity == 0.0


class TestRadonAdapterEmptyCode:
    def test_empty_code_returns_defaults(self, radon_adapter: RadonAdapter) -> None:
        """빈 코드는 모든 메트릭이 0.0인 기본값을 반환한다."""
        result = radon_adapter.analyze("")
        assert result.cyclomatic_complexity == 0.0
        assert result.halstead_difficulty == 0.0
        assert result.halstead_volume == 0.0
        assert result.cognitive_complexity == 0.0

    def test_empty_code_mi_in_range(self, radon_adapter: RadonAdapter) -> None:
        """빈 코드의 MI도 0~100 범위다."""
        result = radon_adapter.analyze("")
        assert 0.0 <= result.maintainability_index <= 100.0

    def test_whitespace_only_code_does_not_raise(
        self, radon_adapter: RadonAdapter
    ) -> None:
        """공백만 있는 코드도 예외 없이 처리한다."""
        result = radon_adapter.analyze("   \n\t\n")
        assert isinstance(result, ComplexityMetrics)


class TestRadonAdapterComplexCode:
    def test_complex_function_higher_cc_than_simple(
        self, radon_adapter: RadonAdapter
    ) -> None:
        """분기가 많은 함수의 CC는 단순 함수보다 높다."""
        simple = radon_adapter.analyze(_SIMPLE_PYTHON)
        complex_ = radon_adapter.analyze(_COMPLEX_PYTHON)
        assert complex_.cyclomatic_complexity > simple.cyclomatic_complexity

    def test_complex_code_cc_above_two(self, radon_adapter: RadonAdapter) -> None:
        """if/elif/for 분기가 있는 함수의 CC는 2 초과다."""
        result = radon_adapter.analyze(_COMPLEX_PYTHON)
        assert result.cyclomatic_complexity > 2.0

    def test_complex_code_mi_not_exceeds_100(self, radon_adapter: RadonAdapter) -> None:
        """복잡한 코드의 MI도 100을 초과하지 않는다 (클램핑)."""
        result = radon_adapter.analyze(_COMPLEX_PYTHON)
        assert result.maintainability_index <= 100.0

    def test_complex_code_halstead_positive(self, radon_adapter: RadonAdapter) -> None:
        """복잡한 코드의 Halstead 메트릭은 양수다."""
        result = radon_adapter.analyze(_COMPLEX_PYTHON)
        assert result.halstead_difficulty > 0.0
        assert result.halstead_volume > 0.0


class TestRadonAdapterSyntaxError:
    def test_invalid_syntax_returns_zeros(self, radon_adapter: RadonAdapter) -> None:
        """유효하지 않은 Python 코드는 기본값(0.0)을 반환하며 예외가 발생하지 않는다."""
        invalid_code = "def broken(:\n    pass"
        result = radon_adapter.analyze(invalid_code)
        assert isinstance(result, ComplexityMetrics)
        assert result.cyclomatic_complexity == 0.0


# ---------------------------------------------------------------------------
# LizardAdapter
# ---------------------------------------------------------------------------


class TestLizardAdapterPythonCode:
    def test_returns_complexity_metrics_instance(
        self, lizard_adapter: LizardAdapter
    ) -> None:
        """analyze()는 ComplexityMetrics 인스턴스를 반환한다."""
        result = lizard_adapter.analyze(_SIMPLE_PYTHON)
        assert isinstance(result, ComplexityMetrics)

    def test_simple_python_cc_positive(self, lizard_adapter: LizardAdapter) -> None:
        """단순 Python 함수의 CC는 0 초과다."""
        result = lizard_adapter.analyze(_SIMPLE_PYTHON)
        assert result.cyclomatic_complexity > 0.0

    def test_complex_python_higher_cc(self, lizard_adapter: LizardAdapter) -> None:
        """분기가 있는 Python 코드의 CC는 단순 코드보다 높다."""
        simple = lizard_adapter.analyze(_SIMPLE_PYTHON)
        complex_ = lizard_adapter.analyze(_COMPLEX_PYTHON)
        assert complex_.cyclomatic_complexity > simple.cyclomatic_complexity

    def test_halstead_and_mi_are_zero(self, lizard_adapter: LizardAdapter) -> None:
        """Lizard는 Halstead와 MI를 지원하지 않으므로 0.0이다."""
        result = lizard_adapter.analyze(_SIMPLE_PYTHON)
        assert result.halstead_difficulty == 0.0
        assert result.halstead_volume == 0.0
        assert result.maintainability_index == 0.0
        assert result.cognitive_complexity == 0.0

    def test_empty_code_returns_zero_cc(self, lizard_adapter: LizardAdapter) -> None:
        """빈 코드는 CC = 0.0을 반환한다."""
        result = lizard_adapter.analyze("")
        assert result.cyclomatic_complexity == 0.0


class TestLizardAdapterJavaScriptCode:
    def test_simple_js_cc_positive(self, lizard_adapter: LizardAdapter) -> None:
        """단순 JavaScript 함수의 CC는 0 초과다."""
        result = lizard_adapter.analyze(_SIMPLE_JS, filename="temp.js")
        assert result.cyclomatic_complexity > 0.0

    def test_complex_js_higher_cc_than_simple(self, lizard_adapter: LizardAdapter) -> None:
        """분기가 많은 JavaScript 코드의 CC는 단순 코드보다 높다."""
        simple = lizard_adapter.analyze(_SIMPLE_JS, filename="temp.js")
        complex_ = lizard_adapter.analyze(_COMPLEX_JS, filename="temp.js")
        assert complex_.cyclomatic_complexity > simple.cyclomatic_complexity

    def test_language_hint_overrides_filename(self, lizard_adapter: LizardAdapter) -> None:
        """language 힌트를 제공하면 filename보다 우선한다."""
        # language="javascript" → 내부에서 "temp.js"로 변환
        result = lizard_adapter.analyze(_SIMPLE_JS, language="javascript")
        assert isinstance(result, ComplexityMetrics)
        assert result.cyclomatic_complexity > 0.0

    def test_js_returns_complexity_metrics(self, lizard_adapter: LizardAdapter) -> None:
        """JavaScript 코드 분석 결과는 ComplexityMetrics 인스턴스다."""
        result = lizard_adapter.analyze(_SIMPLE_JS, filename="temp.js")
        assert isinstance(result, ComplexityMetrics)


class TestLizardAdapterFilenameForLanguage:
    def test_python(self) -> None:
        assert LizardAdapter.filename_for_language("python") == "temp.py"

    def test_javascript(self) -> None:
        assert LizardAdapter.filename_for_language("javascript") == "temp.js"

    def test_typescript(self) -> None:
        assert LizardAdapter.filename_for_language("typescript") == "temp.ts"

    def test_java(self) -> None:
        assert LizardAdapter.filename_for_language("java") == "Temp.java"

    def test_go(self) -> None:
        assert LizardAdapter.filename_for_language("go") == "temp.go"

    def test_c(self) -> None:
        assert LizardAdapter.filename_for_language("c") == "temp.c"

    def test_cpp(self) -> None:
        assert LizardAdapter.filename_for_language("cpp") == "temp.cpp"

    def test_unknown_language_returns_txt(self) -> None:
        assert LizardAdapter.filename_for_language("ruby") == "temp.txt"

    def test_case_insensitive_python(self) -> None:
        """대소문자 무관하게 매핑된다."""
        assert LizardAdapter.filename_for_language("Python") == "temp.py"

    def test_case_insensitive_javascript(self) -> None:
        assert LizardAdapter.filename_for_language("JavaScript") == "temp.js"


# ---------------------------------------------------------------------------
# ComplexityMetrics 도메인 제약 준수 검증
# ---------------------------------------------------------------------------


class TestComplexityMetricsConstraints:
    def test_radon_result_satisfies_domain_constraints(
        self, radon_adapter: RadonAdapter
    ) -> None:
        """RadonAdapter 결과는 ComplexityMetrics 도메인 제약을 모두 만족한다."""
        result = radon_adapter.analyze(_COMPLEX_PYTHON)
        # ge=0 검증
        assert result.cyclomatic_complexity >= 0.0
        assert result.halstead_difficulty >= 0.0
        assert result.halstead_volume >= 0.0
        assert result.cognitive_complexity >= 0.0
        # ge=0, le=100 검증
        assert 0.0 <= result.maintainability_index <= 100.0

    def test_lizard_result_satisfies_domain_constraints(
        self, lizard_adapter: LizardAdapter
    ) -> None:
        """LizardAdapter 결과는 ComplexityMetrics 도메인 제약을 모두 만족한다."""
        result = lizard_adapter.analyze(_COMPLEX_PYTHON)
        assert result.cyclomatic_complexity >= 0.0
        assert result.halstead_difficulty >= 0.0
        assert result.halstead_volume >= 0.0
        assert result.cognitive_complexity >= 0.0
        assert 0.0 <= result.maintainability_index <= 100.0
