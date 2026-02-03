# 03. Temporal Workflow Design

> 워크플로우 오케스트레이션 및 Activity 설계

---

## 1. Temporal 선택 이유

### 1.1 왜 Temporal인가?

| 특징 | Step Functions | LangGraph | Temporal |
|-----|---------------|-----------|----------|
| 로컬 개발 | ❌ AWS 필요 | ✅ 가능 | ✅ 가능 |
| 클라우드 전환 | - | 별도 구현 | ✅ 코드 동일 |
| 내장 재시도 | ✅ | ❌ 직접 구현 | ✅ |
| 상태 지속성 | ✅ | ❌ 직접 구현 | ✅ |
| 병렬 처리 | ✅ | ✅ | ✅ |
| 디버깅 UI | ❌ | ❌ | ✅ 내장 |
| 학습 곡선 | 중간 | 낮음 | 중간 |

### 1.2 핵심 장점
```
1. Write Once, Run Anywhere
   - 로컬: temporal server start-dev
   - 프로덕션: Temporal Cloud 또는 Self-hosted
   - 코드 변경 없음, 주소만 변경

2. Durable Execution
   - 서버가 죽어도 자동 복구
   - Activity 실패 시 자동 재시도
   - 상태가 영구 저장됨

3. Built-in Observability
   - Web UI에서 실시간 모니터링
   - 워크플로우 히스토리 추적
   - 실패 지점 정확히 파악
```

---

## 2. 워크플로우 전체 구조

### 2.1 Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    InterviewGenerationWorkflow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 0: SMART INPUT EXTRACTION                                  │   │
│  │ ┌───────────────────────────────────────────────────────────┐   │   │
│  │ │  enrich_input (Activity)                                  │   │   │
│  │ │  • PDF/DOCX 텍스트 추출 → URL 교차 발견                  │   │   │
│  │ │  • LinkedIn URL → Bright Data API → 프로필 수집             │   │   │
│  │ │  • GitHub username 자동 추론                              │   │   │
│  │ │  • 중복 제거 → EnrichedInput 생성                        │   │   │
│  │ └───────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 1: PLANNING                                                │   │
│  │ ┌───────────────────────────────────────────────────────────┐   │   │
│  │ │  create_execution_plan (Activity)                         │   │   │
│  │ │  • enriched_input 기반 유효성 검사                        │   │   │
│  │ │  • GitHub API로 워크로드 추정                             │   │   │
│  │ │  • 실행 계획 생성                                         │   │   │
│  │ └───────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 2: PARALLEL ANALYSIS (Fan-out)                            │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│  │  │  analyze    │  │  analyze    │  │  analyze    │             │   │
│  │  │  documents  │  │    code     │  │     jd      │             │   │
│  │  │  (Activity) │  │  (Activity) │  │  (Activity) │             │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │   │
│  │         │                │                │                     │   │
│  │         └────────────────┼────────────────┘                     │   │
│  │                          │                                       │   │
│  │                          ▼                                       │   │
│  │              ┌───────────────────────┐                          │   │
│  │              │ aggregate_analysis    │                          │   │
│  │              │ (Activity)            │                          │   │
│  │              └───────────────────────┘                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 3: QUESTION GENERATION (Multi-Agent)                      │   │
│  │                                                                  │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │ 3a. Topic Selector Agent - select_topics (Activity)       │  │   │
│  │  │     주제 선정 (25개 토픽, 5카테고리 × 5)                                  │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  │                          │                                       │   │
│  │                          ▼                                       │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │ 3b. Question Crafter Agent - craft_questions (Parallel)   │  │   │
│  │  │     질문 본체 생성 (25개 병렬)                             │  │   │
│  │  │ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ...                   │  │   │
│  │  │ │ Q1 │ │ Q2 │ │ Q3 │ │ Q4 │ │ Q5 │                       │  │   │
│  │  │ └────┘ └────┘ └────┘ └────┘ └────┘                       │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  │                          │                                       │   │
│  │                          ▼                                       │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │ Parallel Enhancement Agents (3c, 3d, 3e)                  │  │   │
│  │  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │  │   │
│  │  │ │3c.Terminology│ │3d.Scenario  │ │3e.Follow-up │          │  │   │
│  │  │ │Agent        │ │Writer Agent│ │Designer     │          │  │   │
│  │  │ │용어 설명     │ │채점 시나리오│ │꼬리질문     │          │  │   │
│  │  │ └─────────────┘ └─────────────┘ └─────────────┘          │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  │                          │                                       │   │
│  │                          ▼                                       │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │ Parallel Guide Agents (3f, 3g)                            │  │   │
│  │  │ ┌──────────────────┐ ┌──────────────────┐                 │  │   │
│  │  │ │3f.Interviewer Note│ │3g.Decision Guide │                 │  │   │
│  │  │ │Agent             │ │Agent            │                 │  │   │
│  │  │ │면접관 참고 노트   │ │이력서 기반 가이드│                 │  │   │
│  │  │ └──────────────────┘ └──────────────────┘                 │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  │                          │                                       │   │
│  │                          ▼                                       │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │ 3h. Quality Reviewer Agent - review_questions (Activity)  │  │   │
│  │  │     최종 검토 및 종합 (REVIEW LOOP max 3회)               │  │   │
│  │  │                                                            │  │   │
│  │  │  ┌──────────────────┐                                     │  │   │
│  │  │  │ review_quality   │◄────────────────────┐               │  │   │
│  │  │  │                  │                     │               │  │   │
│  │  │  └────────┬─────────┘                     │               │  │   │
│  │  │           │                               │               │  │   │
│  │  │           ▼                               │               │  │   │
│  │  │  ┌──────────────────┐    NEEDS      ┌────┴─────────┐     │  │   │
│  │  │  │ verdict ==       │────REVISION───│ revise       │     │  │   │
│  │  │  │ APPROVED?        │               │ _questions   │     │  │   │
│  │  │  └────────┬─────────┘               │              │     │  │   │
│  │  │           │ YES                     └──────────────┘     │  │   │
│  │  │           ▼                                               │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 4: FINALIZATION                                           │   │
│  │ ┌───────────────────────────────────────────────────────────┐   │   │
│  │ │ finalize_output (Activity)                                │   │   │
│  │ │ • Hallucination 검증                                      │   │   │
│  │ │ • 최종 스크립트 생성 (주 언어)                              │   │   │
│  │ │ • 다국어 번역: on-demand API (저장 X)                     │   │   │
│  │ │ • S3 저장                                                 │   │   │
│  │ └───────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│                          [InterviewScript]                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Workflow 구현

### 3.1 Main Workflow

