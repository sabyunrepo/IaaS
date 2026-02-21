"""
backend/app/api/routes/candidates.py
후보자 CRUD + JD 매칭 + 비교 API
"""
import logging
import uuid as _uuid

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.api.deps import get_current_user_or_api_key
from app.models.database import UserDB
from app.services import candidate_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


# ============================================================
# Request / Response Models
# ============================================================

class CreateCandidateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str | None = None
    experience_years: int | None = None
    experience_level: str | None = None
    skills: list[str] = Field(default_factory=list)
    github_username: str | None = None
    linkedin_url: str | None = None
    profile_data: dict | None = None


class UpdateCandidateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    experience_years: int | None = None
    experience_level: str | None = None
    skills: list[str] | None = None
    github_username: str | None = None
    linkedin_url: str | None = None
    profile_data: dict | None = None


class CreateJDRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    jd_text: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    experience_level: str = "Mid"
    output_language: str = "ko"


class SearchCandidatesRequest(BaseModel):
    jd_text: str = Field(..., min_length=10)
    experience_level: str = "Mid"
    output_language: str = "ko"


# ============================================================
# Candidate Endpoints
# ============================================================

def _candidate_to_dict(c) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "email": c.email,
        "experience_years": c.experience_years,
        "experience_level": c.experience_level,
        "skills": c.skills or [],
        "github_username": c.github_username,
        "linkedin_url": c.linkedin_url,
        "data_completeness": c.data_completeness,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _candidate_detail_to_dict(c) -> dict:
    d = _candidate_to_dict(c)
    d["profile_data"] = c.profile_data or {}
    return d


