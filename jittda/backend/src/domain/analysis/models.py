"""
Analysis 도메인 모델

순수 Pydantic v2 모델 — 외부 의존성 없음 (pydantic만 허용).
코드 복잡도 지표, 진위성 점수, 스킬 평가 데이터 구조 정의.
"""
from pydantic import BaseModel, Field


class ComplexityMetrics(BaseModel, strict=True):
    """
    코드 복잡도 지표 집합.

    정적 분석 도구(radon, lizard 등)에서 추출한 복잡도 수치를 보관한다.
    maintainability_index는 0~100 범위로 제한된다.
    """

    cyclomatic_complexity: float = Field(ge=0)
    halstead_difficulty: float = Field(ge=0)
    halstead_volume: float = Field(ge=0)
    maintainability_index: float = Field(ge=0, le=100)
    cognitive_complexity: float = Field(ge=0)


class AuthenticityScore(BaseModel, strict=True):
    """
    코드 진위성 점수.

    AI 작성 의심도, 표절 비율, 인간 타이핑 패턴 등을 0~1 범위의
    비율로 기록한다.
    """

    human_typing_ratio: float = Field(ge=0, le=1)
    originality_ratio: float = Field(ge=0, le=1)
    ai_code_suspicion: float = Field(ge=0, le=1)
    plagiarism_ratio: float = Field(ge=0, le=1)
    style_consistency: float = Field(ge=0, le=1)


class SkillAssessment(BaseModel, strict=True):
    """
    개별 기술 스킬 평가 결과.

    특정 스킬에 대한 숙련도, 근거 출처, 신뢰도를 기록한다.
    proficiency: beginner | intermediate | advanced | expert
    confidence: high | medium | low
    """

    skill_name: str
    proficiency: str  # beginner | intermediate | advanced | expert
    evidence_count: int = Field(ge=0)
    evidence_sources: list[str]
    confidence: str  # high | medium | low
