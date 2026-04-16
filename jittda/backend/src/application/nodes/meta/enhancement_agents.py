"""
Enhancement Agents 노드 — 면접 질문 보강 (Phase 3.5).

QuestionOrchestrator가 생성한 질문을 5개 Agent가 병렬로 보강한다:
1. TerminologyAgent: 전문 용어 → 비개발자 언어 풀이
2. AnswerGuideAgent: 예상 답변 가이드 보강
3. FollowUpAgent: follow_up_triggers 기반 후속 질문 생성
4. RedFlagAgent: 주의해야 할 답변 패턴 식별
5. CodeReferenceAgent: 관련 코드 위치(파일:라인) 매핑
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from pydantic import BaseModel

from application.states.meta_state import MetaState
from infrastructure.llm.instructor_client import InstructorClient
from infrastructure.persistence.repository import AnalysisRepository

logger = logging.getLogger(__name__)


# ─── Enhancement 결과 모델 ──────────────────────────────────────────

class TerminologyEnhancement(BaseModel):
    """전문 용어 풀이 결과."""
    question_id: str
    terms: list[dict[str, str]]  # [{"term": "...", "explanation": "..."}]


class AnswerGuideEnhancement(BaseModel):
    """답변 가이드 보강 결과."""
    question_id: str
    enhanced_guide: str
    key_points: list[str]


class FollowUpEnhancement(BaseModel):
    """후속 질문 생성 결과."""
    question_id: str
    follow_ups: list[str]


class RedFlagEnhancement(BaseModel):
    """위험 답변 패턴 식별 결과."""
    question_id: str
    red_flags: list[str]
    warning_signs: list[str]


class CodeRefEnhancement(BaseModel):
    """코드 레퍼런스 매핑 결과."""
    question_id: str
    code_reference: str  # "file_path:line_number"
    context_snippet: str


class EnhancementBatch(BaseModel):
    """배치 결과 래퍼."""
    items: list[dict[str, Any]]


# ─── 프롬프트 ──────────────────────────────────────────────────────

TERMINOLOGY_PROMPT = """\
You are a technical terminology translator for non-technical interviewers.
For each interview question, identify technical terms and provide simple explanations
that a non-developer HR professional can understand.

Return a list of term-explanation pairs for EACH question.
Keep explanations under 2 sentences, using everyday analogies where possible."""

ANSWER_GUIDE_PROMPT = """\
You are an interview answer assessment guide writer.
For each interview question, write an enhanced answer guide that helps
a non-technical interviewer evaluate the candidate's response.

Include:
- What a GOOD answer looks like (key points to listen for)
- What a POOR answer looks like (warning signs)
- Keep language simple and accessible for non-developers."""

FOLLOW_UP_PROMPT = """\
You are a senior technical interviewer.
For each interview question, generate 2-3 follow-up questions that dig deeper
into the candidate's understanding based on their initial response.

Follow-ups should:
- Probe for deeper understanding, not just repeat the original question
- Be triggered by common responses
- Help distinguish genuine knowledge from rehearsed answers."""

RED_FLAG_PROMPT = """\
You are an interview fraud detection specialist.
For each interview question, identify red flag answer patterns that suggest
the candidate may not have actually written the code they claim.

Red flags include:
- Vague, generic answers that don't reference specific implementation details
- Inability to explain trade-offs or alternative approaches
- Answers that only describe the final result, not the process
- Inconsistencies between claimed authorship and response depth."""

CODE_REF_PROMPT = """\
You are a code reference mapper.
Given interview questions and their code analysis context,
map each question to the most relevant code location (file:line or file:function).

