"""
backend/app/api/routes/evals.py
Phoenix 평가 API 엔드포인트
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.deps import get_current_user_or_api_key
from app.core.rate_limit import limiter
from app.services.phoenix_eval import phoenix_eval_service

router = APIRouter(prefix="/evals", tags=["evals"])


class EvalRequest(BaseModel):
    """평가 요청"""
    question: str
    context: str
    answer: str


class EvalResponse(BaseModel):
    """평가 응답"""
    score: float | None
    label: str
    explanation: str


class BatchEvalRequest(BaseModel):
    """배치 평가 요청"""
    questions: list[dict[str, Any]]
    jd_context: str
    candidate_context: str


@router.get("/status")
@limiter.limit("30/minute")
async def get_eval_status(request: Request, _user=Depends(get_current_user_or_api_key)):
    """Phoenix 평가 서비스 상태 확인"""
    return {
        "enabled": phoenix_eval_service.is_enabled(),
        "endpoint": phoenix_eval_service.client.endpoint if phoenix_eval_service.client else None,
    }


@router.post("/hallucination", response_model=EvalResponse)
@limiter.limit("10/minute")
async def evaluate_hallucination(request: Request, body: EvalRequest, _user=Depends(get_current_user_or_api_key)):
    """환각(Hallucination) 평가

    답변이 컨텍스트에 기반하는지 확인
    """
    if not phoenix_eval_service.is_enabled():
        raise HTTPException(status_code=503, detail="Phoenix not enabled")

    result = await phoenix_eval_service.evaluate_hallucination(
        question=body.question,
        context=body.context,
        answer=body.answer,
    )
    return result


@router.post("/relevance", response_model=EvalResponse)
@limiter.limit("10/minute")
async def evaluate_relevance(request: Request, body: EvalRequest, _user=Depends(get_current_user_or_api_key)):
    """관련성(Relevance) 평가

    답변이 질문에 관련 있는지 확인
    """
    if not phoenix_eval_service.is_enabled():
        raise HTTPException(status_code=503, detail="Phoenix not enabled")

    result = await phoenix_eval_service.evaluate_relevance(
        question=body.question,
        answer=body.answer,
    )
    return result


@router.post("/batch/interview-questions")
@limiter.limit("5/minute")
async def evaluate_interview_questions(request: Request, body: BatchEvalRequest, _user=Depends(get_current_user_or_api_key)):
    """면접 질문 배치 평가

    생성된 면접 질문들의 품질을 평가
    """
    if not phoenix_eval_service.is_enabled():
        raise HTTPException(status_code=503, detail="Phoenix not enabled")

    results = await phoenix_eval_service.evaluate_interview_questions(
        questions=body.questions,
        jd_context=body.jd_context,
        candidate_context=body.candidate_context,
    )
    return {"evaluations": results}