@router.post("", status_code=201)
@limiter.limit("10/minute")
async def create_candidate(
    request: Request,
    body: CreateCandidateRequest,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """후보자 등록"""
    candidate = await candidate_service.create_candidate(
        user_id=user.id,
        name=body.name,
        db=db,
        email=body.email,
        experience_years=body.experience_years,
        experience_level=body.experience_level,
        skills=body.skills,
        github_username=body.github_username,
        linkedin_url=body.linkedin_url,
        profile_data=body.profile_data,
    )
    return _candidate_detail_to_dict(candidate)


@router.get("")
@limiter.limit("60/minute")
async def list_candidates(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    skill: list[str] | None = Query(None, description="Filter by skills"),
    level: str | None = Query(None, description="Filter by experience level"),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """후보자 목록 조회"""
    candidates = await candidate_service.list_candidates(
        user_id=user.id,
        db=db,
        limit=limit,
        offset=offset,
        skill_filter=skill,
        level_filter=level,
    )
    return [_candidate_to_dict(c) for c in candidates]


@router.get("/{candidate_id}")
@limiter.limit("120/minute")
async def get_candidate(
    request: Request,
    candidate_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """후보자 상세 조회"""
    candidate = await candidate_service.get_candidate(candidate_id, user.id, db)
    return _candidate_detail_to_dict(candidate)


@router.put("/{candidate_id}")
@limiter.limit("10/minute")
async def update_candidate(
    request: Request,
    candidate_id: str,
    body: UpdateCandidateRequest,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """후보자 업데이트"""
    update_data = body.model_dump(exclude_none=True)
    candidate = await candidate_service.update_candidate(
        candidate_id, user.id, db, **update_data,
    )
    return _candidate_detail_to_dict(candidate)


@router.delete("/{candidate_id}", status_code=204)
@limiter.limit("10/minute")
async def delete_candidate(
    request: Request,
    candidate_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """후보자 삭제"""
    await candidate_service.delete_candidate(candidate_id, user.id, db)


# ============================================================
# JD Endpoints
# ============================================================

def _jd_to_dict(jd) -> dict:
    return {
        "id": str(jd.id),
        "title": jd.title,
        "required_skills": jd.required_skills or [],
        "preferred_skills": jd.preferred_skills or [],
        "is_active": jd.is_active,
        "created_at": jd.created_at.isoformat() if jd.created_at else None,
    }


@router.post("/jd", status_code=201, tags=["job-descriptions"])
@limiter.limit("10/minute")
async def create_jd(
    request: Request,
    body: CreateJDRequest,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """JD 생성"""
    jd = await candidate_service.create_jd(
        user_id=user.id,
        title=body.title,
        db=db,
        jd_text=body.jd_text,
        required_skills=body.required_skills,
        preferred_skills=body.preferred_skills,
    )
    result = _jd_to_dict(jd)
    result["jd_text"] = jd.jd_text
    return result


@router.get("/jd", tags=["job-descriptions"])
@limiter.limit("60/minute")
async def list_jds(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """JD 목록 조회"""
    jds = await candidate_service.list_jds(user.id, db, limit=limit, offset=offset)
    return [_jd_to_dict(j) for j in jds]


@router.get("/jd/{jd_id}", tags=["job-descriptions"])
@limiter.limit("120/minute")
async def get_jd(
    request: Request,
    jd_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """JD 상세 조회"""
    jd = await candidate_service.get_jd(jd_id, user.id, db)
    result = _jd_to_dict(jd)
    result["jd_text"] = jd.jd_text
    result["jd_analysis"] = jd.jd_analysis
    return result


@router.put("/jd/{jd_id}", tags=["job-descriptions"])
@limiter.limit("10/minute")
async def update_jd(
    request: Request,
    jd_id: str,
    body: dict,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """JD 수정 (jd_text)"""
    jd = await candidate_service.get_jd(jd_id, user.id, db)
    if "jd_text" in body:
        jd.jd_text = body["jd_text"]
    await db.flush()
    result = _jd_to_dict(jd)
    result["jd_text"] = jd.jd_text
    return result


@router.delete("/jd/{jd_id}", status_code=204, tags=["job-descriptions"])
@limiter.limit("10/minute")
async def delete_jd(
    request: Request,
    jd_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """JD 삭제"""
    jd = await candidate_service.get_jd(jd_id, user.id, db)
    await db.delete(jd)


@router.get("/my-profile")
@limiter.limit("60/minute")
async def get_my_profile(
    request: Request,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """내 후보자 프로필 조회 (candidate 역할인 경우)"""
    # user_id로 내 candidate 조회
    candidates = await candidate_service.list_candidates(
        user_id=user.id, db=db, limit=1, offset=0,
    )
    if candidates:
        return _candidate_detail_to_dict(candidates[0])
    return None


# ============================================================
# Matching Endpoints
# ============================================================

@router.post("/{candidate_id}/match/{jd_id}")
@limiter.limit("10/minute")
async def match_candidate_to_jd(
    request: Request,
    candidate_id: str,
    jd_id: str,
    body: MatchRequest = MatchRequest(),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """후보자-JD 매칭 실행

    후보자 프로필과 JD를 비교하여 매칭 점수를 계산합니다.
    JD에 jd_analysis가 없으면 먼저 JD 분석을 실행합니다.
    """
    # 1. 후보자, JD 로드
    candidate = await candidate_service.get_candidate(candidate_id, user.id, db)
    jd = await candidate_service.get_jd(jd_id, user.id, db)

    # 2. JD 분석 필요 시 실행
    jd_analysis = jd.jd_analysis
    if not jd_analysis and jd.jd_text:
        jd_analysis = await _run_jd_analysis(jd.jd_text, body.output_language)
        jd.jd_analysis = jd_analysis
    elif not jd_analysis:
        from app.exceptions import ValidationError
        raise ValidationError("JD has no text to analyze")

    # 3. 프로필 기반 매칭
    candidate_profile = candidate.profile_data or {}
    # profile_data가 비어있으면 기본 프로필 구성
    if not candidate_profile.get("skills"):
        candidate_profile = _build_minimal_profile(candidate)

    from app.workflows.activities.jd_matching import match_candidate_to_jd as _match_fn
    # Activity를 직접 호출 (Temporal 밖에서 실행)
    match_result = await _execute_matching(
        candidate_profile, jd_analysis, body.experience_level, body.output_language,
    )

    # 4. 결과 DB 저장
    match_db = await candidate_service.upsert_match(
        user_id=user.id,
        candidate_id=candidate_id,
        jd_id=jd_id,
        db=db,
        overall_match_score=match_result.get("overall_match_score", 0.0),
        skill_match_score=match_result.get("skill_match_score", 0.0),
        skill_matches=match_result.get("skill_matches"),
        gaps=match_result.get("gaps"),
        match_explanation=match_result.get("match_explanation", ""),
        confidence_level=match_result.get("confidence_level", "medium"),
    )

    return {
        "candidate_id": candidate_id,
        "jd_id": jd_id,
        **match_result,
    }


@router.get("/compare")
@limiter.limit("30/minute")
async def compare_candidates(
    request: Request,
    jd_id: str = Query(..., description="JD ID for comparison"),
    ids: str = Query(..., description="Comma-separated candidate IDs"),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """다중 후보자 비교

    같은 JD에 대해 여러 후보자의 매칭 결과를 비교합니다.
    """
    candidate_ids = [cid.strip() for cid in ids.split(",") if cid.strip()]
    if len(candidate_ids) < 2:
        from app.exceptions import ValidationError
        raise ValidationError("At least 2 candidate IDs required")
    if len(candidate_ids) > 10:
        from app.exceptions import ValidationError
        raise ValidationError("Maximum 10 candidates for comparison")

    # JD 존재 확인
    await candidate_service.get_jd(jd_id, user.id, db)

    # 매칭 결과 조회
    matches = await candidate_service.get_matches_for_candidates(
        candidate_ids, jd_id, user.id, db,
    )

    # 후보자 기본 정보도 함께 반환
    results = []
    for match in matches:
        candidate = await candidate_service.get_candidate(
            str(match.candidate_id), user.id, db,
        )
        results.append({
            "candidate": _candidate_to_dict(candidate),
            "match": {
                "overall_match_score": match.overall_match_score,
                "skill_match_score": match.skill_match_score,
                "skill_matches": match.skill_matches,
                "gaps": match.gaps,
                "match_explanation": match.match_explanation,
                "confidence_level": match.confidence_level,
                "computed_at": match.computed_at.isoformat() if match.computed_at else None,
            },
        })

    # 매칭 미실행 후보자 표시
    matched_ids = {str(m.candidate_id) for m in matches}
    for cid in candidate_ids:
        if cid not in matched_ids:
            try:
                candidate = await candidate_service.get_candidate(cid, user.id, db)
                results.append({
                    "candidate": _candidate_to_dict(candidate),
                    "match": None,  # 매칭 미실행
                })
            except Exception:
                pass

    return {
        "jd_id": jd_id,
        "candidates": results,
        "total": len(results),
    }


@router.get("/jd/{jd_id}/ranking", tags=["job-descriptions"])
@limiter.limit("30/minute")
async def get_jd_candidate_ranking(
    request: Request,
    jd_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """JD별 후보자 랭킹 (매치율 내림차순)"""
    await candidate_service.get_jd(jd_id, user.id, db)
    matches = await candidate_service.get_matches_by_jd(
        jd_id, user.id, db, limit=limit, offset=offset,
    )
    results = []
    for rank, match in enumerate(matches, start=1 + offset):
        candidate = await candidate_service.get_candidate(
            str(match.candidate_id), user.id, db,
        )
        results.append({
            "rank": rank,
            "candidate": _candidate_to_dict(candidate),
            "overall_match_score": match.overall_match_score,
            "skill_match_score": match.skill_match_score,
            "confidence_level": match.confidence_level,
            "computed_at": match.computed_at.isoformat() if match.computed_at else None,
        })
    return {"jd_id": jd_id, "ranking": results, "total": len(results)}


# ============================================================
# Internal Helpers
# ============================================================

async def _run_jd_analysis(jd_text: str, output_language: str) -> dict:
    """JD 분석 실행 (Temporal Activity를 직접 호출)"""
    try:
        from app.workflows.activities.jd_analysis import analyze_jd
        return await analyze_jd(jd_text=jd_text, output_language=output_language)
    except Exception as e:
        logger.warning(f"JD analysis failed: {e}")
        # Fallback: 기본 구조 반환
        return {
            "requirements": [],
            "company_culture": {},
            "job_summary": jd_text[:200] if jd_text else "",
        }


async def _execute_matching(
    candidate_profile: dict,
    jd_analysis: dict,
    experience_level: str,
    output_language: str,
) -> dict:
    """매칭 로직 실행 (Activity 로직 직접 호출)"""
    from app.services.profile_scoring import profile_weighted_skill_overlap, extract_profile_skills
    from app.services.scoring_formulas import calculate_radar_scores

    # 스킬 매칭
    jd_requirements = jd_analysis.get("requirements", [])
    overlap_score, match_details = profile_weighted_skill_overlap(
        jd_requirements, candidate_profile,
    )
    skill_match_score = round(overlap_score * 100, 1)

    matched_skills = [d for d in match_details if d.get("matched")]
    gap_skills = [d for d in match_details if not d.get("matched")]

    # 레이더 차트
    code_profile = candidate_profile.get("code_profile") or {}
    doc_proxy = {
        "skills": [s.get("canonical_name", "") for s in candidate_profile.get("skills", [])],
        "work_experience": candidate_profile.get("work_history", []),
        "experience_years": candidate_profile.get("experience_years", 0),
    }

    radar = calculate_radar_scores(
        jd_analysis=jd_analysis,
        code_analysis=code_profile if code_profile.get("total_repos_analyzed", 0) > 0 else None,
        document_analysis=doc_proxy,
        experience_level=experience_level,
        output_language=output_language,
        candidate_profile=candidate_profile,
    )

    radar_scores = radar.candidate if isinstance(radar.candidate, list) else [50, 50, 50, 50, 50]
    role_fit = radar_scores[0] if len(radar_scores) > 0 else 50
    technical = radar_scores[1] if len(radar_scores) > 1 else 50
    overall = round(role_fit * 0.30 + skill_match_score * 0.40 + technical * 0.30, 1)

    # 채용 추천
    if overall >= 80 and skill_match_score >= 75:
        recommendation = "강력추천"
    elif overall >= 65 and skill_match_score >= 55:
        recommendation = "추천"
    elif overall >= 45:
        recommendation = "보류"
    else:
        recommendation = "비추천"

    gaps = [
        {
            "skill": g.get("skill", ""),
            "importance": "required" if g.get("category", "우대") in ("필수", "required", "must") else "preferred",
        }
        for g in gap_skills
    ]

    data_completeness = candidate_profile.get("data_completeness", 0.0)
    confidence = "high" if data_completeness >= 0.8 else ("medium" if data_completeness >= 0.5 else "low")

    return {
        "overall_match_score": overall,
        "skill_match_score": skill_match_score,
        "skill_matches": {
            "matched": matched_skills,
            "gaps": gaps,
            "overlap_score": overlap_score,
            "total_jd_skills": len(jd_requirements),
            "matched_count": len(matched_skills),
            "gap_count": len(gap_skills),
        },
        "radar_scores": {
            "candidate": radar.candidate,
            "required": radar.required,
            "sources": radar.sources,
            "human_sources": radar.human_sources,
        },
        "gaps": gaps,
        "match_explanation": f"Overall match {overall:.0f}%: {len(matched_skills)} matched, {len(gap_skills)} gaps. Recommendation: {recommendation}.",
        "hiring_recommendation": recommendation,
        "confidence_level": confidence,
    }


def _build_minimal_profile(candidate) -> dict:
    """CandidateDB에서 최소 프로필 구성 (profile_data가 비어있을 때)"""
    skills = []
    for s in (candidate.skills or []):
        skills.append({
            "canonical_name": s,
            "aliases": [],
            "sources": ["manual"],
            "category": None,
            "confidence": 0.8,
            "implied_skills": [],
        })
    return {
        "name": candidate.name,
        "email": candidate.email,
        "skills": skills,
        "work_history": [],
        "experience_years": candidate.experience_years or 0,
        "experience_level": candidate.experience_level,
        "data_completeness": candidate.data_completeness or 0.3,
        "confidence_level": "low",
        "data_sources": ["manual"],
    }