```python
"""
backend/app/workflows/interview_workflow.py
메인 면접 스크립트 생성 워크플로우
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

# Activity 타입 힌트용 import
with workflow.unsafe.imports_passed_through():
    from app.workflows.activities import (
        input_enrichment,
        planning,
        document_analysis,
        code_analysis,
        jd_analysis,
        question_generation,
        quality_review,
        finalization,
    )
    from app.models.job import InputData, EnrichedInput, InterviewScript


@workflow.defn
class InterviewGenerationWorkflow:
    """
    면접 질문 생성 워크플로우

    이 워크플로우는 로컬(temporal server start-dev)과
    프로덕션(Temporal Cloud)에서 동일하게 실행됩니다.
    """

    def __init__(self) -> None:
        self._current_phase = "initialized"
        self._progress = 0

    @workflow.run
    async def run(self, job_id: str, input_data: dict) -> dict:
        """
        메인 실행 메서드

        Args:
            job_id: 작업 고유 ID
            input_data: InputData 모델의 dict 표현

        Returns:
            InterviewScript의 dict 표현
        """
        # 공통 재시도 정책
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
            non_retryable_error_types=["ValueError", "ValidationError"],
        )

        # 긴 작업용 타임아웃
        long_timeout = timedelta(minutes=10)
        short_timeout = timedelta(minutes=2)

        try:
            # ================================================
            # Phase 0: SMART INPUT EXTRACTION
            # ================================================
            self._current_phase = "enriching"
            self._progress = 2

            enriched_input = await workflow.execute_activity(
                input_enrichment.enrich_input,
                args=[job_id, input_data],
                start_to_close_timeout=short_timeout,
                retry_policy=retry_policy,
            )

            # ================================================
            # Phase 1: PLANNING (enriched_input 기반)
            # ================================================
            self._current_phase = "planning"
            self._progress = 5

            execution_plan = await workflow.execute_activity(
                planning.create_execution_plan,
                args=[job_id, enriched_input],
                start_to_close_timeout=short_timeout,
                retry_policy=retry_policy,
            )

            # ================================================
            # Phase 2: PARALLEL ANALYSIS
            # ================================================
            self._current_phase = "analyzing"
            self._progress = 10

            # 병렬 분석 태스크 구성
            raw = enriched_input.get("raw_input", enriched_input)
            has_docs = raw.get("resume_path") or raw.get("portfolio_path") or raw.get("cover_letter_path")
            has_linkedin = enriched_input.get("linkedin_profile")

            # 병렬 실행할 Activity 태스크만 수집
            analysis_tasks = []

            if has_docs or has_linkedin:
                analysis_tasks.append(
                    workflow.execute_activity(
                        document_analysis.analyze_documents,
                        args=[job_id, enriched_input],
                        start_to_close_timeout=long_timeout,
                        retry_policy=retry_policy,
                    )
                )

            if enriched_input.get("github_urls"):
                analysis_tasks.append(
                    workflow.execute_activity(
                        code_analysis.analyze_code,
                        args=[job_id, enriched_input["github_urls"], enriched_input, execution_plan],
                        start_to_close_timeout=long_timeout,
                        retry_policy=retry_policy,
                    )
                )

            # JD Analysis (필수)
            analysis_tasks.append(
                workflow.execute_activity(
                    jd_analysis.analyze_jd,
                    args=[job_id, raw["jd_text"]],
                    start_to_close_timeout=short_timeout,
                    retry_policy=retry_policy,
                )
            )

            # 병렬 실행
            results = await workflow.wait_all(analysis_tasks)
            self._progress = 40

            # 분석 결과 집계 (없는 분석은 빈 결과)
            result_idx = 0
            doc_result = None
            if has_docs or has_linkedin:
                doc_result = results[result_idx]
                result_idx += 1
            else:
                doc_result = self._create_empty_document_result()

            code_result = None
            if enriched_input.get("github_urls"):
                code_result = results[result_idx]
                result_idx += 1
            else:
                code_result = self._create_empty_code_result()

            jd_result = results[result_idx]

            aggregated = {
                "document_analysis": doc_result,
                "code_analysis": code_result,
                "jd_analysis": jd_result,
            }

            # ================================================
            # Phase 3: QUESTION GENERATION (Multi-Agent)
            # ================================================
            self._current_phase = "generating"
            self._progress = 45

            # 3a. Topic Selector Agent - 토픽 선정
            selected_topics = await workflow.execute_activity(
                question_generation.select_topics,
                args=[job_id, aggregated, enriched_input],
                start_to_close_timeout=short_timeout,
                retry_policy=retry_policy,
            )

            self._progress = 50

            # 3b. Question Crafter Agent - 질문 본체 생성 (25개 병렬)
            question_tasks = [
                workflow.execute_activity(
                    question_generation.craft_question,
                    args=[job_id, topic, aggregated, enriched_input],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=retry_policy,
                )
                for topic in selected_topics
            ]

            questions = await workflow.wait_all(question_tasks)
            self._progress = 55

            # 3c, 3d, 3e - 병렬 Enhancement Agents
            # (Terminology, Scenario Writer, Follow-up Designer)
            enhancement_tasks = [
                # 3c. Terminology Agent - 모든 용어 설명 생성/검증
                workflow.execute_activity(
                    question_generation.enhance_terminology,
                    args=[job_id, questions],
                    start_to_close_timeout=short_timeout,
                    retry_policy=retry_policy,
                ),
                # 3d. Scenario Writer Agent - 채점 시나리오 텍스트 생성
                workflow.execute_activity(
                    question_generation.craft_evaluation_scenarios,
                    args=[job_id, questions, enriched_input],
                    start_to_close_timeout=short_timeout,
                    retry_policy=retry_policy,
                ),
                # 3e. Follow-up Designer Agent - 꼬리질문 설계
                workflow.execute_activity(
                    question_generation.design_follow_ups,
                    args=[job_id, questions, enriched_input],
                    start_to_close_timeout=short_timeout,
                    retry_policy=retry_policy,
                ),
            ]

            enhanced_results = await workflow.wait_all(enhancement_tasks)
            questions = self._merge_enhancements(questions, enhanced_results)
            self._progress = 65

            # 3f, 3g - 병렬 Guide Agents
            # (Interviewer Note, Decision Guide)
            guide_tasks = [
                # 3f. Interviewer Note Agent - 면접관 참고 노트 생성
                workflow.execute_activity(
                    question_generation.generate_interviewer_notes,
                    args=[job_id, questions, enriched_input],
                    start_to_close_timeout=short_timeout,
                    retry_policy=retry_policy,
                ),
                # 3g. Decision Guide Agent - 이력서/커버레터 기반 면접관 가이드
                workflow.execute_activity(
                    question_generation.generate_decision_guide,
                    args=[job_id, aggregated, enriched_input],
                    start_to_close_timeout=short_timeout,
                    retry_policy=retry_policy,
                ),
            ]

            guide_results = await workflow.wait_all(guide_tasks)
            interviewer_notes, decision_guide = guide_results
            questions = self._attach_interviewer_notes(questions, interviewer_notes)
            self._progress = 70

            # 3h. Quality Reviewer Agent - 최종 검토 및 종합
            self._current_phase = "reviewing"
            max_revisions = 3
            revision_count = 0

            while revision_count < max_revisions:
                review_result = await workflow.execute_activity(
                    quality_review.review_questions,
                    args=[job_id, questions],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )

                if review_result["verdict"] == "APPROVED":
                    break

                # 수정 필요
                questions = await workflow.execute_activity(
                    question_generation.revise_questions,
                    args=[job_id, questions, review_result["feedback"]],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )

                revision_count += 1

            self._progress = 85

            # ================================================
            # Phase 4: FINALIZATION
            # ================================================
            self._current_phase = "finalizing"

            final_output = await workflow.execute_activity(
                finalization.finalize_output,
                args=[job_id, questions, aggregated, enriched_input],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            self._current_phase = "completed"
            self._progress = 100

            # decision_guide를 final_output에 포함
            final_output["decision_guide"] = decision_guide

            # Webhook 호출 (callback_url이 있으면)
            callback_url = input_data.get("callback_url")
            if callback_url:
                await workflow.execute_activity(
                    webhook.send_webhook,
                    args=[job_id, callback_url, "completed"],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )

            return final_output

        except ActivityError as e:
            self._current_phase = "failed"
            workflow.logger.error(f"Workflow failed: {e}")
            raise

    def _merge_enhancements(self, questions: list[dict], enhancements: list[dict]) -> list[dict]:
        """Enhancement 결과를 질문에 병합"""
        terminology_map, scenarios, follow_ups = enhancements

        for q in questions:
            q_id = q["id"]
            # 용어 추가
            if q_id in terminology_map:
                q["terminology"] = terminology_map[q_id]
            # 시나리오 추가
            if q_id in scenarios:
                q["evaluation_scenarios"] = scenarios[q_id]
            # 꼬리질문 추가
            if q_id in follow_ups:
                q["follow_ups"] = follow_ups[q_id]

        return questions

    def _attach_interviewer_notes(self, questions: list[dict], notes: dict) -> list[dict]:
        """면접관 노트를 질문에 첨부"""
        for q in questions:
            q_id = q["id"]
            if q_id in notes:
                q["interviewer_notes"] = notes[q_id]

        return questions

    def _create_empty_document_result(self) -> dict:
        """문서 없을 때 빈 결과"""
        return {
            "name": "Unknown",
            "experience_years": 0,
            "skills": [],
            "education": [],
            "work_history": [],
            "projects": [],
            "summary": "문서가 제공되지 않았습니다.",
        }

    def _create_empty_code_result(self) -> dict:
        """코드 없을 때 빈 결과"""
        return {
            "repositories": [],
            "combined_tech_stack": [],
            "total_patterns": 0,
            "total_notable_implementations": 0,
            "top_question_candidates": [],
        }

    @workflow.query
    def get_progress(self) -> dict:
        """현재 진행 상황 조회 (Query)"""
        return {
            "phase": self._current_phase,
            "progress": self._progress,
        }

    @workflow.signal
    def cancel_workflow(self) -> None:
        """워크플로우 취소 (Signal)"""
        self._current_phase = "cancelled"
        raise workflow.CancelledError("Workflow cancelled by user")
```

