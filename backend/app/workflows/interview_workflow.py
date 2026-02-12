"""
backend/app/workflows/interview_workflow.py
메인 워크플로우: InterviewGenerationWorkflow

코드 분석 병렬 오케스트레이션은 workflow_code_analysis.py로 분리됨.
상수(Retry 정책, 버전, 가중치)는 workflow_constants.py로 분리됨.
"""
import asyncio
import logging
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.models.enums import JobStatus
    from app.workflows.activities.input_enrichment import enrich_input
    from app.workflows.activities.planning import create_execution_plan
    from app.workflows.activities.document_analysis import analyze_documents
    from app.workflows.activities.jd_analysis import analyze_jd
    from app.workflows.activities.question_generation import (
        select_topics, craft_question,
        enhance_terminology, craft_evaluation_scenarios,
        design_follow_ups, generate_interviewer_notes,
        generate_decision_guide, revise_questions,
    )
    from app.workflows.activities.quality_review import review_questions
    from app.workflows.activities.finalization import finalize_output
    from app.workflows.activities.persist_result import persist_result
    from app.workflows.activities.send_webhook import send_webhook
    from app.workflows.activities.observability_activities import (
        start_job_trace,
        end_job_trace,
    )
    from app.workflows.activities.intel_generation import generate_intel_brief
    from app.workflows.activities.analysis_generation import generate_deep_analysis
    from app.workflows.activities.decision_generation import generate_decision_support
    from app.workflows.activities.knowledge_graph_activities import build_knowledge_graph
    from app.workflows.activities.profile_builder import build_candidate_profile
    from app.workflows.workflow_code_analysis import run_parallel_code_analysis

# ── 분리된 모듈 re-export (backwards compatibility) ──
from app.workflows.workflow_constants import (  # noqa: F401, E402
    WORKFLOW_VERSION,
    DEFAULT_RETRY,
    LLM_RETRY,
    EXTERNAL_API_RETRY,
    CATEGORY_WEIGHTS_BY_LEVEL,
)

logger = logging.getLogger(__name__)


