"""
backend/app/services/candidate_service.py
후보자 & JD 비즈니스 로직 서비스
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ValidationError, CandidateNotFoundError, JDNotFoundError
from app.models.database import (
    CandidateDB, JobDescriptionDB, CandidateJDMatchDB, UserDB,
)

import logging

logger = logging.getLogger(__name__)


async def create_candidate(
    user_id: uuid.UUID,
    name: str,
    db: AsyncSession,
    email: str | None = None,
    experience_years: int | None = None,
    experience_level: str | None = None,
    skills: list[str] | None = None,
    github_username: str | None = None,
    linkedin_url: str | None = None,
    profile_data: dict | None = None,
) -> CandidateDB:
    """후보자 생성"""
    candidate = CandidateDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        email=email,
        experience_years=experience_years,
        experience_level=experience_level,
        skills=skills or [],
        github_username=github_username,
        linkedin_url=linkedin_url,
        profile_data=profile_data or {},
        data_completeness=_compute_completeness(
            email=email,
            github_username=github_username,
            linkedin_url=linkedin_url,
            skills=skills,
            profile_data=profile_data,
        ),
    )
    db.add(candidate)
    await db.flush()
    return candidate


async def get_candidate(
    candidate_id: str, user_id: uuid.UUID, db: AsyncSession,
) -> CandidateDB:
    """후보자 조회 (소유권 확인)"""
    result = await db.execute(
        select(CandidateDB).where(CandidateDB.id == uuid.UUID(candidate_id))
    )
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise CandidateNotFoundError(candidate_id)
    if candidate.user_id != user_id:
        from app.exceptions import AuthorizationError
        raise AuthorizationError("Not your candidate")
    return candidate


async def list_candidates(
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    skill_filter: list[str] | None = None,
    level_filter: str | None = None,
) -> list[CandidateDB]:
    """사용자의 후보자 목록"""
    query = (
        select(CandidateDB)
        .where(CandidateDB.user_id == user_id)
    )
    if skill_filter:
        query = query.where(CandidateDB.skills.overlap(skill_filter))
    if level_filter:
        query = query.where(CandidateDB.experience_level == level_filter)
    query = query.order_by(CandidateDB.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_candidate(
    candidate_id: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    **kwargs,
) -> CandidateDB:
    """후보자 업데이트"""
    candidate = await get_candidate(candidate_id, user_id, db)
    allowed_fields = {
        "name", "email", "experience_years", "experience_level",
        "skills", "github_username", "linkedin_url", "profile_data",
        "data_completeness",
    }
    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            setattr(candidate, key, value)
    candidate.updated_at = datetime.now(timezone.utc)
    return candidate


async def delete_candidate(
    candidate_id: str, user_id: uuid.UUID, db: AsyncSession,
) -> None:
    """후보자 삭제"""
    candidate = await get_candidate(candidate_id, user_id, db)
    await db.delete(candidate)


# ============================================================
# JD CRUD
# ============================================================

async def create_jd(
    user_id: uuid.UUID,
    title: str,
    db: AsyncSession,
    jd_text: str | None = None,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    jd_analysis: dict | None = None,
) -> JobDescriptionDB:
    """JD 생성"""
    jd = JobDescriptionDB(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title,
        jd_text=jd_text,
        required_skills=required_skills or [],
        preferred_skills=preferred_skills or [],
        jd_analysis=jd_analysis,
    )
    db.add(jd)
    await db.flush()
    return jd


async def get_jd(
    jd_id: str, user_id: uuid.UUID, db: AsyncSession,
) -> JobDescriptionDB:
    """JD 조회 (소유권 확인)"""
    result = await db.execute(
        select(JobDescriptionDB).where(JobDescriptionDB.id == uuid.UUID(jd_id))
    )
    jd = result.scalar_one_or_none()
    if jd is None:
        raise JDNotFoundError(jd_id)
    if jd.user_id != user_id:
        from app.exceptions import AuthorizationError
        raise AuthorizationError("Not your job description")
    return jd


async def list_jds(
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    active_only: bool = True,
) -> list[JobDescriptionDB]:
    """사용자의 JD 목록"""
    query = select(JobDescriptionDB).where(JobDescriptionDB.user_id == user_id)
    if active_only:
        query = query.where(JobDescriptionDB.is_active == True)
    query = query.order_by(JobDescriptionDB.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


# ============================================================
# Match Queries
# ============================================================

async def get_match(
    candidate_id: str, jd_id: str, user_id: uuid.UUID, db: AsyncSession,
) -> CandidateJDMatchDB | None:
    """특정 후보자-JD 매칭 결과 조회"""
    result = await db.execute(
        select(CandidateJDMatchDB).where(
            CandidateJDMatchDB.candidate_id == uuid.UUID(candidate_id),
            CandidateJDMatchDB.jd_id == uuid.UUID(jd_id),
            CandidateJDMatchDB.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_match(
    user_id: uuid.UUID,
    candidate_id: str,
    jd_id: str,
    db: AsyncSession,
    overall_match_score: float = 0.0,
    skill_match_score: float = 0.0,
    skill_matches: dict | None = None,
    gaps: list | None = None,
    match_explanation: str = "",
    confidence_level: str = "medium",
) -> CandidateJDMatchDB:
    """매칭 결과 upsert (UNIQUE(candidate_id, jd_id))"""
    existing = await get_match(candidate_id, jd_id, user_id, db)
    if existing:
        existing.overall_match_score = overall_match_score
        existing.skill_match_score = skill_match_score
        existing.skill_matches = skill_matches or {}
        existing.gaps = gaps or []
        existing.match_explanation = match_explanation
        existing.confidence_level = confidence_level
        existing.computed_at = datetime.now(timezone.utc)
        return existing

    match = CandidateJDMatchDB(
        id=uuid.uuid4(),
        user_id=user_id,
        candidate_id=uuid.UUID(candidate_id),
        jd_id=uuid.UUID(jd_id),
        overall_match_score=overall_match_score,
        skill_match_score=skill_match_score,
        skill_matches=skill_matches or {},
        gaps=gaps or [],
        match_explanation=match_explanation,
        confidence_level=confidence_level,
    )
    db.add(match)
    await db.flush()
    return match


async def get_matches_by_jd(
    jd_id: str, user_id: uuid.UUID, db: AsyncSession,
    limit: int = 50, offset: int = 0,
) -> list[CandidateJDMatchDB]:
    """JD별 후보자 랭킹 (매치율 내림차순)"""
    result = await db.execute(
        select(CandidateJDMatchDB)
        .where(
            CandidateJDMatchDB.jd_id == uuid.UUID(jd_id),
            CandidateJDMatchDB.user_id == user_id,
        )
        .order_by(CandidateJDMatchDB.overall_match_score.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_matches_for_candidates(
    candidate_ids: list[str], jd_id: str, user_id: uuid.UUID, db: AsyncSession,
) -> list[CandidateJDMatchDB]:
    """특정 후보자들의 JD 매칭 결과 (비교용)"""
    uuids = [uuid.UUID(cid) for cid in candidate_ids]
    result = await db.execute(
        select(CandidateJDMatchDB)
        .where(
            CandidateJDMatchDB.jd_id == uuid.UUID(jd_id),
            CandidateJDMatchDB.user_id == user_id,
            CandidateJDMatchDB.candidate_id.in_(uuids),
        )
        .order_by(CandidateJDMatchDB.overall_match_score.desc())
    )
    return list(result.scalars().all())


# ============================================================
# Helpers
# ============================================================

def _compute_completeness(
    email: str | None = None,
    github_username: str | None = None,
    linkedin_url: str | None = None,
    skills: list[str] | None = None,
    profile_data: dict | None = None,
) -> float:
    """데이터 완전성 계산 (0.0-1.0)"""
    score = 0.2  # name is always provided
    if email:
        score += 0.1
    if github_username:
        score += 0.2
    if linkedin_url:
        score += 0.2
    if skills and len(skills) > 0:
        score += 0.15
    if profile_data and len(profile_data) > 0:
        score += 0.15
    return min(score, 1.0)