### 3.2 Worker 설정

```python
"""
backend/app/worker.py
Temporal Worker 실행
"""
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from app.core.config import get_settings
from app.workflows.interview_workflow import InterviewGenerationWorkflow
from app.workflows.activities import (
    input_enrichment,
    planning,
    document_analysis,
    code_analysis,
    jd_analysis,
    question_generation,
    quality_review,
    finalization,
    checkpoint_activities,
    webhook,
)


async def main():
    """Worker 실행"""
    # Temporal 클라이언트 연결
    settings = get_settings()
    client = await Client.connect(settings.TEMPORAL_HOST)

    # Worker 생성
    worker = Worker(
        client,
        task_queue="interview-generation",
        workflows=[InterviewGenerationWorkflow],
        activities=[
            # Input Enrichment
            input_enrichment.enrich_input,

            # Planning
            planning.create_execution_plan,

            # Analysis
            document_analysis.analyze_documents,
            code_analysis.analyze_code,
            jd_analysis.analyze_jd,

            # Question Generation (Multi-Agent)
            question_generation.select_topics,          # 3a. Topic Selector
            question_generation.craft_question,         # 3b. Question Crafter
            question_generation.enhance_terminology,    # 3c. Terminology Agent
            question_generation.craft_evaluation_scenarios,  # 3d. Scenario Writer
            question_generation.design_follow_ups,      # 3e. Follow-up Designer
            question_generation.generate_interviewer_notes,  # 3f. Interviewer Note Agent
            question_generation.generate_decision_guide,     # 3g. Decision Guide Agent
            question_generation.revise_questions,       # 3h. Quality Reviewer (revision)

            # Review
            quality_review.review_questions,            # 3h. Quality Reviewer Agent

            # Finalization
            finalization.finalize_output,

            # Checkpoint
            checkpoint_activities.save_checkpoint,
            checkpoint_activities.load_prior_state,

            # Webhook
            webhook.send_webhook,
        ],
    )

    print(f"Worker started, listening on {settings.TEMPORAL_HOST}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Activity 상세

### 4.1 Activity 공통 패턴

```python
"""
Activity 공통 패턴

LLM 호출 스택:
  - Pydantic AI Agent: 오케스트레이션 + 구조화 출력 (result_type 지정)
  - LiteLLM (library mode): 게이트웨이 + Redis 캐싱 + provider fallback
  - Instructor: 복잡한 구조화 추출 보완 (Pydantic AI로 부족한 케이스)
  - Langfuse: 프롬프트 관리 + 토큰/비용 추적 (self-host)

문서 파싱:
  - Docling (IBM): PDF/DOCX 구조화 파싱 (테이블, 이미지 포함)
  - pymupdf4llm: 경량 fallback (Docling 실패 시)

Storage:
  - obstore: Rust 기반 async S3-compatible (local/R2/S3)
"""
from temporalio import activity
from app.core.config import get_settings
from app.services.llm_config import get_llm_agent
from app.services.vector_store import get_vector_store


@activity.defn
async def example_activity(job_id: str, data: dict) -> dict:
    """
    Activity 구현 패턴

    - @activity.defn 데코레이터 필수
    - async 함수로 구현
    - activity.heartbeat()로 긴 작업 진행 보고
    - 재시도 가능하도록 멱등성 유지
    """
    # Pydantic AI Agent (LiteLLM 백엔드, Redis 자동 캐싱)
    agent = get_llm_agent(result_type=MyResultModel)
    result = await agent.run(prompt, deps=deps)

    # 벡터 스토어
    vector_store = get_vector_store(job_id)

    # Heartbeat (긴 작업 시)
    activity.heartbeat(f"Processing step 1 of 3")

    return result.data.model_dump()
```

### 4.2 예외 처리 구조

```python
"""
backend/app/exceptions.py
프로젝트 공통 예외 계층 — 모든 커스텀 예외는 VantictBaseError를 상속
"""


class VantictBaseError(Exception):
    """프로젝트 베이스 예외. 모든 커스텀 예외의 루트."""
    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


# ── Input Enrichment ──
class DocumentParseError(VantictBaseError):
    """문서 파싱 실패 (PDF/DOCX 깨짐, S3 접근 불가 등)"""
    def __init__(self, message: str, *, source: str = "unknown"):
        super().__init__(message, details={"source": source})


class LinkedInFetchError(VantictBaseError):
    """LinkedIn 프로필 수집 실패 (Bright Data API 오류, rate limit 등)"""
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message, details={"status_code": status_code})


class URLExtractionError(VantictBaseError):
    """URL 추출/검증 실패"""


# ── Code Analysis ──
class GitHubAccessError(VantictBaseError):
    """GitHub API 접근 실패 (토큰 만료, rate limit, 비공개 레포 등)"""


class CodeAnalysisError(VantictBaseError):
    """코드 분석 파이프라인 오류 (PyDriller, AST, LLM)"""
    def __init__(self, message: str, *, phase: str = "unknown", repo: str = ""):
        super().__init__(message, details={"phase": phase, "repo": repo})


# ── LLM ──
class LLMServiceError(VantictBaseError):
    """LLM API 호출 실패"""
    def __init__(self, message: str, *, provider: str = "", model: str = ""):
        super().__init__(message, details={"provider": provider, "model": model})


# ── Storage ──
class StorageError(VantictBaseError):
    """S3/Redis 스토리지 오류"""


# ── Quality ──
class QualityReviewError(VantictBaseError):
    """품질 검토 실패"""
```

> **Temporal 재시도와의 관계**: `VantictBaseError` 하위 예외 중 일시적 오류(rate limit 등)는
> `RetryPolicy`의 `non_retryable_error_types`에 포함하지 않아 자동 재시도 대상.
> `ValueError`, `ValidationError` 등 입력 오류는 재시도하지 않음.

### 4.3 Input Enrichment Activity

```python
"""
backend/app/workflows/activities/input_enrichment.py
Smart Input Extraction — 입력 교차 추출 및 보강
"""
import re
from temporalio import activity

from app.exceptions import (
    DocumentParseError,
    LinkedInFetchError,
)