@workflow.defn
class InterviewGenerationWorkflow:
    """면접 스크립트 생성 워크플로우 (4-Phase Pipeline)"""

    def __init__(self):
        self._status = JobStatus.PENDING.value
        self._progress = 0
        self._current_phase = "pending"

    @workflow.run
    async def run(self, input_data: dict) -> dict:
        """메인 실행"""
        logger.info(f"Starting interview generation workflow v{WORKFLOW_VERSION}")

        job_id = input_data.get("job_id")
        user_id = input_data.get("user_id")
        trace_id = None

        # Start Langfuse trace for this job
        if job_id:
            trace_result = await workflow.execute_activity(
                start_job_trace,
                args=[job_id, user_id, {"workflow_version": WORKFLOW_VERSION}],
                start_to_close_timeout=timedelta(seconds=30),
            )
            trace_id = trace_result.get("trace_id")

        try:
            # Version gate: 향후 워크플로우 로직 변경 시 patched()로 분기
            use_enhanced_pipeline = workflow.patched("enhanced-pipeline-v1")

            # Phase 0: Input Enrichment
            self._update_status(JobStatus.ENRICHING, "Phase 0: Input Enrichment", 5)
            enriched = await workflow.execute_activity(
                enrich_input,
                input_data,
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=EXTERNAL_API_RETRY,
            )

            # Phase 1: Planning
            self._update_status(JobStatus.PLANNING, "Phase 1: Planning", 15)
            execution_plan = await workflow.execute_activity(
                create_execution_plan,
                enriched,
                start_to_close_timeout=timedelta(minutes=3),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=LLM_RETRY,
            )

            # Phase 2: Parallel Analysis
            self._update_status(JobStatus.ANALYZING, "Phase 2: Analysis", 25)
            raw_input = enriched.get("raw_input", {})
            output_language = raw_input.get("language_config", {}).get("output_language", "ko")
            phases = {p["name"]: p["enabled"] for p in execution_plan.get("phases", [])}

            analysis_tasks = []

            # JD Analysis (항상 실행)
            analysis_tasks.append(
                workflow.execute_activity(
                    analyze_jd,
                    args=[raw_input.get("jd_text", ""), job_id, output_language],
                    start_to_close_timeout=timedelta(minutes=5),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=LLM_RETRY,
                )
            )

            # Document Analysis (조건부)
            if phases.get("document_analysis"):
                analysis_tasks.append(
                    workflow.execute_activity(
                        analyze_documents,
                        raw_input,
                        start_to_close_timeout=timedelta(minutes=5),
                        heartbeat_timeout=timedelta(seconds=60),
                        retry_policy=DEFAULT_RETRY,
                    )
                )

            # Code Analysis (조건부) - HYBRID 병렬 처리
            # JD/Doc 분석과 코드 분석을 동시에 실행하여 총 소요시간 단축
            code_analysis_coro = None
            if phases.get("code_analysis"):
                code_analysis_coro = run_parallel_code_analysis(
                    enriched=enriched,
                    raw_input=raw_input,
                    execution_plan=execution_plan,
                    job_id=job_id,
                )

            # 모든 분석을 병렬 실행 (JD + Doc + Code)
            if code_analysis_coro:
                all_results = await asyncio.gather(*analysis_tasks, code_analysis_coro)
                analysis_results = list(all_results[:-1])
                code_analysis_result = all_results[-1]
            else:
                analysis_results = await asyncio.gather(*analysis_tasks)
                code_analysis_result = None

            # Aggregate results
            analysis = {"jd_analysis": analysis_results[0]}
            idx = 1
            if phases.get("document_analysis"):
                analysis["document_analysis"] = analysis_results[idx]
                idx += 1
            if phases.get("code_analysis") and code_analysis_result:
                analysis["code_analysis"] = code_analysis_result

            # Phase 2.5: Knowledge Graph 구축 (non-blocking)
            # 분석 데이터를 기반으로 KG를 구축하여 질문 생성에 활용
            linkedin_profile = enriched.get("linkedin_profile", {})
            try:
                await workflow.execute_activity(
                    build_knowledge_graph,
                    args=[
                        job_id,
                        linkedin_profile,
                        analysis.get("code_analysis"),
                        analysis.get("jd_analysis", {}),
                    ],
                    start_to_close_timeout=timedelta(minutes=3),
                    heartbeat_timeout=timedelta(seconds=60),
                    retry_policy=DEFAULT_RETRY,
                )
                logger.info("Knowledge Graph built successfully")
            except Exception as kg_err:
                logger.warning(f"KG build failed (non-fatal): {kg_err}")

            # Phase 2.5b: Profile Building (non-blocking, unified candidate profile)
            candidate_profile = None
            if workflow.patched("unified-profile-v1"):
                try:
                    candidate_profile = await workflow.execute_activity(
                        build_candidate_profile,
                        args=[enriched, analysis.get("document_analysis", {}), analysis.get("code_analysis")],
                        start_to_close_timeout=timedelta(minutes=3),
                        heartbeat_timeout=timedelta(seconds=60),
                        retry_policy=DEFAULT_RETRY,
                    )
                    logger.info(f"Unified profile built: {candidate_profile.get('name', 'unknown')}")
                except Exception as pb_err:
                    logger.warning(f"Profile builder failed (non-fatal): {pb_err}")

            # Phase 3: Question Generation
            self._update_status(JobStatus.GENERATING, "Phase 3: Generation", 60)

            # 3a. 토픽 선정
            topics = await workflow.execute_activity(
                select_topics,
                args=[analysis, enriched, job_id],  # job_id 추가 (KG 기반 질문 후보 조회용)
                start_to_close_timeout=timedelta(minutes=10),  # Kimi K2 실측 200s + 마진
                heartbeat_timeout=timedelta(seconds=120),  # heartbeat 미수신 시 dead activity 감지
                retry_policy=LLM_RETRY,
            )

            # 3b. 개별 질문 생성 (병렬)
            question_tasks = []
            for topic in topics:
                question_tasks.append(
                    workflow.execute_activity(
                        craft_question,
                        args=[topic, analysis, enriched, job_id],  # job_id 추가 (KG evidence 조회용)
                        start_to_close_timeout=timedelta(minutes=5),  # Kimi K2 실측 86-122s + 마진
                        heartbeat_timeout=timedelta(seconds=120),
                        retry_policy=LLM_RETRY,
                    )
                )
            questions = await asyncio.gather(*question_tasks)
            questions = list(questions)

            # evidence_source 분포 로깅 — 범용 질문 비율 모니터링
            source_dist: dict[str, int] = {}
            for q in questions:
                src = q.get("evidence_source", "Unknown") if isinstance(q, dict) else "Unknown"
                source_dist[src] = source_dist.get(src, 0) + 1
            total_q = len(questions)
            general_ratio = round(source_dist.get("General", 0) / total_q * 100, 1) if total_q > 0 else 0
            logger.info(f"Question evidence_source distribution: {source_dist} (General: {general_ratio}%)")
            if general_ratio > 20:
                logger.warning(f"Generic question ratio {general_ratio}% exceeds 20% target")

            # Phase 3c-3g: Enhancement Agents (병렬)
            self._update_status(JobStatus.GENERATING, "Phase 3: Enhancement", 70)

            enhancement_tasks = [
                # 3c. Terminology Agent
                workflow.execute_activity(
                    enhance_terminology,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=7),  # 20개 질문 일괄 처리, Kimi K2 대비
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=LLM_RETRY,
                ),
                # 3d. Scenario Writer Agent
                workflow.execute_activity(
                    craft_evaluation_scenarios,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=7),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=LLM_RETRY,
                ),
                # 3e. Follow-up Designer Agent
                workflow.execute_activity(
                    design_follow_ups,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=7),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=LLM_RETRY,
                ),
            ]

            guide_tasks = [
                # 3f. Interviewer Note Agent
                workflow.execute_activity(
                    generate_interviewer_notes,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=7),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=LLM_RETRY,
                ),
                # 3g. Decision Guide Agent
                workflow.execute_activity(
                    generate_decision_guide,
                    args=[analysis, enriched],
                    start_to_close_timeout=timedelta(minutes=5),  # 실측 40s, 마진 충분
                    retry_policy=LLM_RETRY,
                ),
            ]

            # Run all enhancement agents in parallel
            all_enhancements = await asyncio.gather(
                *enhancement_tasks, *guide_tasks
            )
            terminology = all_enhancements[0]
            scenarios = all_enhancements[1]
            follow_ups = all_enhancements[2]
            interviewer_notes = all_enhancements[3]
            decision_guide = all_enhancements[4]

            # Merge enhancements into questions
            # Enhancement Activity들은 question의 id/topic을 키로 사용하여 dict를 반환
            for q in questions:
                # 여러 가능한 키 후보를 시도: id (UUID), question_id, topic
                q_keys = [
                    q.get("id", ""),
                    q.get("question_id", ""),
                    q.get("topic", ""),
                ]
                for enhancement, field_name in [
                    (terminology, "terminology"),
                    (scenarios, "evaluation_scenarios"),
                    (follow_ups, "follow_up_questions"),
                    (interviewer_notes, "interviewer_note"),
                ]:
                    if not isinstance(enhancement, dict):
                        continue
                    for q_key in q_keys:
                        if q_key and q_key in enhancement:
                            # interviewer_note는 deep-merge (craft_question의 level_expectation 보존)
                            if field_name == "interviewer_note" and isinstance(q.get(field_name), dict):
                                q[field_name] = {**q[field_name], **enhancement[q_key]}
                            else:
                                q[field_name] = enhancement[q_key]
                            break

            # Phase 4: Quality Review + Finalization
            self._update_status(JobStatus.REVIEWING, "Phase 4: Review", 85)

            # 4a. 품질 검토
            review = await workflow.execute_activity(
                review_questions,
                args=[questions, output_language],
                start_to_close_timeout=timedelta(minutes=7),  # 20개 질문 일괄 검토, Kimi K2 대비
                heartbeat_timeout=timedelta(seconds=120),
                retry_policy=LLM_RETRY,
            )

            # 4a-1. Revision loop (최대 1회, flagged 질문만 revise)
            revision_count = 0
            max_revisions = 1
            while (
                isinstance(review, dict)
                and review.get("verdict") == "NEEDS_REVISION"
                and revision_count < max_revisions
            ):
                revision_count += 1
                self._update_status(
                    JobStatus.REVIEWING,
                    f"Phase 4: Revision {revision_count}/{max_revisions}",
                    85 + revision_count,
                )

                # C: flagged 질문만 추출하여 revise에 전달 (토큰 절감)
                flagged_indices: set[int] = set()
                for qr in review.get("questions_to_revise", []):
                    if isinstance(qr, dict):
                        idx = qr.get("question_index")
                        if isinstance(idx, int) and 0 <= idx < len(questions):
                            flagged_indices.add(idx)
                # hallucination_risk 질문도 포함
                for issue in review.get("issues", []):
                    if isinstance(issue, dict) and issue.get("type") == "hallucination_risk":
                        details = issue.get("details", {})
                        if isinstance(details, dict):
                            idx = details.get("question_index")
                            if isinstance(idx, int) and 0 <= idx < len(questions):
                                flagged_indices.add(idx)

                # flagged 질문이 없으면 revision 불필요 — 루프 종료
                if not flagged_indices:
                    break

                # flagged 질문만 추출 (원본 인덱스를 _original_idx로 보존)
                flagged_questions = []
                for idx in sorted(flagged_indices):
                    q = questions[idx]
                    if isinstance(q, dict):
                        q_copy = {**q, "_original_idx": idx}
                        flagged_questions.append(q_copy)

                questions = await workflow.execute_activity(
                    revise_questions,
                    args=[questions, flagged_questions, review, enriched],
                    start_to_close_timeout=timedelta(minutes=7),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=LLM_RETRY,
                )
                review = await workflow.execute_activity(
                    review_questions,
                    args=[questions, output_language],
                    start_to_close_timeout=timedelta(minutes=7),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=LLM_RETRY,
                )

            # 4a-2. Merge evidence quality data from review into questions
            if isinstance(review, dict):
                for qr in review.get("question_reviews", []):
                    if not isinstance(qr, dict):
                        continue
                    q_idx = qr.get("question_index")
                    if q_idx is not None and isinstance(q_idx, int) and 0 <= q_idx < len(questions):
                        q = questions[q_idx]
                        if isinstance(q, dict):
                            if qr.get("evidence_score") is not None:
                                q["evidence_score"] = qr["evidence_score"]
                            if qr.get("hallucination_risk"):
                                q["evidence_quality"] = (
                                    "high" if qr["hallucination_risk"] == "low"
                                    else "low" if qr["hallucination_risk"] == "high"
                                    else "medium"
                                )

            # 4b. 최종화
            self._update_status(JobStatus.REVIEWING, "Phase 4: Finalization", 90)
            final_script = await workflow.execute_activity(
                finalize_output,
                args=[questions, analysis, enriched],
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=LLM_RETRY,
            )
            # Attach decision guide + quality review metadata to final output
            if isinstance(final_script, dict) and decision_guide:
                final_script["decision_guide"] = decision_guide
            if isinstance(final_script, dict):
                meta = final_script.get("metadata", {})
                if isinstance(meta, dict):
                    quality = meta.get("quality", {})
                    if isinstance(quality, dict):
                        quality["review_verdict"] = review.get("verdict") if isinstance(review, dict) else None
                        quality["revision_count"] = revision_count

            # Phase 4c: Generate v2 Intel and Analysis (병렬)
            self._update_status(JobStatus.REVIEWING, "Phase 4: Intel/Analysis", 92)

            # Prepare inputs for intel/analysis generation
            jd_analysis_data = analysis.get("jd_analysis", {})
            jd_text_raw = raw_input.get("jd_text", "")
            jd_text = jd_analysis_data.get("translated_jd_text") or jd_text_raw
            document_analysis = analysis.get("document_analysis", {})
            code_analysis_data = analysis.get("code_analysis")
            linkedin_profile = enriched.get("linkedin_profile")

            # Get candidate_summary for decision support
            candidate_summary_data = final_script.get("candidate_summary", {})

            intel_analysis_tasks = [
                workflow.execute_activity(
                    generate_intel_brief,
                    args=[
                        jd_analysis_data,
                        document_analysis,
                        code_analysis_data,
                        linkedin_profile,
                        jd_text,
                        job_id,
                        output_language,
                        candidate_profile,
                    ],
                    start_to_close_timeout=timedelta(minutes=5),  # Kimi K2 대비 확장
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=DEFAULT_RETRY,
                ),
                workflow.execute_activity(
                    generate_deep_analysis,
                    args=[
                        jd_analysis_data,
                        code_analysis_data,
                        document_analysis,
                        job_id,
                        output_language,
                        input_data.get("experience_level", "미들"),
                        linkedin_profile,
                        candidate_profile,
                    ],
                    start_to_close_timeout=timedelta(minutes=5),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=DEFAULT_RETRY,
                ),
                workflow.execute_activity(
                    generate_decision_support,
                    args=[
                        candidate_summary_data,
                        questions,
                        jd_analysis_data,
                        document_analysis,
                        job_id,
                        output_language,
                        input_data.get("experience_level", "미들"),
                        candidate_profile,
                        code_analysis_data,
                    ],
                    start_to_close_timeout=timedelta(minutes=5),
                    heartbeat_timeout=timedelta(seconds=120),
                    retry_policy=DEFAULT_RETRY,
                ),
            ]

            intel_analysis_results = await asyncio.gather(*intel_analysis_tasks)
            intel_brief = intel_analysis_results[0]
            deep_analysis = intel_analysis_results[1]
            decision_support = intel_analysis_results[2]

            # JIT-11: jd_competency_map의 related_questions를 skill_table에 흡수
            if isinstance(deep_analysis, dict) and isinstance(decision_support, dict):
                skill_table = deep_analysis.get("skill_table", [])
                jd_comp_map = decision_support.get("jd_competency_map", [])
                if isinstance(skill_table, list) and isinstance(jd_comp_map, list):
                    # competency → related_questions 매핑 구축
                    comp_questions: dict[str, list[int]] = {}
                    for comp in jd_comp_map:
                        if isinstance(comp, dict):
                            name = comp.get("competency", "").lower().strip()
                            rqs = comp.get("related_questions", [])
                            if name and isinstance(rqs, list):
                                comp_questions[name] = [q for q in rqs if isinstance(q, int)]
                    # skill_table 각 행에 매핑
                    for row in skill_table:
                        if isinstance(row, dict) and not row.get("related_questions"):
                            skill_name = row.get("skill", "").lower().strip()
                            # 정확 매칭 → 부분 매칭 순서
                            matched = comp_questions.get(skill_name)
                            if not matched:
                                for comp_name, rqs in comp_questions.items():
                                    if skill_name in comp_name or comp_name in skill_name:
                                        matched = rqs
                                        break
                            if matched:
                                row["related_questions"] = matched

            # Attach v2 data to final script
            if isinstance(final_script, dict):
                final_script["intel"] = intel_brief
                final_script["analysis"] = deep_analysis
                final_script["decision"] = decision_support
                if candidate_profile:
                    final_script["candidate_profile"] = candidate_profile

                # 교차 일관성 검증 (Intel ↔ Deep Analysis ↔ Decision)
                inconsistencies = []
                intel_data = intel_brief if isinstance(intel_brief, dict) else {}
                analysis_data = deep_analysis if isinstance(deep_analysis, dict) else {}
                decision_data = decision_support if isinstance(decision_support, dict) else {}

                # 레이더 점수 ↔ Decision 추천 일관성
                radar = analysis_data.get("radar_candidate", {})
                if isinstance(radar, dict) and decision_data:
                    avg_radar = 0
                    radar_values = [v for v in radar.values() if isinstance(v, (int, float))]
                    if radar_values:
                        avg_radar = sum(radar_values) / len(radar_values)
                    summary = decision_data.get("summary", {})
                    if isinstance(summary, dict):
                        jd_match = summary.get("jd_match", "")
                        # 평균 레이더 ≤ 30인데 jd_match에 "높" or "strong" → 불일치
                        if avg_radar > 0 and avg_radar <= 30 and any(w in str(jd_match).lower() for w in ["높", "strong", "excellent"]):
                            inconsistencies.append(f"radar_avg={avg_radar:.0f} but jd_match='{jd_match}'")
                        # 평균 레이더 ≥ 80인데 jd_match에 "낮" or "weak" → 불일치
                        if avg_radar >= 80 and any(w in str(jd_match).lower() for w in ["낮", "weak", "poor"]):
                            inconsistencies.append(f"radar_avg={avg_radar:.0f} but jd_match='{jd_match}'")

                # Intel 스킬 매칭 수 ↔ Deep Analysis 스킬 테이블 수 비교
                intel_skills = intel_data.get("competency_match", [])
                analysis_skills = analysis_data.get("skill_table", [])
                if isinstance(intel_skills, list) and isinstance(analysis_skills, list):
                    if len(intel_skills) > 0 and len(analysis_skills) > 0:
                        ratio = min(len(intel_skills), len(analysis_skills)) / max(len(intel_skills), len(analysis_skills))
                        if ratio < 0.3:
                            inconsistencies.append(
                                f"intel competency_match({len(intel_skills)}) vs analysis skill_table({len(analysis_skills)}) ratio={ratio:.2f}"
                            )

                if inconsistencies:
                    logger.warning(f"Cross-tab inconsistencies detected: {inconsistencies}")
                    meta = final_script.get("metadata", {})
                    if isinstance(meta, dict):
                        meta["cross_tab_inconsistencies"] = inconsistencies

            # DB에 결과 저장
            job_id = input_data.get("job_id")
            if job_id:
                self._update_status(JobStatus.REVIEWING, "Persisting result", 95)
                await workflow.execute_activity(
                    persist_result,
                    args=[job_id, final_script],
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=DEFAULT_RETRY,
                )

            # Webhook callback (fire-and-forget, 실패해도 워크플로우 성공)
            callback_url = input_data.get("callback_url")
            if callback_url and job_id:
                try:
                    await workflow.execute_activity(
                        send_webhook,
                        args=[job_id, callback_url, "completed", final_script],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception as we:
                    logger.warning(f"Webhook delivery failed (non-fatal): {we}")

            self._update_status(JobStatus.COMPLETED, "completed", 100)

            # End Langfuse trace with success
            if job_id and trace_id:
                await workflow.execute_activity(
                    end_job_trace,
                    args=[job_id, trace_id, "success", None],
                    start_to_close_timeout=timedelta(seconds=30),
                )

            return {"status": "completed", "script": final_script}

        except Exception as e:
            self._status = JobStatus.FAILED.value
            self._current_phase = "failed"
            logger.error(f"Workflow failed: {e}")

            # End Langfuse trace with failure
            if job_id and trace_id:
                try:
                    await workflow.execute_activity(
                        end_job_trace,
                        args=[job_id, trace_id, "failed", None],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception:
                    logger.warning("Failed to end Langfuse trace")

            # DB에 실패 상태 저장
            if job_id:
                try:
                    await workflow.execute_activity(
                        persist_result,
                        args=[job_id, {"error": str(e)}],
                        start_to_close_timeout=timedelta(minutes=1),
                    )
                except Exception:
                    logger.error("Failed to persist error status to DB")

            # Webhook callback for failure
            callback_url = input_data.get("callback_url")
            if callback_url and job_id:
                try:
                    await workflow.execute_activity(
                        send_webhook,
                        args=[job_id, callback_url, "failed", {"error": str(e)}],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception:
                    logger.warning("Webhook delivery for failure failed (non-fatal)")
            raise

    @workflow.query
    def get_status(self) -> str:
        return self._status

    @workflow.query
    def get_progress(self) -> dict:
        return {
            "status": self._status,
            "phase": self._current_phase,
            "progress": self._progress,
        }

    def _update_status(self, status: JobStatus, phase: str, progress: int):
        self._status = status.value
        self._current_phase = phase
        self._progress = progress
        logger.info(f"Phase: {phase} ({progress}%)")

