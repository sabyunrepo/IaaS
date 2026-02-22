"""
Uploads API — 파일 업로드.

POST   /api/uploads/{file_type}          — admin 업로드
POST   /api/public/uploads/{file_type}   — 지원자 업로드
GET    /api/storage/{file_path:path}     — 로컬 파일 서빙
"""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse

from infrastructure.persistence.application_repository import FileUploadRepository
from infrastructure.storage.storage_service import get_storage, validate_upload
from interface.api.middleware.auth import get_current_user

router = APIRouter(tags=["uploads"])


@router.post("/api/uploads/{file_type}")
async def upload_file_admin(
    file_type: str,
    file: UploadFile,
    user: dict = Depends(get_current_user),
):
    """관리자 파일 업로드."""
    if file_type not in ("resume", "cover_letter", "portfolio"):
        raise HTTPException(400, "Invalid file type")

    file_bytes = await file.read()
    try:
        validate_upload(file.filename or "", file_bytes, file_type, file.content_type)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    # 저장
    storage = get_storage()
    key = f"uploads/admin/{user['user_id']}/{file_type}/{uuid.uuid4()}/{file.filename}"
    path = storage.upload_file(key, file_bytes, file.content_type or "application/octet-stream")

    # 메타데이터 저장
    repo = FileUploadRepository()
    upload_id = await repo.save_metadata(
        uploader_type="admin",
        uploader_ref=user["user_id"],
        file_type=file_type,
        file_name=file.filename or "unknown",
        file_path=path,
        content_type=file.content_type,
        size_bytes=len(file_bytes),
    )

    return {"id": upload_id, "file_path": path, "file_name": file.filename}


@router.post("/api/public/uploads/{file_type}")
async def upload_file_public(
    file_type: str,
    file: UploadFile,
):
    """지원자 파일 업로드 (인증 불필요, rate limit 적용)."""
    if file_type not in ("resume", "cover_letter", "portfolio"):
        raise HTTPException(400, "Invalid file type")

    file_bytes = await file.read()
    try:
        validate_upload(file.filename or "", file_bytes, file_type, file.content_type)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    storage = get_storage()
    key = f"uploads/public/{file_type}/{uuid.uuid4()}/{file.filename}"
    path = storage.upload_file(key, file_bytes, file.content_type or "application/octet-stream")

    repo = FileUploadRepository()
    upload_id = await repo.save_metadata(
        uploader_type="candidate",
        uploader_ref=None,
        file_type=file_type,
        file_name=file.filename or "unknown",
        file_path=path,
        content_type=file.content_type,
        size_bytes=len(file_bytes),
    )

    return {"id": upload_id, "file_path": path, "file_name": file.filename}


@router.get("/api/storage/{file_path:path}")
async def serve_file(
    file_path: str,
    user: dict = Depends(get_current_user),
):
    """로컬 저장소 파일을 서빙한다 (path traversal 방지)."""
    storage = get_storage()
    abs_path = storage.get_local_path(file_path)

    # path traversal 방지
    base = os.path.realpath(storage._local_path)
    real_path = os.path.realpath(abs_path)
    if not real_path.startswith(base):
        raise HTTPException(403, "Access denied")

    if not os.path.exists(real_path):
        raise HTTPException(404, "File not found")

    return FileResponse(real_path)