@activity.defn
async def enrich_input(job_id: str, input_data: dict) -> dict:
    """
    Phase 0: Smart Input Extraction

    모든 입력에서 URL/프로필 정보를 교차 추출하여 빈 필드를 자동으로 채움.
    유저가 직접 입력하지 않아도 제공된 정보에서 필요한 데이터를 발견.

    Steps:
        1. PDF/DOCX 텍스트에서 URL 추출 (GitHub, LinkedIn)
        2. LinkedIn URL → Bright Data API → 프로필 수집
        3. GitHub username 자동 추론 (URL 패턴)
        4. 중복 제거 + EnrichedInput 생성
    """
    from docling.document_converter import DocumentConverter  # IBM Docling
    from app.services.linkedin_service import Bright DataService

    converter = DocumentConverter()  # PDF/DOCX 구조화 파싱
    extracted_urls = {"github": set(), "linkedin": set()}
    extraction_sources = {}

    # 1. Resume에서 URL 추출
    if input_data.get("resume_path"):
        activity.heartbeat("Extracting URLs from resume...")
        try:
            text = await _extract_text(converter, input_data["resume_path"])
            found = _extract_urls(text)
            for url in found["github"]:
                extracted_urls["github"].add(url)
                extraction_sources.setdefault("github_urls", []).append("resume")
            for url in found["linkedin"]:
                extracted_urls["linkedin"].add(url)
                extraction_sources.setdefault("linkedin_url", []).append("resume")
        except Exception as e:
            raise DocumentParseError(
                f"Resume 파싱 실패: {input_data['resume_path']}", source="resume"
            ) from e

    # 2. Portfolio에서 URL 추출
    if input_data.get("portfolio_path"):
        activity.heartbeat("Extracting URLs from portfolio...")
        try:
            text = await _extract_text(converter, input_data["portfolio_path"])
            found = _extract_urls(text)
            for url in found["github"]:
                extracted_urls["github"].add(url)
                extraction_sources.setdefault("github_urls", []).append("portfolio")
        except Exception as e:
            raise DocumentParseError(
                f"Portfolio 파싱 실패: {input_data['portfolio_path']}", source="portfolio"
            ) from e

    if input_data.get("cover_letter_path"):
        activity.heartbeat("Extracting URLs from cover letter...")
        try:
            text = await _extract_text(converter, input_data["cover_letter_path"])
            found = _extract_urls(text)
            for url in found["github"]:
                extracted_urls["github"].add(url)
                extraction_sources.setdefault("github_urls", []).append("cover_letter")
        except Exception as e:
            raise DocumentParseError(
                f"Cover letter 파싱 실패: {input_data['cover_letter_path']}", source="cover_letter"
            ) from e

    # 3. 직접 입력된 URL 병합
    for url in input_data.get("github_urls", []):
        extracted_urls["github"].add(str(url))
        extraction_sources.setdefault("github_urls", []).append("user_input")

    linkedin_url = (
        input_data.get("linkedin_url")
        or (list(extracted_urls["linkedin"])[0] if extracted_urls["linkedin"] else None)
    )

    # 4. LinkedIn → Bright Data API (실패 시 graceful fallback)
    linkedin_profile = None
    if linkedin_url:
        activity.heartbeat("Fetching LinkedIn profile via Bright Data...")
        try:
            linkedin_svc = Bright DataService()
            linkedin_profile = await linkedin_svc.get_profile(linkedin_url)
        except LinkedInFetchError:
            raise  # 이미 우리 예외 → 그대로 전파
        except Exception as e:
            # Bright Data 실패 시 LinkedIn 없이 진행 (non-fatal)
            activity.logger.warning(f"Bright Data failed for {linkedin_url}: {e}")
            linkedin_profile = None

        # LinkedIn에서 GitHub URL 발견 시 추가
        if linkedin_profile and linkedin_profile.get("github_url"):
            extracted_urls["github"].add(linkedin_profile["github_url"])
            extraction_sources.setdefault("github_urls", []).append("linkedin")

    # 5. GitHub username 자동 추론
    github_urls = list(extracted_urls["github"])
    candidate_username = input_data.get("candidate_github_username")
    if not candidate_username and github_urls:
        candidate_username = _extract_github_username(github_urls[0])

    # 6. 사용 가능한 분석 목록
    available = ["jd_analysis"]  # JD는 항상
    if input_data.get("resume_path") or input_data.get("portfolio_path") or input_data.get("cover_letter_path") or linkedin_profile:
        available.append("document_analysis")
    if github_urls:
        available.append("code_analysis")

    return {
        "raw_input": input_data,
        "github_urls": github_urls,
        "candidate_github_username": candidate_username,
        "linkedin_profile": linkedin_profile,
        "extraction_sources": extraction_sources,
        "available_analyses": available,
    }


def _extract_urls(text: str) -> dict[str, list[str]]:
    """텍스트에서 GitHub/LinkedIn URL 추출
    GitHub: /owner/repo 형태만 매칭 (org 루트 URL 제외)
    """
    github_pattern = r'https?://github\.com/[\w\-]+/[\w\-\.]+'
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+'
    return {
        "github": re.findall(github_pattern, text),
        "linkedin": re.findall(linkedin_pattern, text),
    }


def _extract_github_username(github_url: str) -> str | None:
    """GitHub URL에서 username 추출 (/owner/repo 형태에서 owner)"""
    match = re.match(r'https?://github\.com/([\w\-]+)/[\w\-\.]+', github_url)
    return match.group(1) if match else None
```

### 4.4 Planning Activity

```python
"""
backend/app/workflows/activities/planning.py
실행 계획 수립 Activity
"""
from temporalio import activity
from app.services.github_service import GitHubService


@activity.defn
async def create_execution_plan(job_id: str, enriched_input: dict) -> dict:
    """
    실행 계획 수립 (enriched_input 기반)

    1. enriched_input 검증
    2. GitHub API로 워크로드 추정
    3. 실행 계획 생성
    """
    github = GitHubService()
    raw_input = enriched_input.get("raw_input", {})

    # 입력 검증
    validated = validate_input(enriched_input)

    # JD에서 기술스택 사전 추출 (코드 분석 Phase 1용)
    from app.services.llm_config import get_llm_agent
    agent = get_llm_agent()
    jd_result = await agent.run(f"Extract tech stack from JD:\n{raw_input['jd_text']}")
    jd_tech_stack = jd_result.data  # ["Python", "FastAPI", "PostgreSQL", ...]
    # → ["Python", "FastAPI", "PostgreSQL", ...] JD에서 언급된 기술 목록

    # GitHub 워크로드 추정 (PyGithub 기반, enriched github_urls 사용)
    workload = {}
    github_urls = enriched_input.get("github_urls", [])
    for url in github_urls:
        repo_info = await github.get_repo_info(url)
        languages = await github.get_repo_languages(url)
        workload[url] = {
            "total_files": repo_info["size"],
            "languages": languages,  # {"Python": 45000, "JS": 2000}
            "jd_match": any(lang in languages for lang in jd_tech_stack),
            "estimated_time_seconds": calculate_time(repo_info),
        }

    # 실행 계획 생성
    available = enriched_input.get("available_analyses", [])
    plan = {
        "job_id": job_id,
        "jd_tech_stack": jd_tech_stack,  # Phase 2 코드 분석에서 레포 필터링용
        "candidate_github_username": enriched_input.get("candidate_github_username"),
        "phases": [
            {"name": "document_analysis", "enabled": "document_analysis" in available},
            {"name": "code_analysis", "enabled": "code_analysis" in available},
            {"name": "jd_analysis", "enabled": True},
        ],
        "workload": workload,
        "jd_matched_repos": [url for url, w in workload.items() if w.get("jd_match")],
        "estimated_total_time_seconds": sum(w["estimated_time_seconds"] for w in workload.values()) + 120,
    }

    return plan
```

### 4.5 Analysis Activities

```python
"""
backend/app/workflows/activities/document_analysis.py
문서 분석 Activity
"""
from temporalio import activity


