"""
backend/app/workflows/activities/question_enhancement.py
질문 Enhancement Activities — 용어설명, 평가시나리오, 꼬리질문, 면접관노트, 의사결정가이드, 수정

Extracted from question_generation.py for SRP compliance.
"""
import asyncio
import json
import logging
from typing import Any

from temporalio import activity

from app.core.observability import observe_activity
from app.workflows.utils import run_llm_with_prompt_config_heartbeat

logger = logging.getLogger(__name__)

# 병렬 처리 상수
ENHANCEMENT_MAX_CONCURRENCY = 10  # 동시 LLM 호출 제한 (API rate limit 방지)


async def _run_batched_enhancement(
    questions: list[dict],
    prompt_file: str,
    prompt_name: str,
    activity_name: str,
    extra_vars: dict[str, Any] | None = None,
) -> dict:
    """Enhancement Activity 질문별 병렬 LLM 호출

    질문 1개당 1회 LLM 호출 → asyncio.gather로 전체 병렬 실행
    → 결과 dict 병합. Heartbeat는 별도 태스크로 관리.
    동시성 세마포어로 API rate limit 방지.

    기존: 1 LLM 호출 × 20 질문 (프롬프트 거대, 3분+)
    변경: 20 LLM 호출 × 1 질문 (프롬프트 소형, ~20-30s) 병렬 → wall time ~30s
    """
    from app.services.cached_llm import CachedLLMService, validate_llm_output
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    semaphore = asyncio.Semaphore(ENHANCEMENT_MAX_CONCURRENCY)

    logger.info(f"{activity_name}: {len(questions)} questions → {len(questions)} parallel LLM calls (concurrency={ENHANCEMENT_MAX_CONCURRENCY})")

    async def process_single(question: dict, idx: int) -> dict:
        """질문 1개에 대한 LLM 호출 (세마포어로 동시성 제한, JIT-70: 실패 시 1회 재시도)"""
        async with semaphore:
            vars_ = {**(extra_vars or {})}
            vars_["questions_json"] = json.dumps([question], ensure_ascii=False, default=str)
            prompt_config = get_prompt_with_config(prompt_file, prompt_name, **vars_)
            result = await llm.run_with_prompt_config(prompt_config)
            validated = validate_llm_output(result, activity_name=f"{activity_name}_q{idx}")
            if isinstance(validated, dict) and validated:
                return validated

            # JIT-70: JSON 파싱 실패 시 1회 재시도
            logger.warning(f"{activity_name}_q{idx}: empty result, retrying once")
            prompt_config = get_prompt_with_config(prompt_file, prompt_name, **vars_)
            result = await llm.run_with_prompt_config(prompt_config)
            validated = validate_llm_output(result, activity_name=f"{activity_name}_q{idx}_retry")
            return validated if isinstance(validated, dict) else {}

    # Heartbeat 태스크 — 병렬 LLM 호출 중 Temporal에 alive 신호 전송
    completed = [0]

    async def heartbeat_loop():
        count = 0
        try:
            while True:
                await asyncio.sleep(30)
                count += 1
                activity.heartbeat(
                    f"{activity_name}: {completed[0]}/{len(questions)} done (#{count})"
                )
        except asyncio.CancelledError:
            pass

    hb_task = asyncio.create_task(heartbeat_loop())
    try:
        async def process_and_track(question: dict, idx: int) -> dict:
            result = await process_single(question, idx)
            completed[0] += 1
            return result

        results = await asyncio.gather(
            *[process_and_track(q, i) for i, q in enumerate(questions)],
            return_exceptions=True,
        )
    finally:
        hb_task.cancel()

    # 결과 병합
    merged: dict = {}
    failed_count = 0
    for i, result in enumerate(results):
        if isinstance(result, dict):
            merged.update(result)
        elif isinstance(result, Exception):
            failed_count += 1
            logger.warning(f"{activity_name} question {i} failed: {result}")

    logger.info(f"{activity_name}: merged {len(merged)} results, {failed_count} failures")
    return merged


