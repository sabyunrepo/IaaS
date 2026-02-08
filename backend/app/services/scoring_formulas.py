"""
backend/app/services/scoring_formulas.py
Evidence-Based Scoring Formulas — 산업 표준 기반 점수 공식

모든 점수 계산의 단일 진실 소스 (Single Source of Truth).
각 공식은 학술/산업 근거 주석으로 출처를 명시.

References:
- McCabe (1976): Cyclomatic Complexity
- Radon: Python complexity grading (A-F)
- SonarQube SQALE: Maintainability rating (A-E)
- SFIA v9: Skills Framework for the Information Age
- Dreyfus (1980): Skill Acquisition Model
- Bird et al. (2011, Microsoft Research): Code Ownership & Quality
- Google re:Work: Structured Interview Rubrics
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================
# Data Classes
# ============================================================

@dataclass
class ScoringResult:
    """점수 계산 결과 (투명성 보장)"""
    score: int          # 0-100
    source: str         # 점수 산출 근거 설명
    confidence: str     # "high" | "medium" | "low"
    components: dict = field(default_factory=dict)  # 세부 항목별 점수


@dataclass
class RadarScores:
    """레이더 차트 점수 (5축)"""
    candidate: list[int]    # [role_fit, technical, execution, communication, code_quality]
    required: list[int]     # 경험 레벨별 기대 점수
    sources: list[str]      # 각 축의 산출 근거
    confidence: str         # 전체 데이터 신뢰도


# ============================================================
# 1. Cyclomatic Complexity Normalization
#    Source: McCabe (1976), Radon documentation
#    Scale: CC → 0-100 score (lower CC = higher score)
# ============================================================

# Radon grading thresholds (per-function basis)
RADON_GRADES = [
    (5,  100, "A"),   # CC 1-5:  Low risk, simple
    (10,  85, "B"),   # CC 6-10: Low risk, well-structured
    (20,  65, "C"),   # CC 11-20: Moderate risk
    (30,  40, "D"),   # CC 21-30: High risk
    (40,  20, "E"),   # CC 31-40: Very high risk
]


def normalize_cyclomatic_complexity(avg_cc: float) -> tuple[int, str]:
    """Cyclomatic Complexity → 0-100 점수 (Radon scale)

    Args:
        avg_cc: 평균 순환 복잡도 (PyDriller에서 추출)

    Returns:
        (score, grade) — score는 0-100, grade는 A-F

    Reference: McCabe, T. (1976). "A Complexity Measure".
               IEEE Transactions on Software Engineering.
    """
    if avg_cc <= 0:
        return 50, "N/A"  # 데이터 없음

    for threshold, score, grade in RADON_GRADES:
        if avg_cc <= threshold:
            return score, grade

    return 10, "F"  # CC > 40: Error-prone, unstable


# ============================================================
# 2. Code Quality Composite Score
#    Source: SonarQube SQALE, CodeClimate 10-point assessment
#    Weights: Industry standard composite (Ranger, daily.dev)
# ============================================================

# Weight rationale (from industry practice):
# - CC: 직접적인 코드 가독성 지표 (30%)
# - Test coverage: 품질 보증 신호 (30%)
# - Documentation: 유지보수성 (20%)
# - Code stability: 성숙도 (20%)
CODE_QUALITY_WEIGHTS = {
    "complexity": 0.30,     # Cyclomatic complexity (Radon)
    "test_coverage": 0.30,  # Statement coverage (SonarQube default gate: 80%)
    "documentation": 0.20,  # Docstring/comment ratio
    "stability": 0.20,      # Inverse churn ratio (Microsoft Research)
}


def calculate_code_quality_score(
    quality_metrics: dict,
    stats: dict | None = None,
) -> ScoringResult:
    """코드 품질 종합 점수 계산

    Args:
        quality_metrics: {test_coverage, documentation_score, complexity_score}
        stats: {total_additions, total_deletions, avg_complexity}

    Returns:
        ScoringResult with composite score

    Reference: SonarQube SQALE model, CodeClimate maintainability
    """
    components = {}
    has_data = False

    # 1. Cyclomatic Complexity (30%)
    avg_cc = 0.0
    if stats:
        avg_cc = stats.get("avg_complexity", 0)
    if avg_cc <= 0:
        avg_cc = quality_metrics.get("complexity_score", 50)
    cc_score, cc_grade = normalize_cyclomatic_complexity(avg_cc)
    components["complexity"] = {
        "score": cc_score,
        "raw": avg_cc,
        "grade": cc_grade,
        "source": "PyDriller avg_complexity → Radon scale (McCabe 1976)",
    }
    if avg_cc > 0:
        has_data = True

    # 2. Test Coverage (30%)
    test_cov = quality_metrics.get("test_coverage", 0)
    components["test_coverage"] = {
        "score": min(100, max(0, test_cov)),
        "raw": test_cov,
        "source": "AST test file detection → coverage percentage",
        "threshold": "SonarQube default gate: 80%",
    }
    if test_cov > 0:
        has_data = True

    # 3. Documentation Score (20%)
    doc_score = quality_metrics.get("documentation_score", 0)
    components["documentation"] = {
        "score": min(100, max(0, doc_score)),
        "raw": doc_score,
        "source": "Docstring/comment ratio analysis",
    }
    if doc_score > 0:
        has_data = True

    # 4. Code Stability — inverse churn ratio (20%)
    stability = 50  # default when no git data
    if stats:
        additions = stats.get("total_additions", 0)
        deletions = stats.get("total_deletions", 0)
        if additions > 0:
            churn_ratio = deletions / (additions + 1)
            # Lower churn = more stable. churn_ratio ~0.3 is healthy
            stability = max(0, min(100, int(100 - churn_ratio * 60)))
            has_data = True
    components["stability"] = {
        "score": stability,
        "source": "Git churn ratio (deletions/additions) — Bird et al. 2011, Microsoft Research",
    }

    # Weighted composite
    composite = (
        components["complexity"]["score"] * CODE_QUALITY_WEIGHTS["complexity"]
        + components["test_coverage"]["score"] * CODE_QUALITY_WEIGHTS["test_coverage"]
        + components["documentation"]["score"] * CODE_QUALITY_WEIGHTS["documentation"]
        + components["stability"]["score"] * CODE_QUALITY_WEIGHTS["stability"]
    )
    final_score = max(0, min(100, int(composite)))

    confidence = "high" if has_data else "low"
    if has_data and (test_cov == 0 or avg_cc <= 0):
        confidence = "medium"

    return ScoringResult(
        score=final_score,
        source="Composite: CC(30%) + TestCov(30%) + Docs(20%) + Stability(20%)",
        confidence=confidence,
        components=components,
    )


# ============================================================
# 3. Radar 5-Axis Scores — Evidence-Based
#    Each axis has a transparent formula with cited weights.
# ============================================================

def calculate_radar_scores(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
    experience_level: str = "미들",
) -> RadarScores:
    """5축 레이더 점수 계산 (결정론적)

    축: [role_fit, technical, execution, communication, code_quality]

    Args:
        jd_analysis: JD 분석 결과
        code_analysis: 코드 분석 결과 (optional)
        document_analysis: 문서 분석 결과
        experience_level: 경험 레벨 (CTO/VP, 시니어, 미들, 주니어, 신입)

    Returns:
        RadarScores with candidate/required scores and sources
    """
    profile = document_analysis.get("profile", {})
    quality = {}
    stats = {}
    if code_analysis:
        quality = code_analysis.get("quality_metrics", {})
        stats = code_analysis.get("stats", {})

    sources = []

    # --- Axis 0: Role Fit ---
    # Primary: JD match score (70%), Skill overlap ratio (30%)
    jd_match = document_analysis.get("jd_match_score", 0.5)
    jd_component = int(jd_match * 100) * 0.70

    # Skill overlap
    jd_skills = {r.get("skill", "").lower() for r in jd_analysis.get("requirements", [])}
    raw_skills = profile.get("skills", [])
    candidate_skills = set()
    if isinstance(raw_skills, dict):
        candidate_skills = {s.lower() for s in raw_skills.keys()}
    elif isinstance(raw_skills, list):
        candidate_skills = {s.lower() for s in raw_skills if isinstance(s, str)}

    code_techs = set()
    if code_analysis:
        code_techs = {s.lower() for s in code_analysis.get("tech_stack", [])}
    all_candidate = candidate_skills | code_techs

    overlap = len(jd_skills & all_candidate) / max(len(jd_skills), 1)
    skill_component = int(overlap * 100) * 0.30

    role_fit = max(0, min(100, int(jd_component + skill_component)))
    sources.append(
        f"role_fit: jd_match({jd_match:.2f})×70% + skill_overlap({overlap:.2f})×30%"
    )

    # --- Axis 1: Technical Depth ---
    # Code quality (40%), Tech breadth (30%), Contribution consistency (30%)
    cq = calculate_code_quality_score(quality, stats)
    cq_component = cq.score * 0.40

    tech_stack = code_analysis.get("tech_stack", []) if code_analysis else []
    tech_breadth = min(100, len(tech_stack) * 12)  # 8+ techs = ~100
    tb_component = tech_breadth * 0.30

    monthly = code_analysis.get("monthly_contributions", []) if code_analysis else []
    active_months = sum(1 for m in monthly if m > 0) if monthly else 0
    consistency = int((active_months / 12) * 100) if monthly else 0
    cc_component = consistency * 0.30

    technical = max(0, min(100, int(cq_component + tb_component + cc_component)))
    sources.append(
        f"technical: code_quality({cq.score})×40% + tech_breadth({tech_breadth})×30% + consistency({consistency})×30%"
    )

    # --- Axis 2: Execution & Delivery ---
    # Experience SFIA score (40%), Commit consistency (30%), Code volume (30%)
    exp_years = profile.get("experience_years", 0) or 0
    _, sfia_score = classify_experience_level(exp_years)
    exp_component = sfia_score * 0.40

    commit_consistency_component = consistency * 0.30  # reuse from above

    total_additions = stats.get("total_additions", 0) if stats else 0
    # Log-scale: 10K additions ≈ 100 score
    code_volume = min(100, int(math.log10(max(total_additions, 1)) * 25))
    vol_component = code_volume * 0.30

    execution = max(0, min(100, int(exp_component + commit_consistency_component + vol_component)))
    sources.append(
        f"execution: sfia_exp({sfia_score})×40% + commit_consistency({consistency})×30% + code_volume({code_volume})×30%"
    )

    # --- Axis 3: Communication ---
    # Documentation score (50%), Code readability (50%)
    doc_score = quality.get("documentation_score", 50)
    doc_component = doc_score * 0.50

    # Code readability = inverse complexity (lower CC = more readable)
    cc_norm, _ = normalize_cyclomatic_complexity(stats.get("avg_complexity", 0) if stats else 0)
    readability_component = cc_norm * 0.50

    communication = max(0, min(100, int(doc_component + readability_component)))
    sources.append(
        f"communication: doc_score({doc_score})×50% + readability({cc_norm})×50%"
    )

    # --- Axis 4: Code Quality ---
    # Direct composite code quality score
    code_quality = cq.score
    sources.append(
        f"code_quality: composite({cq.score}) = {cq.source}"
    )

    # No-code fallback: reasonable defaults when GitHub data unavailable
    if not code_analysis:
        technical = max(technical, 40)  # Floor at 40 with no code data
        code_quality = 50  # Neutral

    candidate = [role_fit, technical, execution, communication, code_quality]
    required = get_required_scores(experience_level)

    # Determine confidence
    confidence = "low"
    data_sources = 0
    if code_analysis:
        data_sources += 1
    if profile.get("skills"):
        data_sources += 1
    if document_analysis.get("jd_match_score") is not None:
        data_sources += 1
    if data_sources >= 3:
        confidence = "high"
    elif data_sources >= 2:
        confidence = "medium"

    return RadarScores(
        candidate=candidate,
        required=required,
        sources=sources,
        confidence=confidence,
    )


# ============================================================
# 4. Required Scores — Dynamic by Experience Level
#    Source: SFIA v9 autonomy/complexity levels
# ============================================================

# Required scores per axis: [role_fit, technical, execution, communication, code_quality]
# Higher experience level → higher expected bar
REQUIRED_SCORES_BY_LEVEL = {
    "CTO/VP":  [85, 90, 90, 85, 85],   # SFIA 6-7: Full accountability
    "시니어":   [80, 85, 80, 75, 80],   # SFIA 4-5: Substantial responsibility
    "미들":     [70, 70, 65, 65, 65],   # SFIA 3:   General direction
    "주니어":   [55, 55, 45, 50, 50],   # SFIA 2:   Routine direction
    "신입":     [45, 45, 35, 40, 40],   # SFIA 1:   Close direction
}


def get_required_scores(experience_level: str) -> list[int]:
    """경험 레벨에 따른 기대 점수 반환

    Reference: SFIA v9 (sfia-online.org) — autonomy & complexity levels
    """
    return REQUIRED_SCORES_BY_LEVEL.get(
        experience_level,
        REQUIRED_SCORES_BY_LEVEL["미들"],  # default
    )


# ============================================================
# 5. Experience Level Classification — SFIA Framework
#    Source: SFIA v9, Dreyfus Model (1980)
# ============================================================

# SFIA → Internal level mapping with score (0-100 scale)
SFIA_LEVELS = [
    # (max_years, level_name, sfia_level, score, dreyfus_stage)
    (2,   "Junior",    "SFIA 1-2", 25, "Novice/Advanced Beginner"),
    (5,   "Mid",       "SFIA 3",   50, "Competent"),
    (8,   "Senior",    "SFIA 4",   70, "Proficient"),
    (12,  "Lead",      "SFIA 5",   85, "Expert"),
    (999, "Principal", "SFIA 6-7", 95, "Expert"),
]


def classify_experience_level(
    experience_years: int,
    has_management: bool = False,
) -> tuple[str, int]:
    """경험 연수 → 레벨 분류 (SFIA/Dreyfus 기반)

    Args:
        experience_years: 경력 연수
        has_management: CTO/VP 직함 보유 여부

    Returns:
        (level_name, score) — e.g., ("Senior", 70)

    Reference:
        - SFIA v9 (sfia-online.org/en/sfia-9/skills/programming-software-development)
        - Dreyfus, S. & Dreyfus, H. (1980). "A Five-Stage Model of the Mental Activities
          Involved in Directed Skill Acquisition". UC Berkeley.
    """
    if has_management and experience_years >= 8:
        return "Lead", 85

    for max_years, level, _sfia, score, _dreyfus in SFIA_LEVELS:
        if experience_years <= max_years:
            return level, score

    return "Principal", 95


def map_experience_level_label(experience_level: str) -> str:
    """한글 경험 레벨 → 영문 레벨 매핑

    입력: CreateJobPage에서 사용자가 선택한 한글 레벨
    """
    LABEL_MAP = {
        "CTO/VP": "Lead",
        "시니어": "Senior",
        "미들": "Mid",
        "주니어": "Junior",
        "신입": "Junior",
    }
    return LABEL_MAP.get(experience_level, "Mid")


# ============================================================
# 6. Overall Match Percentage — Weighted Composite
#    Source: Composite scoring model (Scale.jobs, Ranger)
# ============================================================

# Weight rationale:
# - Skill match: Direct JD-candidate alignment (35%)
# - Code quality: Objective code evidence (25%)
# - Experience fit: SFIA-level appropriateness (25%)
# - JD document match: Resume-JD textual match (15%)
OVERALL_MATCH_WEIGHTS = {
    "skill_match": 0.35,
    "code_quality": 0.25,
    "experience_fit": 0.25,
    "jd_match": 0.15,
}


def calculate_overall_match(
    skill_match_score: int,
    code_quality_score: int,
    experience_fit_score: int,
    jd_match_score: float,
) -> ScoringResult:
    """전체 매칭 점수 계산 (가중 평균)

    Args:
        skill_match_score: 스킬 매칭 점수 (0-100)
        code_quality_score: 코드 품질 점수 (0-100)
        experience_fit_score: 경험 적합도 점수 (0-100)
        jd_match_score: JD 매칭 점수 (0.0-1.0)

    Returns:
        ScoringResult

    Reference: Weighted scoring model (daily.dev, Scale.jobs)
               Score = Σ(wi × si) / Σ(wi) where Σ(wi) = 1.0
    """
    jd_normalized = int(jd_match_score * 100)

    composite = (
        skill_match_score * OVERALL_MATCH_WEIGHTS["skill_match"]
        + code_quality_score * OVERALL_MATCH_WEIGHTS["code_quality"]
        + experience_fit_score * OVERALL_MATCH_WEIGHTS["experience_fit"]
        + jd_normalized * OVERALL_MATCH_WEIGHTS["jd_match"]
    )
    final = max(0, min(100, int(composite)))

    return ScoringResult(
        score=final,
        source=(
            f"skill({skill_match_score})×35% + code({code_quality_score})×25% "
            f"+ exp({experience_fit_score})×25% + jd({jd_normalized})×15%"
        ),
        confidence="high",
        components={
            "skill_match": skill_match_score,
            "code_quality": code_quality_score,
            "experience_fit": experience_fit_score,
            "jd_match": jd_normalized,
        },
    )


# ============================================================
# 7. Data Confidence System — 3-Tier
#    Based on available data source count & quality
# ============================================================

def calculate_data_confidence(
    has_github: bool,
    has_linkedin: bool,
    has_resume: bool,
    github_commits: int = 0,
    linkedin_positions: int = 0,
) -> tuple[str, int]:
    """데이터 신뢰도 등급 계산

    Returns:
        (tier, score) where tier is "high"/"medium"/"low"
        and score is 0-100

    Tiers:
        🟢 High  (≥80%): 3 sources with substantial data
        🟡 Medium (50-79%): 2+ sources or 1 source with good data
        🔴 Low   (<50%): Single weak source
    """
    score = 0

    # Source availability (each source adds base points)
    if has_resume:
        score += 25
    if has_github:
        score += 25
    if has_linkedin:
        score += 20

    # Data quality bonuses
    if github_commits >= 50:
        score += 15
    elif github_commits >= 10:
        score += 8
    elif github_commits > 0:
        score += 3

    if linkedin_positions >= 3:
        score += 10
    elif linkedin_positions >= 1:
        score += 5

    # Bonus for having all 3 sources
    if has_github and has_linkedin and has_resume:
        score += 5

    score = min(100, score)

    if score >= 80:
        return "high", score
    elif score >= 50:
        return "medium", score
    else:
        return "low", score


# ============================================================
# 8. JD Match Level — Threshold-Based Classification
#    Source: Google re:Work structured interview guidelines
# ============================================================

def classify_jd_match(jd_match_score: float) -> str:
    """JD 매칭 레벨 분류

    Args:
        jd_match_score: 0.0-1.0

    Returns:
        "High" | "Medium" | "Low"

    Reference: Google re:Work — structured interview scoring thresholds
    """
    if jd_match_score >= 0.75:
        return "High"
    elif jd_match_score >= 0.50:
        return "Medium"
    else:
        return "Low"
