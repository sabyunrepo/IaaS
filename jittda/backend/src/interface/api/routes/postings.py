"""
Postings API — 채용 공고 CRUD.

POST   /api/postings
GET    /api/postings
GET    /api/postings/{id}
PUT    /api/postings/{id}
DELETE /api/postings/{id}
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from infrastructure.persistence.posting_repository import PostingRepository
from interface.api.middleware.auth import get_current_user
from interface.api.schemas.posting_schemas import (
    PostingCreateRequest,
    PostingResponse,
    PostingUpdateRequest,
)

router = APIRouter(prefix="/api/postings", tags=["postings"])


def _validate_uuid(value: str) -> None:
    try:
        uuid.UUID(value)
    except ValueError:
        raise HTTPException(400, "Invalid UUID format") from None


@router.post("", response_model=PostingResponse, status_code=201)
async def create_posting(
    body: PostingCreateRequest,
    user: dict = Depends(get_current_user),
):
    """새 채용 공고를 생성한다."""
    repo = PostingRepository()
    posting_id = await repo.create(
        user_id=user["user_id"],
        title=body.title,
        department=body.department,
        jd_description=body.jd_description,
        jd_languages=body.jd_languages,
        jd_tech_stack=body.jd_tech_stack,
        jd_experience_years=body.jd_experience_years,
        auto_analyze=body.auto_analyze,
        status=body.status,
    )
    posting = await repo.get(posting_id)
    return PostingResponse(**posting, application_count=0)


@router.get("", response_model=list[PostingResponse])
async def list_postings(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """사용자의 공고 목록을 조회한다."""
    repo = PostingRepository()
    postings = await repo.list_by_user(user["user_id"], status=status, limit=limit)
    return [PostingResponse(**p) for p in postings]


@router.get("/{posting_id}", response_model=PostingResponse)
async def get_posting(
    posting_id: str,
    user: dict = Depends(get_current_user),
):
    """공고 상세를 조회한다."""
    _validate_uuid(posting_id)
    repo = PostingRepository()
    posting = await repo.get(posting_id)
    if not posting:
        raise HTTPException(404, "Posting not found")
    if posting["user_id"] != user["user_id"]:
        raise HTTPException(403, "Access denied")
    return PostingResponse(**posting)


@router.put("/{posting_id}", response_model=PostingResponse)
async def update_posting(
    posting_id: str,
    body: PostingUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """공고를 수정한다."""
    _validate_uuid(posting_id)
    repo = PostingRepository()

    posting = await repo.get(posting_id)
    if not posting:
        raise HTTPException(404, "Posting not found")
    if posting["user_id"] != user["user_id"]:
        raise HTTPException(403, "Access denied")

    fields = body.model_dump(exclude_unset=True)
    if fields:
        await repo.update(posting_id, **fields)

    updated = await repo.get(posting_id)
    return PostingResponse(**updated)


@router.delete("/{posting_id}", status_code=204)
async def delete_posting(
    posting_id: str,
    user: dict = Depends(get_current_user),
):
    """공고를 삭제한다."""
    _validate_uuid(posting_id)
    repo = PostingRepository()

    posting = await repo.get(posting_id)
    if not posting:
        raise HTTPException(404, "Posting not found")
    if posting["user_id"] != user["user_id"]:
        raise HTTPException(403, "Access denied")

    await repo.delete(posting_id)
