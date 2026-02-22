"""
Applications API — 지원 CRUD + 분석 트리거.

POST   /api/postings/{id}/applications
GET    /api/postings/{id}/applications
GET    /api/postings/{id}/applications/{appId}
PUT    /api/postings/{id}/applications/{appId}
DELETE /api/postings/{id}/applications/{appId}
POST   /api/postings/{id}/applications/{appId}/analyze
GET    /api/postings/{id}/applications/{appId}/result
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from infrastructure.persistence.application_repository import ApplicationRepository
from infrastructure.persistence.posting_repository import PostingRepository
from infrastructure.persistence.repository import JobRepository
from interface.api.middleware.auth import get_current_user
from interface.api.schemas.application_schemas import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationUpdateRequest,
)

router = APIRouter(prefix="/api/postings/{posting_id}/applications", tags=["applications"])


def _validate_uuid(value: str) -> None:
    try:
        uuid.UUID(value)
    except ValueError:
        raise HTTPException(400, "Invalid UUID format") from None


async def _check_posting_ownership(posting_id: str, user_id: str) -> dict:
    """공고 소유권을 검증하고 공고를 반환한다."""
    repo = PostingRepository()
    posting = await repo.get(posting_id)
    if not posting:
        raise HTTPException(404, "Posting not found")
    if posting["user_id"] != user_id:
        raise HTTPException(403, "Access denied")
    return posting


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    posting_id: str,
    body: ApplicationCreateRequest,
    user: dict = Depends(get_current_user),
):
    """관리자가 지원자를 수동 등록한다."""
    _validate_uuid(posting_id)
    await _check_posting_ownership(posting_id, user["user_id"])

    repo = ApplicationRepository()
    app_id = await repo.create(
        posting_id=posting_id,
        candidate_name=body.candidate_name,
        candidate_email=body.candidate_email,
        github_username=body.github_username,
        github_urls=body.github_urls,
        linkedin_url=body.linkedin_url,
        resume_path=body.resume_path,
        cover_letter_path=body.cover_letter_path,
        portfolio_path=body.portfolio_path,
        memo=body.memo,
        source="admin_manual",
    )
    app = await repo.get(app_id)
    return ApplicationResponse(**app)


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    posting_id: str,
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """공고의 지원 목록을 조회한다."""
    _validate_uuid(posting_id)
    await _check_posting_ownership(posting_id, user["user_id"])

    repo = ApplicationRepository()
    apps = await repo.list_by_posting(posting_id, status=status, limit=limit)
    return [ApplicationResponse(**a) for a in apps]


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    posting_id: str,
    app_id: str,
    user: dict = Depends(get_current_user),
):
    """지원 상세를 조회한다."""
    _validate_uuid(posting_id)
    _validate_uuid(app_id)
    await _check_posting_ownership(posting_id, user["user_id"])

    repo = ApplicationRepository()
    app = await repo.get(app_id)
    if not app or app["posting_id"] != posting_id:
        raise HTTPException(404, "Application not found")
    return ApplicationResponse(**app)


@router.put("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    posting_id: str,
    app_id: str,
    body: ApplicationUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """지원 정보를 수정한다."""
    _validate_uuid(posting_id)
    _validate_uuid(app_id)
    await _check_posting_ownership(posting_id, user["user_id"])

    repo = ApplicationRepository()
    app = await repo.get(app_id)
    if not app or app["posting_id"] != posting_id:
        raise HTTPException(404, "Application not found")

    fields = body.model_dump(exclude_unset=True)
    if fields:
        await repo.update(app_id, **fields)

    updated = await repo.get(app_id)
    return ApplicationResponse(**updated)


@router.delete("/{app_id}", status_code=204)
async def delete_application(
    posting_id: str,
    app_id: str,
    user: dict = Depends(get_current_user),
):
    """지원을 삭제한다."""
    _validate_uuid(posting_id)
    _validate_uuid(app_id)
    await _check_posting_ownership(posting_id, user["user_id"])

    repo = ApplicationRepository()
    app = await repo.get(app_id)
    if not app or app["posting_id"] != posting_id:
        raise HTTPException(404, "Application not found")

    await repo.delete(app_id)


@router.post("/{app_id}/analyze", status_code=202)
async def analyze_application(
    posting_id: str,
    app_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """지원자 분석을 시작한다 (Temporal Workflow 트리거)."""
    _validate_uuid(posting_id)
    _validate_uuid(app_id)
    posting = await _check_posting_ownership(posting_id, user["user_id"])

    app_repo = ApplicationRepository()
    app = await app_repo.get(app_id)
    if not app or app["posting_id"] != posting_id:
        raise HTTPException(404, "Application not found")

    if app["status"] == "analyzing":
        raise HTTPException(409, "Analysis already in progress")

    # Job 입력 데이터 구성
    input_data = {
        "candidate_username": app.get("github_username"),
        "github_urls": app.get("github_urls", []),
        "linkedin_url": app.get("linkedin_url"),
        "jd_languages": posting.get("jd_languages", []),
        "jd_tech_stack": posting.get("jd_tech_stack", []),
        "jd_description": posting.get("jd_description"),
        "resume_path": app.get("resume_path"),
        "cover_letter_path": app.get("cover_letter_path"),
    }

    # Job 생성
    job_repo = JobRepository()
    job_id = await job_repo.create(input_data, user_id=user["user_id"])

    # Application에 Job 연결
    await app_repo.link_job(app_id, job_id)

    # Temporal Workflow 시작
    temporal_client = getattr(request.app.state, "temporal_client", None)
    if not temporal_client:
        raise HTTPException(503, "Temporal service unavailable")

    from application.temporal import TASK_QUEUE
    from application.temporal.workflows import AnalysisPipeline

    await temporal_client.start_workflow(
        AnalysisPipeline.run,
        job_id,
        id=f"analysis-{job_id}",
        task_queue=TASK_QUEUE,
    )

    return {"job_id": job_id, "status": "analyzing"}


@router.get("/{app_id}/result")
async def get_application_result(
    posting_id: str,
    app_id: str,
    user: dict = Depends(get_current_user),
):
    """지원자 분석 결과를 조회한다 (프록시 → /api/jobs/{jobId}/result)."""
    _validate_uuid(posting_id)
    _validate_uuid(app_id)
    await _check_posting_ownership(posting_id, user["user_id"])

    app_repo = ApplicationRepository()
    app = await app_repo.get(app_id)
    if not app or app["posting_id"] != posting_id:
        raise HTTPException(404, "Application not found")

    if not app.get("job_id"):
        raise HTTPException(400, "분석이 시작되지 않았습니다.")

    job_repo = JobRepository()
    job = await job_repo.get(app["job_id"])
    if not job:
        raise HTTPException(404, "Job not found")

    if job["status"] != "completed":
        raise HTTPException(400, f"분석이 아직 완료되지 않았습니다. 상태: {job['status']}")

    return job.get("result_data", {})