@activity.defn
async def analyze_documents(job_id: str, input_data: dict) -> dict:
    """
    이력서/포트폴리오 분석

    1. S3에서 파일 다운로드
    2. PDF/DOCX 파싱
    3. LLM으로 프로필 추출
    4. 벡터 스토어에 저장
    """
    from docling.document_converter import DocumentConverter
    from app.services.llm_config import get_llm_agent
    from app.services.vector_store import get_vector_store
    from app.models.analysis import CandidateProfile

    converter = DocumentConverter()  # Docling (IBM)
    agent = get_llm_agent(result_type=CandidateProfile)
    vector_store = get_vector_store(job_id)

    # 문서 파싱 (Docling: 테이블/이미지 포함 구조화 추출)
    documents = []
    if input_data.get("resume_path"):
        activity.heartbeat("Parsing resume with Docling...")
        result = converter.convert(input_data["resume_path"])
        documents.append(result.document.export_to_markdown())

    if input_data.get("portfolio_path"):
        activity.heartbeat("Parsing portfolio with Docling...")
        result = converter.convert(input_data["portfolio_path"])
        documents.append(result.document.export_to_markdown())

    if input_data.get("cover_letter_path"):
        activity.heartbeat("Parsing cover letter with Docling...")
        result = converter.convert(input_data["cover_letter_path"])
        documents.append(result.document.export_to_markdown())

    # Pydantic AI Agent로 프로필 추출 (구조화 출력)
    activity.heartbeat("Extracting profile with LLM...")
    run_result = await agent.run(
        f"Extract candidate profile:\n\n{'---'.join(documents)}"
    )
    profile = run_result.data.model_dump()

    # 벡터 스토어에 저장
    await vector_store.store_profile(profile)

    return profile


"""
backend/app/workflows/activities/code_analysis.py
코드 분석 Activity (PyGithub + PyDriller + GitHub API 파이프라인)

의존성:
  - PyGithub: GitHub API 래퍼 (레포 메타데이터, 언어 정보, Search API)
  - PyDriller: Git 레포 분석 전용 (커밋 순회, 복잡도, diff 추출)

환경변수:
  - GITHUB_ANALYSIS_YEARS: 분석 기간 (기본 1년, 최대 3년 권장)
  - GITHUB_TOKEN: GitHub API 토큰 (5000 req/hour)
"""
@activity.defn
async def analyze_code(job_id: str, github_urls: list[str], input_data: dict, execution_plan: dict = None) -> dict:
    """
    GitHub 종합 코드 분석 — 4-Channel 파이프라인

    ┌─────────────────────────────────────────────────────────────────────┐
    │                    4-Channel GitHub Analysis                        │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  Channel A: 본인 레포 분석 (PyDriller - diff 기반)                   │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │ • JD 매칭 레포 선별 (PyGithub)                               │   │
    │  │ • diff 기반 코드 추출 (source_code 대신 diff만)              │   │
    │  │ • 분석 기간: GITHUB_ANALYSIS_YEARS (기본 1년)                │   │
    │  │ • AST 구조 분석 (Python ast, JS/TS tree-sitter)             │   │
    │  │ • 토큰 예산: ~3,000-5,000 tokens/repo                       │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    │  Channel B: 오픈소스 PR 기여 (GitHub Search API)                    │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │ • 검색: author:{username} type:pr is:merged -user:{username}│   │
    │  │ • 외부 레포에 머지된 PR 분석                                  │   │
    │  │ • PR 제목, 설명, 변경 파일 수, 리뷰 코멘트                     │   │
    │  │ • 토큰 예산: ~500-1,000 tokens/PR                           │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    │  Channel C: 이슈 참여 (GitHub Search API)                           │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │ • 작성한 이슈: author:{username} type:issue                  │   │
    │  │ • 코멘트한 이슈: commenter:{username} type:issue             │   │
    │  │ • 이슈 제목, 본문 요약, 라벨, 상태                            │   │
    │  │ • 토큰 예산: ~200-500 tokens/issue                          │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    │  Channel D: 코드 리뷰 활동 (GitHub Events API)                      │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │ • PullRequestReviewEvent 필터링                              │   │
    │  │ • 리뷰 상태: APPROVED, CHANGES_REQUESTED, COMMENTED          │   │
    │  │ • 리뷰 본문, 인라인 코멘트                                    │   │
    │  │ • 토큰 예산: ~300-800 tokens/review                         │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    Channel A 상세 (본인 레포):
        Phase 1 (PyGithub): JD 매칭 레포 선별
            - 후보자 레포별 언어 비율 조회
            - JD 기술스택과 매칭되는 레포만 필터
        Phase 2 (PyDriller): 후보자 코드 추출 + 정적 메트릭
            - 선별 레포 auto-clone
            - only_authors: 후보자 커밋만 필터
            - since/to: GITHUB_ANALYSIS_YEARS (기본 1년) 범위
            - only_modifications_with_file_types: JD 매칭 확장자
            - 파일별 complexity, nloc, **diff** 추출 (source_code 대신)
        Phase 3 (AST): 구조적 코드 분석
            - Phase 2 상위 N개 파일 대상 (complexity × JD match 기준)
            - Python: ast 모듈 (빌트인)
            - JS/TS: tree-sitter 파서
            - 추출: 함수 시그니처, 클래스 계층, 디자인 패턴, import 구조
            - 미지원 언어 fallback: Phase 2 메트릭만 사용
        Phase 4 (LLM): 의미 분석 + 질문 후보 추출
            - 토큰 예산(30K/레포) 내 파일 랭킹
            - Phase 2 메트릭 + Phase 3 AST 구조를 컨텍스트로 전달
            - 패턴 탐지, notable implementations 추출
            - 벡터 스토어 저장

    총 토큰 예산 (활발한 개발자 기준):
        - Channel A (3 repos): ~12,000 tokens
        - Channel B (10 PRs):  ~8,000 tokens
        - Channel C (15 issues): ~5,250 tokens
        - Channel D (20 reviews): ~8,000 tokens
        - Total: ~33,250 tokens
    """
    from app.services.github_service import GitHubService
    from app.services.github_analyzer import GitHubComprehensiveAnalyzer
    from app.services.code_analyzer import CodeAnalyzer
    from app.services.vector_store import get_vector_store
    from app.core.config import settings
    import os

    github = GitHubService()  # PyGithub 기반
    analyzer = CodeAnalyzer()  # PyDriller 기반
    vector_store = get_vector_store(job_id)

    # 환경변수에서 분석 기간 설정 (기본 1년)
    analysis_years = int(os.getenv("GITHUB_ANALYSIS_YEARS", "1"))

    # execution_plan에서 jd_tech_stack 우선, fallback으로 input_data
    jd_tech_stack = (execution_plan or {}).get("jd_tech_stack") or input_data.get("jd_tech_stack", [])
    candidate_username = input_data.get("candidate_github_username")

    # ══════════════════════════════════════════════════════════════════
    # 4-Channel GitHub Analysis (병렬 실행)
    # ══════════════════════════════════════════════════════════════════

    comprehensive_analyzer = GitHubComprehensiveAnalyzer(
        username=candidate_username,
        github_token=settings.GITHUB_TOKEN,
        analysis_years=analysis_years,
    )

    # Channel B, C, D 병렬 수집 (본인 레포 외 활동)
    activity.heartbeat("Collecting OSS contributions, issues, and code reviews...")
    oss_contributions, issue_participations, code_reviews = await asyncio.gather(
        comprehensive_analyzer.analyze_oss_prs(),       # Channel B
        comprehensive_analyzer.analyze_issues(),         # Channel C
        comprehensive_analyzer.analyze_code_reviews(),   # Channel D
    )

    # ── Channel A: 본인 레포 분석 (기존 로직 개선) ──
    activity.heartbeat("Channel A: Filtering repos by JD tech stack...")

    target_repos = await github.filter_repos_by_language(
        github_urls=github_urls,
        target_languages=jd_tech_stack,
        min_language_ratio=0.3,
    )

    # ── Phase 2~4: 레포별 분석 파이프라인 ──
    # Heartbeat recovery: 완료된 repo는 건너뛰고, 실패한 repo만 재분석
    heartbeat_details = activity.info().heartbeat_details
    completed_repos = heartbeat_details[0] if heartbeat_details else {}  # {repo_url: result}
    repositories = list(completed_repos.values()) if completed_repos else []

    file_types = _jd_to_file_types(jd_tech_stack)

    for i, repo_info in enumerate(target_repos):
        # 이미 완료된 repo는 건너뜀
        if repo_info["url"] in completed_repos:
            continue

        activity.heartbeat(
            f"Channel A Phase 2: Analyzing {repo_info['name']} ({i+1}/{len(target_repos)})"
        )

        # PyDriller: clone + 후보자 커밋 순회 + **diff 기반** 추출
        driller_result = await analyzer.analyze_with_pydriller(
            repo_url=repo_info["url"],
            job_id=job_id,
            author=candidate_username,
            since_years=analysis_years,  # 환경변수 기반 (기본 1년)
            file_types=file_types,
            extract_diff=True,  # diff만 추출 (source_code 대신)
        )
        # driller_result 구조 (diff 기반):
        # {
        #   "commits": [{hash, msg, date, files_changed}],
        #   "files": [{filename, diff, complexity, nloc, methods, added, deleted}],
        #   "stats": {total_commits, total_additions, total_deletions, avg_complexity}
        # }

        # ── Phase 3: AST 구조 분석 ──
        activity.heartbeat(f"Phase 3: AST analysis for {repo_info['name']}...")

        # 상위 N개 파일만 AST 분석 (complexity × JD match 기준)
        top_files = analyzer.select_top_files(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            max_files=20,
        )

        ast_result = await analyzer.analyze_ast(
            files=top_files,
            primary_language=repo_info["primary_language"],
        )
        # ast_result 구조:
        # {
        #   "functions": [{name, params, return_type, decorators, complexity}],
        #   "classes": [{name, bases, methods, attributes}],
        #   "patterns": [{type, name, evidence}],  # Singleton, Factory 등
        #   "imports": [{module, alias, is_third_party}],
        #   "parser_used": "ast" | "tree-sitter" | "fallback",
        # }
        # MVP 지원: Python (ast 빌트인), JS/TS (tree-sitter)
        # 미지원 언어: fallback → Phase 2 메트릭만 사용

        # ── Phase 4: LLM 의미 분석 ──
        activity.heartbeat(f"Phase 4: LLM analysis for {repo_info['name']}...")

        ranked_files = analyzer.rank_files_for_llm(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            token_budget=30_000,
        )

        analysis = await analyzer.llm_analyze_code(
            ranked_files,
            ast_context=ast_result,  # AST 구조를 LLM 컨텍스트로 전달
        )
        notable = analysis.get("notable_implementations", [])

        for impl in notable:
            await vector_store.store_code(impl)

        repositories.append({
            "repo_url": repo_info["url"],
            "repo_name": repo_info["name"],
            "language": repo_info["primary_language"],
            "candidate_commits": driller_result["stats"]["total_commits"],
            "candidate_additions": driller_result["stats"]["total_additions"],
            "avg_complexity": driller_result["stats"]["avg_complexity"],
            "ast_analysis": ast_result,
            "analysis": analysis,
            "notable_implementations": notable,
        })

        completed_repos[repo_info["url"]] = repositories[-1]
        activity.heartbeat(completed_repos)

    # 4-Channel 통합 결과 반환
    return aggregate_comprehensive_analysis(
        own_repos=repositories,
        oss_contributions=oss_contributions,
        issue_participations=issue_participations,
        code_reviews=code_reviews,
        analysis_years=analysis_years,
        candidate_username=candidate_username,
    )


