"""
backend/app/models/deep_analysis.py
Deep Analysis 탭 데이터 모델
"""
from typing import Literal

from pydantic import BaseModel, Field


class EngineeringDNAItem(BaseModel):
    """Engineering DNA 항목 (Deprecated: JIT-12/17에서 프론트엔드·백엔드 모두 제거, 기존 데이터 역직렬화용 유지)"""
    label: str  # 예: "테스트 커버리지"
    value: int  # 퍼센트 (0-100)
    display: str  # 표시 텍스트 (예: "82%", "우수", "미확인")
    color: Literal["emerald", "blue", "amber", "red", "slate"]
    note: str | None = None  # 추가 설명
    tooltip: str | None = None  # 마우스오버 설명


class RiskFlag(BaseModel):
    """리스크 플래그"""
    label: str
    detail: str


class SkillMatchRow(BaseModel):
    """스킬 매칭 테이블 행"""
    skill: str  # JD 요구 스킬
    candidate: str  # 후보자 보유 스킬
    type: Literal["exact", "similar", "partial", "none"]
    evidence: str  # 증거 출처
    confidence: int  # 신뢰도 (0-100)
    related_questions: list[int] = Field(default_factory=list)  # 관련 질문 번호 (JIT-11)


class DeepAnalysis(BaseModel):
    """Deep Analysis 탭 데이터"""
    # 5축 레이더 차트: [role_fit, technical, execution, communication, code_quality]
    radar_candidate: list[int] = Field(default_factory=list)  # 후보자 점수
    radar_required: list[int] = Field(default_factory=list)  # JD 요구 점수
    engineering_dna: list[EngineeringDNAItem] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    skill_table: list[SkillMatchRow] = Field(default_factory=list)
    overall_match: int = 0  # 전체 매칭 퍼센트
    # 점수 투명성 메타데이터 (PR #138: Evidence-Based Scoring)
    score_sources: list[str] = Field(default_factory=list)  # 각 축의 산출 근거
    data_confidence: str = "medium"  # "high" | "medium" | "low"
    data_confidence_score: int = 50  # 0-100 데이터 신뢰도 수치
