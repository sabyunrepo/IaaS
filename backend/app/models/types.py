"""
backend/app/models/types.py
공통 타입 정의
"""
from typing import Literal, TypeAlias

# 지원 언어
SupportedLanguage: TypeAlias = Literal[
    "ko", "en", "ja", "zh-CN", "zh-TW",
    "es", "de", "fr", "pt", "vi", "th", "id"
]

# 경험 레벨
ExperienceLevel: TypeAlias = Literal[
    "Entry", "Junior", "Mid", "Senior", "CTO/VP",
    "신입", "주니어", "미들", "시니어",  # backward compat
]

# 질문 난이도
Difficulty: TypeAlias = Literal["Easy", "Medium", "Hard"]

# 요구사항 구분
RequirementCategory: TypeAlias = Literal["필수", "우대"]

# 코드 패턴 유형
PatternType: TypeAlias = Literal["design_pattern", "anti_pattern", "idiom"]

# 이슈 심각도
Severity: TypeAlias = Literal["info", "warning", "error"]

# 스킬 매칭 유형
MatchType: TypeAlias = Literal["exact", "similar", "partial", "none"]
