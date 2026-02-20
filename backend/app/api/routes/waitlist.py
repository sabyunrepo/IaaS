"""
backend/app/api/routes/waitlist.py
랜딩페이지 얼리엑세스 대기자 등록 API
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import WaitlistEntryDB

router = APIRouter(prefix="/api/v1/waitlist", tags=["waitlist"])


class WaitlistRequest(BaseModel):
    name: str
    email: EmailStr


class WaitlistCountResponse(BaseModel):
    count: int


@router.post("", status_code=201)
async def register_waitlist(
    data: WaitlistRequest,
    db: AsyncSession = Depends(get_db),
):
    """대기자 등록 (중복 이메일은 무시)"""
    existing = await db.execute(
        select(WaitlistEntryDB).where(WaitlistEntryDB.email == data.email)
    )
    if existing.scalar_one_or_none():
        return {"message": "Already registered"}

    entry = WaitlistEntryDB(name=data.name.strip(), email=data.email)
    db.add(entry)
    await db.commit()
    return {"message": "Registered successfully"}


@router.get("/count", response_model=WaitlistCountResponse)
async def get_waitlist_count(
    db: AsyncSession = Depends(get_db),
):
    """대기자 수 조회"""
    WAITLIST_OFFSET = 27
    result = await db.execute(select(func.count()).select_from(WaitlistEntryDB))
    count = (result.scalar() or 0) + WAITLIST_OFFSET
    return {"count": count}