Provide a brief context snippet (1-3 lines) showing the relevant code.
This helps the interviewer follow along during the interview."""


# ─── 개별 Agent 실행 ───────────────────────────────────────────────

async def _run_agent(
    agent_name: str,
    system_prompt: str,
    questions_summary: str,
    client: InstructorClient,
) -> list[dict[str, Any]]:
    """하나의 Enhancement Agent를 실행한다."""
    try:
        result = await client.create(
            response_model=EnhancementBatch,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": questions_summary},
            ],
            temperature=0.4,
        )
        return result.items
    except Exception as e:
        logger.error("Enhancement agent '%s' failed: %s", agent_name, e)
        return []


# ─── 메인 노드 ─────────────────────────────────────────────────────

async def enhancement_agents_node(state: MetaState) -> dict[str, Any]:
    """5개 Enhancement Agent를 병렬 실행하여 질문을 보강한다."""
    job_id = state["job_id"]

    try:
        analysis_repo = AnalysisRepository()

        # 1. 질문 로드
        questions_ref = state.get("questions_ref")
        if not questions_ref:
            logger.warning("enhancement_agents: no questions_ref in state")
            return {}

        questions_data = await analysis_repo.get_result(questions_ref)
        if not questions_data:
            logger.warning("enhancement_agents: questions not found in DB")
            return {}

        result_data = questions_data.get("result_data", {})
        questions = result_data.get("questions", [])

        if not questions:
            logger.warning("enhancement_agents: empty questions list")
            return {}

        # 2. 질문 요약 컨텍스트 구성
        questions_summary = f"Interview Questions ({len(questions)} total):\n\n"
        for i, q in enumerate(questions, 1):
            questions_summary += (
                f"Q{i} [id={q.get('question_id', '')}] "
                f"[strategy={q.get('strategy', '')}] "
                f"[category={q.get('category', '')}]\n"
                f"  Question: {q.get('question_text', '')}\n"
                f"  Intent: {q.get('intent', '')}\n"
                f"  Code ref: {q.get('code_reference', 'N/A')}\n"
                f"  Current answer guide: {q.get('expected_answer_guide', '')[:200]}\n\n"
            )

        # 3. LLM 클라이언트
        client = InstructorClient(
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
        )

        # 4. 5개 Agent 병렬 실행
        agent_tasks = [
            _run_agent("terminology", TERMINOLOGY_PROMPT, questions_summary, client),
            _run_agent("answer_guide", ANSWER_GUIDE_PROMPT, questions_summary, client),
            _run_agent("follow_up", FOLLOW_UP_PROMPT, questions_summary, client),
            _run_agent("red_flag", RED_FLAG_PROMPT, questions_summary, client),
            _run_agent("code_reference", CODE_REF_PROMPT, questions_summary, client),
        ]

        results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        agent_names = ["terminology", "answer_guide", "follow_up", "red_flag", "code_reference"]
        enhancements: dict[str, list[dict[str, Any]]] = {}

        for name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                logger.error("Enhancement agent '%s' raised: %s", name, result)
                enhancements[name] = []
            else:
                enhancements[name] = result

        # 5. 질문에 보강 결과 병합
        enhanced_questions = _merge_enhancements(questions, enhancements)

        # 6. 보강된 질문을 DB에 저장 (기존 questions_ref 업데이트가 아닌 새 레코드)
        enhanced_data = {
            **result_data,
            "questions": enhanced_questions,
            "enhancement_applied": True,
            "enhancement_agents": agent_names,
        }

        enhanced_ref = await analysis_repo.save_result(
            job_id,
            "enhancement_agents",
            "meta",
            enhanced_data,
        )

        logger.info(
            "enhancement_agents completed: %d questions enhanced with %d agents",
            len(enhanced_questions),
            sum(1 for r in results if not isinstance(r, Exception) and r),
        )

        # questions_ref를 보강된 버전으로 교체
        return {"questions_ref": enhanced_ref}
    except Exception as e:
        logger.error("enhancement_agents_node failed for job %s: %s", job_id, e)
        # 보강 실패 시 기존 questions_ref를 그대로 유지 (보강 없이 계속 진행)
        return {
            "errors": state.get("errors", []) + [f"enhancement_agents: {e}"],
        }


def _merge_enhancements(
    questions: list[dict[str, Any]],
    enhancements: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Enhancement 결과를 질문에 병합한다."""
    # question_id → enhancement 매핑 구성
    terminology_map: dict[str, list[dict]] = {}
    for item in enhancements.get("terminology", []):
        qid = item.get("question_id", "")
        if qid:
            terminology_map[qid] = item.get("terms", [])

    answer_guide_map: dict[str, dict] = {}
    for item in enhancements.get("answer_guide", []):
        qid = item.get("question_id", "")
        if qid:
            answer_guide_map[qid] = item

    follow_up_map: dict[str, list[str]] = {}
    for item in enhancements.get("follow_up", []):
        qid = item.get("question_id", "")
        if qid:
            follow_up_map[qid] = item.get("follow_ups", [])

    red_flag_map: dict[str, dict] = {}
    for item in enhancements.get("red_flag", []):
        qid = item.get("question_id", "")
        if qid:
            red_flag_map[qid] = item

    code_ref_map: dict[str, dict] = {}
    for item in enhancements.get("code_reference", []):
        qid = item.get("question_id", "")
        if qid:
            code_ref_map[qid] = item

    # 병합
    enhanced = []
    for q in questions:
        qid = q.get("question_id", "")
        eq = {**q}

        # Terminology 보강
        if qid in terminology_map:
            eq["terminology"] = terminology_map[qid]

        # Answer guide 보강
        if qid in answer_guide_map:
            guide = answer_guide_map[qid]
            eq["expected_answer_guide"] = guide.get("enhanced_guide", eq.get("expected_answer_guide", ""))

        # Follow-up 보강
        if qid in follow_up_map:
            existing = eq.get("follow_up_triggers", [])
            eq["follow_up_triggers"] = list(set(existing + follow_up_map[qid]))

        # Red flag 보강
        if qid in red_flag_map:
            rf = red_flag_map[qid]
            existing_flags = eq.get("red_flags", [])
            eq["red_flags"] = list(set(existing_flags + rf.get("red_flags", []) + rf.get("warning_signs", [])))

        # Code reference 보강
        if qid in code_ref_map:
            ref = code_ref_map[qid]
            if ref.get("code_reference"):
                eq["code_reference"] = ref["code_reference"]

        enhanced.append(eq)

    return enhanced
