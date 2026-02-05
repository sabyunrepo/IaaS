"""
backend/app/services/phoenix_eval.py
Phoenix 평가(Evals) 및 실험(Experiments) 서비스

역할 분리:
- Langfuse: LLM 트레이싱, 프롬프트 관리, 비용 추적
- Phoenix: 평가(Evals), 실험(Experiments), 데이터셋
"""
import logging
from typing import Any

import phoenix as px
from phoenix.evals import (
    HallucinationEvaluator,
    QAEvaluator,
    RelevanceEvaluator,
    run_evals,
)
from phoenix.evals.models import LiteLLMModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class PhoenixEvalService:
    """Phoenix 평가 서비스 - LLM 출력 품질 평가 전용"""

    def __init__(self):
        self._client = None
        self._eval_model = None

    @property
    def client(self) -> px.Client | None:
        """Phoenix 클라이언트 (lazy initialization)"""
        if self._client is None and settings.PHOENIX_COLLECTOR_ENDPOINT:
            try:
                self._client = px.Client(endpoint=settings.PHOENIX_COLLECTOR_ENDPOINT)
                logger.info(f"Phoenix client connected: {settings.PHOENIX_COLLECTOR_ENDPOINT}")
            except Exception as e:
                logger.warning(f"Phoenix connection failed: {e}")
        return self._client

    @property
    def eval_model(self) -> LiteLLMModel | None:
        """평가용 LLM 모델 (GLM 무료 모델 사용)"""
        if self._eval_model is None:
            try:
                # 평가용으로 무료 GLM 모델 사용
                self._eval_model = LiteLLMModel(
                    model=settings.GLM_MODEL,  # zai/glm-4.5-flash (무료)
                )
                logger.info(f"Phoenix eval model initialized: {settings.GLM_MODEL}")
            except Exception as e:
                logger.warning(f"Phoenix eval model init failed: {e}")
        return self._eval_model

    def is_enabled(self) -> bool:
        """Phoenix 활성화 여부"""
        return settings.PHOENIX_COLLECTOR_ENDPOINT is not None

    # ========================================
    # 평가 (Evals) - Langfuse에 없는 기능
    # ========================================

    async def evaluate_hallucination(
        self,
        question: str,
        context: str,
        answer: str,
    ) -> dict[str, Any]:
        """환각(Hallucination) 평가 - 답변이 컨텍스트에 기반하는지 확인

        Args:
            question: 질문
            context: 참조 컨텍스트 (이력서, JD 등)
            answer: LLM 생성 답변

        Returns:
            {"score": float, "label": str, "explanation": str}
        """
        if not self.is_enabled() or not self.eval_model:
            return {"score": None, "label": "skipped", "explanation": "Phoenix not enabled"}

        try:
            evaluator = HallucinationEvaluator(self.eval_model)
            result = evaluator.evaluate(
                input=question,
                output=answer,
                reference=context,
            )
            return {
                "score": result.score,
                "label": result.label,
                "explanation": result.explanation,
            }
        except Exception as e:
            logger.error(f"Hallucination eval failed: {e}")
            return {"score": None, "label": "error", "explanation": str(e)}

    async def evaluate_relevance(
        self,
        question: str,
        answer: str,
    ) -> dict[str, Any]:
        """관련성(Relevance) 평가 - 답변이 질문에 관련 있는지 확인

        Args:
            question: 질문
            answer: LLM 생성 답변

        Returns:
            {"score": float, "label": str, "explanation": str}
        """
        if not self.is_enabled() or not self.eval_model:
            return {"score": None, "label": "skipped", "explanation": "Phoenix not enabled"}

        try:
            evaluator = RelevanceEvaluator(self.eval_model)
            result = evaluator.evaluate(
                input=question,
                output=answer,
            )
            return {
                "score": result.score,
                "label": result.label,
                "explanation": result.explanation,
            }
        except Exception as e:
            logger.error(f"Relevance eval failed: {e}")
            return {"score": None, "label": "error", "explanation": str(e)}

    async def evaluate_qa_correctness(
        self,
        question: str,
        answer: str,
        reference_answer: str,
    ) -> dict[str, Any]:
        """QA 정확성 평가 - 답변이 정답과 일치하는지 확인

        Args:
            question: 질문
            answer: LLM 생성 답변
            reference_answer: 정답 (ground truth)

        Returns:
            {"score": float, "label": str, "explanation": str}
        """
        if not self.is_enabled() or not self.eval_model:
            return {"score": None, "label": "skipped", "explanation": "Phoenix not enabled"}

        try:
            evaluator = QAEvaluator(self.eval_model)
            result = evaluator.evaluate(
                input=question,
                output=answer,
                reference=reference_answer,
            )
            return {
                "score": result.score,
                "label": result.label,
                "explanation": result.explanation,
            }
        except Exception as e:
            logger.error(f"QA eval failed: {e}")
            return {"score": None, "label": "error", "explanation": str(e)}

    # ========================================
    # 배치 평가 - 여러 항목 한번에 평가
    # ========================================

    async def evaluate_interview_questions(
        self,
        questions: list[dict[str, Any]],
        jd_context: str,
        candidate_context: str,
    ) -> list[dict[str, Any]]:
        """면접 질문 배치 평가

        Args:
            questions: [{"question_text": str, "why_matters": str, ...}]
            jd_context: JD 분석 결과
            candidate_context: 후보자 분석 결과

        Returns:
            평가 결과 리스트
        """
        if not self.is_enabled():
            return [{"eval_skipped": True} for _ in questions]

        results = []
        combined_context = f"JD:\n{jd_context}\n\nCandidate:\n{candidate_context}"

        for q in questions:
            question_text = q.get("question_text", "")
            why_matters = q.get("why_matters", "")

            # 환각 평가: why_matters가 컨텍스트에 기반하는지
            hallucination_result = await self.evaluate_hallucination(
                question=question_text,
                context=combined_context,
                answer=why_matters,
            )

            # 관련성 평가: 질문이 JD/후보자에 관련 있는지
            relevance_result = await self.evaluate_relevance(
                question=f"Is this interview question relevant? {question_text}",
                answer=why_matters,
            )

            results.append({
                "question_id": q.get("id"),
                "hallucination": hallucination_result,
                "relevance": relevance_result,
            })

        return results

    # ========================================
    # 데이터셋 관리 - 실험용 데이터 저장
    # ========================================

    async def create_dataset(
        self,
        name: str,
        examples: list[dict[str, Any]],
    ) -> str | None:
        """평가용 데이터셋 생성

        Args:
            name: 데이터셋 이름
            examples: [{"input": str, "expected_output": str, "metadata": dict}]

        Returns:
            dataset_id or None
        """
        if not self.client:
            return None

        try:
            dataset = self.client.upload_dataset(
                dataset_name=name,
                inputs=[ex.get("input", "") for ex in examples],
                outputs=[ex.get("expected_output", "") for ex in examples],
                metadata=[ex.get("metadata", {}) for ex in examples],
            )
            logger.info(f"Phoenix dataset created: {name}")
            return str(dataset.id)
        except Exception as e:
            logger.error(f"Dataset creation failed: {e}")
            return None


# 싱글톤 인스턴스
phoenix_eval_service = PhoenixEvalService()
