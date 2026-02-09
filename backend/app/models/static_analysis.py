"""
backend/app/models/static_analysis.py
정적 분석 결과 데이터 모델

Lizard (17개 언어 CC), Semgrep (보안), Radon (Python MI) 결과를 통합.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class SecurityFinding(BaseModel):
    """Semgrep/Bandit 보안 취약점"""
    rule_id: str                          # "python.security.sql-injection"
    severity: str                         # "ERROR" | "WARNING" | "INFO"
    message: str
    file_path: str
    line: int
    tool: str = "semgrep"                 # "semgrep" | "bandit"


class FunctionMetric(BaseModel):
    """Lizard per-function 메트릭"""
    function_name: str
    file_path: str
    language: str
    cyclomatic_complexity: int
    nloc: int                             # Non-comment Lines of Code
    token_count: int | None = None


class FileMetric(BaseModel):
    """파일 단위 메트릭"""
    file_path: str
    language: str
    total_nloc: int
    avg_cc: float
    max_cc: int
    function_count: int
    maintainability_index: float | None = None  # Radon MI (Python only)


class StaticAnalysisResult(BaseModel):
    """정적 분석 통합 결과"""
    # 언어 분포
    language_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description='{"Python": 3200, "TypeScript": 1500}',
    )

    # 복잡도 메트릭 (Lizard)
    file_metrics: list[FileMetric] = Field(default_factory=list)
    function_metrics: list[FunctionMetric] = Field(
        default_factory=list,
        description="상위 20개 복잡 함수만",
    )
    overall_avg_cc: float = 0.0
    overall_max_cc: int = 0
    total_nloc: int = 0

    # 보안 (Semgrep)
    security_findings: list[SecurityFinding] = Field(default_factory=list)
    security_score: int = Field(
        default=100,
        description="0-100 (발견 수/심각도 역비례)",
    )

    # Python 전용 (Radon)
    maintainability_index: float | None = None  # 0-100
    halstead_volume: float | None = None

    # 문서화 (docstring 비율)
    documentation_ratio: float = 0.0      # 0.0-1.0

    # 테스트 감지
    has_tests: bool = False
    test_file_count: int = 0
    test_to_code_ratio: float = 0.0       # test files / total files
