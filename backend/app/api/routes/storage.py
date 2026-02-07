"""
backend/app/api/routes/storage.py
로컬 스토리지 파일 서빙 (avatars 등)
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/storage", tags=["storage"])

STORAGE_ROOT = Path("/app/data")


@router.get("/{file_path:path}")
async def serve_storage_file(file_path: str):
    """로컬 스토리지 파일 서빙 (path traversal 방지)"""
    full_path = (STORAGE_ROOT / file_path).resolve()

    # path traversal 공격 방지
    if not str(full_path).startswith(str(STORAGE_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(full_path)