def _jd_to_file_types(jd_tech_stack: list[str]) -> list[str]:
    """JD 기술스택 → 분석 대상 파일 확장자"""
    mapping = {
        "Python": [".py"], "JavaScript": [".js", ".jsx"],
        "TypeScript": [".ts", ".tsx"], "Java": [".java"],
        "Go": [".go"], "Rust": [".rs"], "C++": [".cpp", ".hpp"],
    }
    types = []
    for tech in jd_tech_stack:
        types.extend(mapping.get(tech, []))
    return types or [".py"]


"""
backend/app/workflows/activities/jd_analysis.py
채용공고 분석 Activity
"""
@activity.defn
async def analyze_jd(job_id: str, jd_text: str) -> dict:
    """
    채용공고(JD) 분석

    1. 요구사항 추출
    2. 스킬 추출
    3. 회사 문화 추출
    """
    from app.services.llm_config import get_llm_agent
    from app.models.analysis import JDAnalysis

    agent = get_llm_agent(result_type=JDAnalysis)

    # Pydantic AI Agent로 JD 분석 (구조화 출력)
    run_result = await agent.run(f"Analyze job description:\n{jd_text}")
    analysis = run_result.data.model_dump()

    return {
        "job_title": analysis.get("job_title"),
        "company_name": analysis.get("company_name"),
        "requirements": analysis.get("requirements", []),
        "responsibilities": analysis.get("responsibilities", []),
        "company_culture": analysis.get("company_culture", []),
        "skill_matches": [],  # 나중에 aggregate에서 채움
        "overall_match_score": 0,
        "gaps": [],
        "strengths": [],
    }
```

### 4.6 Question Generation Activities

```python
"""
backend/app/workflows/activities/question_generation.py
질문 생성 Activity
"""
from temporalio import activity


@activity.defn
async def select_topics(job_id: str, analysis: dict, enriched_input: dict) -> list[dict]:
    """
    25개 질문 토픽 선정 (5카테고리 × 5)

    선정 기준:
    1. 코드에서 발견된 주목할 만한 구현
    2. JD 요구사항과의 매칭
    3. 경험 레벨에 맞는 난이도
    """
    from app.services.llm_config import get_llm_agent
    from app.services.vector_store import get_vector_store

    agent = get_llm_agent()
    vector_store = get_vector_store(job_id)
    raw_input = enriched_input.get("raw_input", {})

    # 질문 후보 수집
    candidates = []

    # 코드 기반 후보
    code_analysis = analysis.get("code_analysis", {})
    for impl in code_analysis.get("top_question_candidates", []):
        candidates.append({
            "source": "code",
            "topic": impl["title"],
            "evidence": impl,
            "score": impl.get("question_potential", 0.5),
        })

    # JD 기반 후보
    jd_analysis = analysis.get("jd_analysis", {})
    for req in jd_analysis.get("requirements", []):
        # 관련 코드 증거 검색
        evidence = await vector_store.search_code(req["skill"])
        if evidence:
            candidates.append({
                "source": "jd_match",
                "topic": req["skill"],
                "evidence": evidence[0],
                "score": 0.7 if req["category"] == "필수" else 0.5,
            })

    # Pydantic AI Agent로 최종 25개 선정 (5카테고리 × 5)
    experience_level = raw_input.get("experience_level", "미들")
    max_questions = raw_input.get("max_questions", 25)

    run_result = await agent.run(
        f"Select {max_questions} best topics for {experience_level} level",
        deps={"candidates": candidates},
    )

    return run_result.data


