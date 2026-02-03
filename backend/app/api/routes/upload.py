"""
backend/app/api/routes/upload.py
파일 업로드 API 엔드포인트
"""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user_or_api_key
from app.models.database import UserDB
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

# 허용된 파일 타입
ALLOWED_EXTENSIONS = {
    "resume": [".pdf"],
    "portfolio": [".pdf", ".docx"],
    "cover_letter": [".pdf", ".docx"],
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class UploadResponse(BaseModel):
    """파일 업로드 응답"""
    file_path: str
    file_name: str
    file_type: str
    size_bytes: int


@router.post("/{file_type}", response_model=UploadResponse)
async def upload_file(
    file_type: str,
    file: UploadFile = File(...),
    user: UserDB = Depends(get_current_user_or_api_key),
):
    """파일 업로드 (resume, portfolio, cover_letter)"""
    if file_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {list(ALLOWED_EXTENSIONS.keys())}",
        )

    # 파일 확장자 검증
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS[file_type]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension for {file_type}. Allowed: {ALLOWED_EXTENSIONS[file_type]}",
        )

    # 파일 크기 검증
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB",
        )

    # 파일 저장 경로 생성
    file_id = str(uuid.uuid4())
    file_name = f"{file_id}{file_ext}"

    # LocalStack S3 또는 로컬 저장소 사용
    if settings.STORAGE_BACKEND == "s3":
        # S3 업로드
        import aioboto3

        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or "test",
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or "test",
        ) as s3:
            bucket = settings.S3_BUCKET or "vantict-data"
            key = f"uploads/{user.id}/{file_type}/{file_name}"

            await s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
            )

            file_path = f"s3://{bucket}/{key}"
    else:
        # 로컬 저장소
        local_path = Path(settings.LOCAL_STORAGE_PATH or "/app/data")
        upload_dir = local_path / "uploads" / str(user.id) / file_type
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_full_path = upload_dir / file_name
        file_full_path.write_bytes(content)

        file_path = str(file_full_path)

    logger.info(f"File uploaded: {file_path} by user {user.id}")

    return UploadResponse(
        file_path=file_path,
        file_name=file.filename or file_name,
        file_type=file_type,
        size_bytes=len(content),
    )