@activity.defn
@observe_activity(name="enhance_terminology", phase="question_generation")
async def enhance_terminology(questions: list[dict], enriched_input: dict) -> dict:
    """3c. Terminology Agent — 전문용어에 비개발자용 설명 추가 (배치 병렬)"""
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    validated = await _run_batched_enhancement(
        questions=questions[:25],
        prompt_file="question_enhancement.yaml",
        prompt_name="enhance_terminology",
        activity_name="enhance_terminology",
        extra_vars={"output_language": output_language},
    )

    # 용어 설명 커버리지 검증 — plain_explanation 누락 + 중복 + 자기참조 감지
    if isinstance(validated, dict):
        total_terms = 0
        missing_explanation = 0
        self_referential = 0
        all_term_names: list[str] = []
        for q_key, q_data in validated.items():
            terms = q_data if isinstance(q_data, list) else q_data.get("terminology", []) if isinstance(q_data, dict) else []
            for term in terms:
                if isinstance(term, dict):
                    total_terms += 1
                    term_name = str(term.get("term", "") or term.get("name", "")).strip().lower()
                    explanation = term.get("plain_language_explanation", "") or term.get("plain_explanation", "") or term.get("explanation", "")
                    explanation_str = str(explanation).strip()

                    if not explanation_str or len(explanation_str) < 3:
                        missing_explanation += 1
                    elif term_name and term_name in explanation_str.lower() and len(explanation_str) < len(term_name) * 3:
                        self_referential += 1

                    if term_name:
                        all_term_names.append(term_name)

        from collections import Counter as _TermCounter
        term_counts = _TermCounter(all_term_names)
        duplicates = {t: c for t, c in term_counts.items() if c > 1}

        if total_terms > 0:
            coverage = round((total_terms - missing_explanation) / total_terms * 100, 1)
            logger.info(f"enhance_terminology: {total_terms} terms, {coverage}% have explanations")
            if missing_explanation > 0:
                logger.warning(f"enhance_terminology: {missing_explanation}/{total_terms} terms missing plain_explanation")
            if self_referential > 0:
                logger.warning(f"enhance_terminology: {self_referential}/{total_terms} terms have self-referential explanations")
            if duplicates:
                logger.warning(f"enhance_terminology: duplicate terms across questions: {duplicates}")

    return validated


@activity.defn
@observe_activity(name="craft_evaluation_scenarios", phase="question_generation")
async def craft_evaluation_scenarios(questions: list[dict], enriched_input: dict) -> dict:
    """3d. Scenario Writer Agent — 3단계 평가 시나리오 생성 (배치 병렬)"""
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "Mid")

    validated = await _run_batched_enhancement(
        questions=questions[:25],
        prompt_file="question_enhancement.yaml",
        prompt_name="craft_evaluation_scenarios",
        activity_name="craft_evaluation_scenarios",
        extra_vars={"output_language": output_language, "experience_level": experience_level},
    )

    # 3단계 시나리오 구조 검증 — expert/mid_level/low_level 존재 확인
    EXPECTED_LEVELS = {"expert", "mid_level", "low_level"}
    if isinstance(validated, dict):
        total_questions = 0
        incomplete_questions = 0
        short_scenario_count = 0
        low_discriminability = 0
        for q_key, q_data in validated.items():
            if not isinstance(q_data, dict):
                continue
            total_questions += 1
            present_levels = set(q_data.keys()) & EXPECTED_LEVELS
            if present_levels != EXPECTED_LEVELS:
                incomplete_questions += 1
                missing = EXPECTED_LEVELS - present_levels
                logger.warning(f"craft_evaluation_scenarios: {q_key} missing levels: {missing}")

            texts = []
            for level in EXPECTED_LEVELS:
                level_data = q_data.get(level, {})
                text = ""
                if isinstance(level_data, dict):
                    text = level_data.get("text", "") or level_data.get("description", "")
                elif isinstance(level_data, str):
                    text = level_data
                texts.append(str(text).strip())
                if len(str(text).strip()) < 15:
                    short_scenario_count += 1

            if len(texts) >= 3 and texts[0] and texts[2]:
                expert_words = set(texts[0].lower().split())
                low_words = set(texts[2].lower().split())
                if expert_words and low_words:
                    overlap = len(expert_words & low_words) / max(len(expert_words), len(low_words))
                    if overlap > 0.8:
                        low_discriminability += 1

        if total_questions > 0:
            coverage = round((total_questions - incomplete_questions) / total_questions * 100, 1)
            logger.info(f"craft_evaluation_scenarios: {total_questions} questions, {coverage}% have all 3 levels")
            if short_scenario_count > 0:
                logger.warning(f"craft_evaluation_scenarios: {short_scenario_count} scenario texts are too short (<15 chars)")
            if low_discriminability > 0:
                logger.warning(f"craft_evaluation_scenarios: {low_discriminability}/{total_questions} questions have low expert/low discriminability (>80% word overlap)")

    return validated