@activity.defn
async def craft_question(
    job_id: str,
    topic: dict,
    analysis: dict,
    enriched_input: dict,
) -> dict:
    """
    단일 질문 상세 생성 (주 언어만, 다국어는 on-demand)

    생성 내용:
    - 메인 질문 (output_language 단일 언어)
    - 대체 표현
    - 예상 답변
    - 평가 시나리오
    - 꼬리질문
    - 용어 설명
    """
    from app.services.llm_config import get_llm_agent
    from app.services.vector_store import get_vector_store
    from app.models.question import InterviewQuestion

    agent = get_llm_agent(result_type=InterviewQuestion)
    vector_store = get_vector_store(job_id)
    raw_input = enriched_input.get("raw_input", {})

    # 관련 코드 컨텍스트 수집
    code_context = await vector_store.search_code(topic["topic"], top_k=3)

    # 언어 설정 — 주 언어만 생성 (on-demand i18n)
    language_config = raw_input.get("language_config", {})
    output_language = language_config.get("output_language", "ko")

    # Pydantic AI Agent로 질문 생성 (구조화 출력, 단일 언어)
    run_result = await agent.run(
        f"Generate interview question in {output_language}",
        deps={
            "topic": topic,
            "code_context": code_context,
            "candidate_profile": analysis.get("document_analysis"),
            "jd_analysis": analysis.get("jd_analysis"),
            "experience_level": raw_input.get("experience_level", "미들"),
            "include_expected_answer": raw_input.get("include_expected_answers", True),
        },
    )
    question = run_result.data.model_dump()

    # question_text: str (단일 언어)
    # language: output_language 태깅
    question["language"] = output_language

    return question


@activity.defn
async def revise_questions(
    job_id: str,
    questions: list[dict],
    feedback: dict
) -> list[dict]:
    """
    피드백 기반 질문 수정

    수정 대상:
    - 중복 질문
    - 연관성 부족한 질문
    - 난이도 조정 필요한 질문
    """
    from app.services.llm_config import get_llm_agent

    agent = get_llm_agent()

    # 수정이 필요한 질문만 처리
    questions_to_revise = feedback.get("questions_to_revise", [])

    revised = []
    for q in questions:
        if q["id"] in questions_to_revise:
            revision_feedback = feedback.get("details", {}).get(q["id"], {})
            run_result = await agent.run(
                "Revise question based on feedback",
                deps={"question": q, "feedback": revision_feedback},
            )
            revised.append(run_result.data)
        else:
            revised.append(q)

    return revised
```

### 4.7 Quality Review Activity

```python
"""
backend/app/workflows/activities/quality_review.py
품질 검토 Activity
"""
from temporalio import activity


@activity.defn
async def review_questions(job_id: str, questions: list[dict]) -> dict:
    """
    질문 품질 검토

    검토 항목:
    1. 중복 검사 - 유사한 질문이 있는지
    2. 연관성 검토 - 코드 증거가 유효한지
    3. 흐름 최적화 - 질문 순서가 자연스러운지
    4. 난이도 균형 - 레벨별 분포가 적절한지
    """
    from app.services.llm_config import get_llm_agent
    from app.services.vector_store import get_vector_store

    agent = get_llm_agent()
    vector_store = get_vector_store(job_id)

    issues = []
    questions_to_revise = []

    # 1. 중복 검사 (question_text: str — 단일 언어)
    for i, q1 in enumerate(questions):
        for j, q2 in enumerate(questions[i+1:], i+1):
            sim_result = await agent.run(
                f"Rate similarity 0-1:\nQ1: {q1['question_text']}\nQ2: {q2['question_text']}"
            )
            similarity = sim_result.data
            if similarity > 0.8:
                issues.append({
                    "type": "duplicate",
                    "questions": [q1["id"], q2["id"]],
                    "similarity": similarity,
                })
                questions_to_revise.append(q2["id"])

    # 2. 코드 증거 검증
    for q in questions:
        if q.get("code_reference"):
            is_valid = await vector_store.verify_code_reference(
                q["code_reference"]
            )
            if not is_valid:
                issues.append({
                    "type": "invalid_reference",
                    "question": q["id"],
                })
                questions_to_revise.append(q["id"])

    # 3. 흐름 최적화 (LLM 판단)
    flow_result = await agent.run("Analyze question flow", deps={"questions": questions})
    flow_analysis = flow_result.data
    if flow_analysis.get("needs_reorder"):
        issues.append({
            "type": "flow",
            "suggestion": flow_analysis["suggested_order"],
        })

    # 4. 난이도 균형
    difficulty_dist = count_difficulty_distribution(questions)
    if not is_balanced(difficulty_dist):
        issues.append({
            "type": "difficulty_imbalance",
            "distribution": difficulty_dist,
        })

    # 최종 판정
    verdict = "APPROVED" if len(questions_to_revise) == 0 else "NEEDS_REVISION"

    return {
        "verdict": verdict,
        "issues": issues,
        "questions_to_revise": list(set(questions_to_revise)),
        "feedback": {
            "details": {qid: {"reason": "..."} for qid in questions_to_revise}
        },
    }
```

### 4.8 Finalization Activity

```python
"""
backend/app/workflows/activities/finalization.py
최종화 Activity
"""
from temporalio import activity


@activity.defn
async def finalize_output(
    job_id: str,
    questions: list[dict],
    analysis: dict,
    enriched_input: dict,
) -> dict:
    """
    최종 면접 스크립트 생성

    1. Hallucination 최종 검증
    2. 용어집 통합
    3. 면접관 가이드 생성
    4. 스크립트 조립
    5. S3 저장
    """
    from app.services.llm_config import get_llm_agent
    from app.services.vector_store import get_vector_store
    import obstore as obs
    from app.core.config import get_settings
    from datetime import datetime

    settings = get_settings()
    agent = get_llm_agent()
    vector_store = get_vector_store(job_id)
    store = obs.store.S3Store.from_env(settings.S3_BUCKET)  # obstore (local/R2/S3)
    raw_input = enriched_input.get("raw_input", {})

    activity.heartbeat("Verifying questions...")

    # 1. Hallucination 검증 (question_text: str 단일 언어)
    for q in questions:
        if q.get("code_reference"):
            is_valid = await vector_store.verify_with_evidence(
                claim=q["question_text"],  # str
                evidence_query=q["code_reference"]["file_path"],
            )
            if not is_valid:
                q["code_reference"]["warning"] = "검증 필요"

    activity.heartbeat("Generating guide...")

    # 2. 용어집 통합
    all_terms = []
    seen_terms = set()
    for q in questions:
        for term in q.get("terminology", []):
            if term["term"] not in seen_terms:
                all_terms.append(term)
                seen_terms.add(term["term"])

    # 3. 후보자 요약 생성 (Pydantic AI Agent)
    summary_result = await agent.run(
        "Generate candidate summary",
        deps={
            "profile": analysis.get("document_analysis"),
            "code_analysis": analysis.get("code_analysis"),
            "jd_analysis": analysis.get("jd_analysis"),
        },
    )
    candidate_summary = summary_result.data

    # 4. 면접관 가이드 생성 (Pydantic AI Agent)
    guide_result = await agent.run(
        "Generate interviewer guide",
        deps={"questions": questions, "experience_level": raw_input.get("experience_level")},
    )
    interviewer_guide = guide_result.data

    # 5. 최종 스크립트 조립
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    final_script = {
        "job_id": job_id,
        "generated_at": datetime.utcnow().isoformat(),
        "output_language": output_language,
        "candidate_summary": candidate_summary,
        "questions": questions,
        "interviewer_guide": interviewer_guide,
        "full_glossary": all_terms,
        "metadata": {
            "total_questions": len(questions),
            "language": output_language,  # 주 언어 (다국어는 on-demand)
            "terminology_count": len(all_terms),
        },
    }

    activity.heartbeat("Saving to storage...")

    # 6. obstore 저장 (local/R2/S3)
    await obs.put_async(
        store,
        f"outputs/{job_id}/interview_script.json",
        json.dumps(final_script, ensure_ascii=False).encode(),
    )

    return final_script
```

### 4.9 Webhook Activity

```python
"""
backend/app/workflows/activities/webhook.py
완료 웹훅 호출 Activity
"""
import httpx
from temporalio import activity


