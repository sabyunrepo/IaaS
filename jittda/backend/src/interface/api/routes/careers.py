"""
Careers API — Public 커리어 페이지.

GET    /api/careers/{slug}                     — 회사 정보 + 활성 공고
GET    /api/careers/{slug}/{postingId}         — 공고 상세
POST   /api/careers/{slug}/{postingId}/apply   — 지원 (multipart)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from infrastructure.persistence.application_repository import ApplicationRepository
from infrastructure.persistence.posting_repository import PostingRepository
from infrastructure.persistence.repository import UserRepository
from interface.api.schemas.application_schemas import (
    PublicApplyRequest,
    PublicApplyResponse,
)

router = APIRouter(prefix="/api/careers", tags=["careers"])


@router.get("/{slug}")
async def get_career_page(slug: str):
    """회사 정보와 활성 공고 목록을 반환한다."""
    user_repo = UserRepository()
    company = await user_repo.get_by_slug(slug)
    if not company:
        raise HTTPException(404, "회사를 찾을 수 없습니다.")

    posting_repo = PostingRepository()
    postings = await posting_repo.list_active_by_slug(slug)

    return {
        "company": {
            "name": company.get("company_name") or company.get("name"),
            "slug": company.get("company_slug"),
            "logo": company.get("company_logo"),
            "description": company.get("company_description"),
        },
        "postings": [
            {
                "id": p["id"],
                "title": p["title"],
                "department": p["department"],
                "jd_languages": p["jd_languages"],
                "jd_tech_stack": p["jd_tech_stack"],
                "jd_experience_years": p["jd_experience_years"],
                "created_at": p["created_at"],
            }
            for p in postings
        ],
    }


@router.get("/{slug}/{posting_id}")
async def get_career_posting(slug: str, posting_id: str):
    """공고 상세를 반환한다."""
    try:
        uuid.UUID(posting_id)
    except ValueError:
        raise HTTPException(400, "Invalid posting ID") from None

    user_repo = UserRepository()
    company = await user_repo.get_by_slug(slug)
    if not company:
        raise HTTPException(404, "회사를 찾을 수 없습니다.")

    posting_repo = PostingRepository()
    posting = await posting_repo.get(posting_id)
    if not posting or posting["user_id"] != company["id"]:
        raise HTTPException(404, "공고를 찾을 수 없습니다.")
    if posting["status"] != "active":
        raise HTTPException(404, "공고가 활성 상태가 아닙니다.")

    return {
        "company": {
            "name": company.get("company_name") or company.get("name"),
            "slug": company.get("company_slug"),
            "logo": company.get("company_logo"),
        },
        "posting": {
            "id": posting["id"],
            "title": posting["title"],
            "department": posting["department"],
            "jd_description": posting["jd_description"],
            "jd_languages": posting["jd_languages"],
            "jd_tech_stack": posting["jd_tech_stack"],
            "jd_experience_years": posting["jd_experience_years"],
        },
    }


@router.post("/{slug}/{posting_id}/apply", response_model=PublicApplyResponse)
async def apply_to_posting(
    slug: str,
    posting_id: str,
    body: PublicApplyRequest,
):
    """지원자가 직접 지원한다."""
    try:
        uuid.UUID(posting_id)
    except ValueError:
        raise HTTPException(400, "Invalid posting ID") from None

    user_repo = UserRepository()
    company = await user_repo.get_by_slug(slug)
    if not company:
        raise HTTPException(404, "회사를 찾을 수 없습니다.")

    posting_repo = PostingRepository()
    posting = await posting_repo.get(posting_id)
    if not posting or posting["user_id"] != company["id"]:
        raise HTTPException(404, "공고를 찾을 수 없습니다.")
    if posting["status"] != "active":
        raise HTTPException(400, "지원이 마감되었습니다.")

    app_repo = ApplicationRepository()
    try:
        app_id = await app_repo.create(
            posting_id=posting_id,
            candidate_name=body.candidate_name,
            candidate_email=body.candidate_email,
            github_username=body.github_username,
            github_urls=body.github_urls,
            linkedin_url=body.linkedin_url,
            resume_path=body.resume_path,
            cover_letter_path=body.cover_letter_path,
            portfolio_path=body.portfolio_path,
            source="self_apply",
        )
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(409, "이미 지원한 이메일입니다.") from e
        raise

    # auto_analyze가 켜져 있으면 자동 분석 시작은 별도 로직으로 처리
    # (향후 확장 포인트)

    return PublicApplyResponse(application_id=app_id)