@activity.defn
@observe_activity(name="design_follow_ups", phase="question_generation")
async def design_follow_ups(questions: list[dict], enriched_input: dict) -> dict:
    """3e. Follow-up Designer Agent — 후속질문 분기 설계 (질문별 병렬)"""
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "Mid")

    validated = await _run_batched_enhancement(
        questions=questions[:25],
        prompt_file="question_enhancement.yaml",
        prompt_name="design_follow_ups",
        activity_name="design_follow_ups",
        extra_vars={"output_language": output_language, "experience_level": experience_level},
    )

    # 후속질문 트리거 커버리지 + 구조 검증
    EXPECTED_TRIGGERS = {"expert", "mid", "low"}
    if isinstance(validated, dict):
        total_questions = 0
        missing_trigger_coverage = 0
        empty_text_count = 0
        for q_key, follow_ups in validated.items():
            if not isinstance(follow_ups, list):
                continue
            total_questions += 1
            triggers_present = {fu.get("trigger", "").lower() for fu in follow_ups if isinstance(fu, dict)}
            if not triggers_present & EXPECTED_TRIGGERS:
                missing_trigger_coverage += 1
            for fu in follow_ups:
                if isinstance(fu, dict) and not fu.get("question_text", "").strip():
                    empty_text_count += 1
        if total_questions > 0:
            coverage = round((total_questions - missing_trigger_coverage) / total_questions * 100, 1)
            logger.info(f"design_follow_ups: {total_questions} questions, {coverage}% have trigger-based follow-ups")
            if empty_text_count > 0:
                logger.warning(f"design_follow_ups: {empty_text_count} follow-ups have empty question_text")

    return validated


@activity.defn
@observe_activity(name="generate_interviewer_notes", phase="question_generation")
async def generate_interviewer_notes(questions: list[dict], enriched_input: dict) -> dict:
    """3f. Interviewer Note Agent — 면접관 참고 노트 (질문별 병렬)"""
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    validated = await _run_batched_enhancement(
        questions=questions[:25],
        prompt_file="question_enhancement.yaml",
        prompt_name="generate_interviewer_notes",
        activity_name="generate_interviewer_notes",
        extra_vars={"output_language": output_language},
    )

    # 면접관 노트 핵심 필드 존재 검증
    REQUIRED_FIELDS = {"business_interpretation", "daily_analogy", "what_to_listen_for"}
    if isinstance(validated, dict):
        total_notes = 0
        incomplete_notes = 0
        for q_key, note_data in validated.items():
            if not isinstance(note_data, dict):
                continue
            total_notes += 1
            present = set(note_data.keys()) & REQUIRED_FIELDS
            if present != REQUIRED_FIELDS:
                incomplete_notes += 1
                missing = REQUIRED_FIELDS - present
                logger.warning(f"generate_interviewer_notes: {q_key} missing fields: {missing}")
        if total_notes > 0:
            coverage = round((total_notes - incomplete_notes) / total_notes * 100, 1)
            logger.info(f"generate_interviewer_notes: {total_notes} notes, {coverage}% have all required fields")

    return validated