@activity.defn
async def send_webhook(job_id: str, callback_url: str, status: str) -> dict:
    """
    Job 완료 시 callback_url로 웹훅 POST 전송

    Args:
        job_id: 작업 ID
        callback_url: 호출할 웹훅 URL
        status: 작업 상태 ("completed" | "failed")

    Returns:
        {"status_code": int, "success": bool}
    """
    payload = {
        "job_id": job_id,
        "status": status,
        "result_url": f"/api/v1/jobs/{job_id}/result",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(callback_url, json=payload)

    return {
        "status_code": response.status_code,
        "success": 200 <= response.status_code < 300,
    }
```

### 4.10 코드 분석 클린업

> `analyze_code` Activity에서 PyDriller가 `/tmp` 디렉터리에 git clone하는데,
> Worker 재시작이나 Activity 실패 시 orphaned 클론이 남을 수 있음.
> 아래 패턴으로 `tempfile.mkdtemp()` 사용 및 `finally` 블록에서 정리.

```python
# code_analysis.py 내 클린업 패턴 (기존 analyze_code에 적용)
import tempfile
import shutil

@activity.defn
async def analyze_code(job_id: str, github_urls: list[str], input_data: dict, execution_plan: dict = None) -> dict:
    clone_dirs: list[str] = []
    try:
        for repo_info in target_repos:
            # tempfile로 격리된 디렉터리 생성
            clone_dir = tempfile.mkdtemp(prefix=f"vantict-{job_id[:8]}-")
            clone_dirs.append(clone_dir)

            driller_result = await analyzer.analyze_with_pydriller(
                repo_url=repo_info["url"],
                job_id=job_id,
                clone_dir=clone_dir,  # 명시적 클론 경로 전달
                author=candidate_username,
                since_years=3,
                file_types=file_types,
            )
            # ... 나머지 분석 로직
    finally:
        # 성공/실패 무관 — 클론된 레포 항상 정리
        for d in clone_dirs:
            shutil.rmtree(d, ignore_errors=True)

    return aggregate_code_analysis(repositories)
```

---

## 5. 클라이언트 사용법

### 5.1 워크플로우 시작

```python
"""
backend/app/api/routes/jobs.py
API에서 워크플로우 시작
"""
from temporalio.client import Client
from app.workflows.interview_workflow import InterviewGenerationWorkflow


async def start_job(input_data: dict) -> str:
    """새 Job 시작"""
    client = await Client.connect(settings.TEMPORAL_ADDRESS)

    job_id = str(uuid.uuid4())

    # 워크플로우 시작
    handle = await client.start_workflow(
        InterviewGenerationWorkflow.run,
        args=[job_id, input_data],
        id=f"interview-{job_id}",
        task_queue="interview-generation",
    )

    return job_id


async def get_job_status(job_id: str) -> dict:
    """Job 상태 조회"""
    client = await Client.connect(settings.TEMPORAL_ADDRESS)

    handle = client.get_workflow_handle(f"interview-{job_id}")

    # Query로 진행 상황 조회
    progress = await handle.query(
        InterviewGenerationWorkflow.get_progress
    )

    return progress


async def cancel_job(job_id: str) -> None:
    """Job 취소"""
    client = await Client.connect(settings.TEMPORAL_ADDRESS)

    handle = client.get_workflow_handle(f"interview-{job_id}")

    # Signal로 취소 요청
    await handle.signal(InterviewGenerationWorkflow.cancel_workflow)
```

---

## 6. 체크포인트 및 복구 전략

> 상세 구현: [skills/checkpoint-manager/SKILL.md](./skills/checkpoint-manager/SKILL.md) 참조

### 6.1 3-Layer 내구성 아키텍처

```
Layer 1: Temporal 내장 (Activity 단위 자동 복구)
  └→ Worker 죽어도 Event History replay로 자동 재개
  └→ Activity 실패 시 RetryPolicy에 따라 자동 재시도

Layer 2: LLM 결과 캐싱 (비용 절감)
  └→ 동일 프롬프트 → Redis 캐시 히트 → API 호출 0원
  └→ LiteLLM Redis 캐싱 (litellm.cache = Cache(type="redis"))

Layer 3: 단계별 스냅샷 (수동 재시작)
  └→ 각 Phase 완료 시 결과를 Redis + S3에 저장
  └→ API: POST /api/v1/jobs/{job_id}/retry?from_step=select_topics
  └→ checkpoint_store.py + checkpoint_activities.py
```

### 6.2 복구 시나리오

| 시나리오 | 자동/수동 | 비용 | 메커니즘 |
|----------|----------|------|----------|
| Worker 프로세스 크래시 | 자동 | 0 | Temporal Event History replay |
| LLM API 일시 장애 | 자동 | 0 | RetryPolicy (3회, exponential backoff) |
| LLM API 재시도 성공 | 자동 | 0 | LLMResultCache 캐시 히트 |
| 코드 분석 중 실패 | 자동 | 부분 | heartbeat로 완료된 repo 건너뜀 |
| Phase 3 실패 → Phase 3부터 재시작 | 수동 | 0 | CheckpointStore에서 Phase 1~2 로드 |
| 디버깅: 질문 생성만 재실행 | 수동 | 0 | `from_step=craft_questions` |

### 6.3 워크플로우 변경사항

기존 워크플로우 대비 추가된 요소:

```python
# 1. resume_from 시그널 (수동 재시작 지점 지정)
@workflow.signal
def set_resume_from(self, step: str) -> None:
    self._resume_from = step

# 2. 각 Phase 완료 시 체크포인트 저장
await workflow.execute_activity(
    checkpoint_activities.save_checkpoint,
    args=[job_id, "aggregate_analysis", aggregated],
)

# 3. 재시작 시 이전 결과 로드
prior_state = await workflow.execute_activity(
    checkpoint_activities.load_prior_state,
    args=[job_id, resume_from],
)

# 4. _should_run()으로 단계 실행 여부 판단
if self._should_run("select_topics", resume_from):
    # 실행
else:
    selected_topics = prior_state.get("select_topics", [])
```

### 6.4 Activity heartbeat 체크포인트

긴 Activity(코드 분석)에서 중간 진행을 heartbeat에 저장:

```python
@activity.defn
async def analyze_code(job_id: str, github_urls: list[str]) -> dict:
    # 이전 heartbeat에서 복구 — 완료된 repo dict 기반
    heartbeat_details = activity.info().heartbeat_details
    completed_repos = heartbeat_details[0] if heartbeat_details else {}
    repositories = list(completed_repos.values())

    for url in github_urls:
        if url in completed_repos:  # 이미 완료 → 건너뜀
            continue
        result = await _analyze_single_repo(url, job_id)
        repositories.append(result)
        completed_repos[url] = result
        activity.heartbeat(completed_repos)  # URL 키 기반 진행 저장

    return aggregate_code_analysis(repositories)
```

---

## 7. 로컬 vs 클라우드 설정

### 7.1 환경별 설정

```python
# .env.local
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default

# .env.production
TEMPORAL_ADDRESS=your-namespace.tmprl.cloud:7233
TEMPORAL_NAMESPACE=your-namespace
TEMPORAL_API_KEY=your-api-key
```

### 7.2 연결 코드 (동일)

```python
from temporalio.client import Client
from app.config import settings

async def get_temporal_client() -> Client:
    """환경에 따라 자동으로 로컬/클라우드 연결"""
    if settings.TEMPORAL_API_KEY:
        # Temporal Cloud
        return await Client.connect(
            settings.TEMPORAL_ADDRESS,
            namespace=settings.TEMPORAL_NAMESPACE,
            api_key=settings.TEMPORAL_API_KEY,
        )
    else:
        # Local
        return await Client.connect(
            settings.TEMPORAL_ADDRESS,
            namespace=settings.TEMPORAL_NAMESPACE,
        )
```

---

*이전: [02-data-models.md](./02-data-models.md) | 다음: [04-infrastructure.md](./04-infrastructure.md)*
