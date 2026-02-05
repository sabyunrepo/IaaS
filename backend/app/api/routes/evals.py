"""
backend/app/api/routes/evals.py
Phoenix 평가 API 엔드포인트
"""
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
async def get_eval_status():
    """Phoenix 평가 서비스 상태 확인"""
    return {
        "enabled": phoenix_eval_service.is_enabled(),
        "endpoint": phoenix_eval_service.client.endpoint if phoenix_eval_service.client else None,
    }


@router.post("/hallucination", response_model=EvalResponse)
async def evaluate_hallucination(request: EvalRequest):
    """환각(Hallucination) 평가

    답변이 컨텍스트에 기반하는지 확인
    """
    if not phoenix_eval_service.is_enabled():
        raise HTTPException(status_code=503, detail="Phoenix not enabled")

    result = await phoenix_eval_service.evaluate_hallucination(
        question=request.question,
        context=request.context,
        answer=request.answer,
    )
    return result


@router.post("/relevance", response_model=EvalResponse)
async def evaluate_relevance(request: EvalRequest):
    """관련성(Relevance) 평가

    답변이 질문에 관련 있는지 확인
    """
    if not phoenix_eval_service.is_enabled():
        raise HTTPException(status_code=503, detail="Phoenix not enabled")

    result = await phoenix_eval_service.evaluate_relevance(
        question=request.question,
        answer=request.answer,
    )
    return result


@router.post("/batch/interview-questions")
async def evaluate_interview_questions(request: BatchEvalRequest):
    """면접 질문 배치 평가

    생성된 면접 질문들의 품질을 평가
    """
    if not phoenix_eval_service.is_enabled():
        raise HTTPException(status_code=503, detail="Phoenix not enabled")

    results = await phoenix_eval_service.evaluate_interview_questions(
        questions=request.questions,
        jd_context=request.jd_context,
        candidate_context=request.candidate_context,
    )
    return {"evaluations": results}