@activity.defn
@observe_activity(name="generate_decision_guide", phase="question_generation")
async def generate_decision_guide(analysis: dict, enriched_input: dict) -> dict:
    """3g. Decision Guide Agent — 채용 의사결정 가이드"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "Mid")

    # Summarize analysis for the prompt
    analysis_summary = json.dumps({
        k: v.get("summary", str(v)[:500]) if isinstance(v, dict) else str(v)[:500]
        for k, v in analysis.items()
    }, ensure_ascii=False, default=str)

    categories = ["role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"]
    category_summary = json.dumps(categories, ensure_ascii=False)

    prompt_config = get_prompt_with_config(
        "question_enhancement.yaml", "generate_decision_guide",
        output_language=output_language,
        experience_level=experience_level,
        analysis_summary=analysis_summary,
        category_summary=category_summary,
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
    from app.services.cached_llm import validate_llm_output
    validated = validate_llm_output(result, activity_name="generate_decision_guide")

    # 의사결정 가이드 구조 검증
    REQUIRED_TOP_KEYS = {"scoring_weights", "decision_thresholds", "category_insights"}
    if isinstance(validated, dict):
        present = set(validated.keys()) & REQUIRED_TOP_KEYS
        if present != REQUIRED_TOP_KEYS:
            missing = REQUIRED_TOP_KEYS - present
            logger.warning(f"generate_decision_guide: missing top-level keys: {missing}")
        else:
            logger.info("generate_decision_guide: all required top-level keys present")

        # risk_assessment에 identified_risks가 있으면 근거 없는 빈 리스크 경고
        risk_assessment = validated.get("risk_assessment", {})
        if isinstance(risk_assessment, dict):
            risks = risk_assessment.get("identified_risks", [])
            if isinstance(risks, list):
                empty_risks = [r for r in risks if isinstance(r, str) and len(r.strip()) < 5]
                if empty_risks:
                    logger.warning(f"generate_decision_guide: {len(empty_risks)} risks with insufficient description")

    return validated


@activity.defn
@observe_activity(name="revise_questions", phase="question_generation")
async def revise_questions(
    all_questions: list[dict],
    flagged_questions: list[dict],
    review_feedback: dict,
    enriched_input: dict,
) -> list[dict]:
    """3h. Quality Review revision — flagged 질문만 LLM에 전달하여 토큰 절감

    Args:
        all_questions: 전체 질문 목록 (수정 결과를 병합할 원본)
        flagged_questions: review에서 문제 있다고 판정된 질문만 (_original_idx 포함)
        review_feedback: review_questions의 피드백
        enriched_input: 워크플로우 enriched input
    """
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    logger.info(f"revise_questions: {len(flagged_questions)}/{len(all_questions)} flagged questions to revise")

    # flagged 질문만 LLM에 전달 (토큰 ~84K → ~5-20K)
    prompt_config = get_prompt_with_config(
        "question_enhancement.yaml", "revise_questions",
        output_language=output_language,
        questions_json=json.dumps(flagged_questions, ensure_ascii=False, default=str),
        review_feedback=json.dumps(review_feedback, ensure_ascii=False, default=str),
    )
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

    # original_index→_original_idx 매핑 테이블 생성
    # LLM이 반환하는 original_index는 flagged_questions 배열 내의 인덱스
    # _original_idx는 all_questions 내의 실제 인덱스
    idx_map: dict[int, int] = {}
    for i, fq in enumerate(flagged_questions):
        if isinstance(fq, dict):
            orig_idx = fq.get("_original_idx")
            if isinstance(orig_idx, int):
                idx_map[i] = orig_idx

    if isinstance(result, list):
        applied = 0
        for revision in result:
            if not isinstance(revision, dict):
                continue
            flagged_idx = revision.get("original_index")
            if flagged_idx is None or not isinstance(flagged_idx, int):
                logger.warning(f"revise_questions: missing original_index, skipping")
                continue

            # flagged 배열 인덱스 → 전체 배열 인덱스로 변환
            real_idx = idx_map.get(flagged_idx)
            if real_idx is None or real_idx < 0 or real_idx >= len(all_questions):
                logger.warning(f"revise_questions: flagged_idx={flagged_idx} → real_idx={real_idx}, skipping")
                continue

            original = all_questions[real_idx]
            if not isinstance(original, dict):
                continue

            revised_text = revision.get("revised_question")
            if revised_text:
                original["question_text"] = revised_text
                applied += 1

            for field in ("revision_type", "revision_rationale", "new_evidence_reference"):
                if revision.get(field):
                    original[field] = revision[field]
            if revision.get("new_confidence_score") is not None:
                original["confidence_score"] = revision["new_confidence_score"]

        logger.info(f"revise_questions: applied {applied}/{len(result)} revisions to {len(all_questions)} questions (flagged: {len(flagged_questions)})")
        return all_questions
    else:
        logger.warning("revise_questions: LLM did not return a list, returning original questions")
        return all_questions
