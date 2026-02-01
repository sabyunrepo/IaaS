# Checkpoint Manager Skill

> 파이프라인 내구성, LLM 결과 캐싱, 단계별 복구 에이전트

---

## 역할

워크플로우 실행 중 발생하는 실패에 대해 **비용 손실 없이** 복구하고,
사용자가 **원하는 단계부터** 재시작할 수 있도록 중간 결과를 관리한다.

## 해결하는 문제

| 문제 | 영향 | 해결 |
|------|------|------|
| Activity 내부 LLM 호출 실패 시 동일 프롬프트 재호출 | 비용 낭비, 시간 지연 | LLM 결과 캐싱 |
| 긴 Activity(코드 분석) 중간 실패 | 처음부터 재실행 | Activity 내 heartbeat 체크포인트 |
| Phase 3 실패 시 Phase 1~2 재실행 | 불필요한 재계산 | 단계별 결과 스냅샷 |
| 디버깅/테스트 시 특정 단계만 실행 | 전체 파이프라인 실행 필요 | 수동 재시작 지점 지정 |

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    Checkpoint Manager                             │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  LLM Cache      │  │  Step Snapshot   │  │  Resume Engine  │  │
│  │  Layer           │  │  Store           │  │                 │  │
│  │                   │  │                   │  │  • from_step   │  │
│  │  • prompt hash   │  │  • phase results │  │  • skip/replay  │  │
│  │  • result cache  │  │  • Redis + S3    │  │  • signal-based │  │
│  │  • TTL 24h       │  │  • TTL 7d        │  │                 │  │
│  └────────┬──────────┘  └────────┬──────────┘  └────────┬──────┘  │
│           │                      │                      │         │
│           └──────────────────────┼──────────────────────┘         │
│                                  │                                 │
│                          ┌───────▼───────┐                        │
│                          │   Redis       │                        │
│                          │   + S3 backup │                        │
│                          └───────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 책임

1. **LLM 결과 캐싱**: 동일 프롬프트 재호출 방지 (비용 절감)
2. **단계별 스냅샷**: 각 Phase/Activity 완료 시 결과 저장
3. **복구 엔진**: 실패 지점 또는 지정 지점부터 재시작
4. **Activity 내부 체크포인트**: heartbeat 기반 세밀한 진행 추적
5. **캐시 무효화**: 입력 변경 시 관련 캐시 자동 삭제

---

## 구현 상세

### 1. LLM Result Cache

```python
"""
backend/app/services/llm_cache.py
LLM 호출 결과 캐싱 서비스
"""
import hashlib
import json
from datetime import timedelta
from redis.asyncio import Redis


class LLMResultCache:
    """
    LLM 호출 결과를 Redis에 캐싱하여 재시도 시 비용 0으로 만든다.

    캐시 키 구조:
        llm_cache:{model}:{prompt_hash}

    캐시 전략:
        - 동일 (model + messages) → 동일 결과 반환
        - TTL: 24시간 (기본)
        - Job 단위 캐시 무효화 가능
    """

    PREFIX = "llm_cache"
    DEFAULT_TTL = timedelta(hours=24)

    def __init__(self, redis: Redis):
        self.redis = redis

    def _hash_prompt(self, messages: list[dict], model: str) -> str:
        """프롬프트를 해시하여 캐시 키 생성"""
        content = json.dumps(
            {"model": model, "messages": messages},
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def _make_key(self, model: str, prompt_hash: str) -> str:
        return f"{self.PREFIX}:{model}:{prompt_hash}"

    async def get(self, messages: list[dict], model: str) -> dict | None:
        """캐시 조회. 히트 시 LLM 호출 불필요."""
        prompt_hash = self._hash_prompt(messages, model)
        key = self._make_key(model, prompt_hash)

        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set(
        self,
        messages: list[dict],
        model: str,
        result: dict,
        ttl: timedelta | None = None,
    ) -> None:
        """LLM 결과 캐싱"""
        prompt_hash = self._hash_prompt(messages, model)
        key = self._make_key(model, prompt_hash)

        await self.redis.setex(
            key,
            ttl or self.DEFAULT_TTL,
            json.dumps(result, ensure_ascii=False),
        )

    async def invalidate_by_job(self, job_id: str) -> int:
        """특정 Job 관련 캐시 전체 무효화"""
        pattern = f"{self.PREFIX}:*:{job_id}:*"
        keys = []
        async for key in self.redis.scan_iter(pattern):
            keys.append(key)
        if keys:
            return await self.redis.delete(*keys)
        return 0
```

### 2. LLM Service with Cache Integration

```python
"""
backend/app/services/llm_service.py
캐시 통합 LLM 서비스 (기존 llm_service.py 확장)
"""
from app.services.llm_cache import LLMResultCache


class CachedLLMService:
    """
    LLMResultCache를 통합한 LLM 서비스.
    모든 LLM 호출은 이 서비스를 통해야 한다.

    사용법:
        llm = CachedLLMService(openai_client, redis)
        result = await llm.chat(messages, model="gpt-4o")
        # 첫 호출: API 호출 + 캐시 저장
        # 재시도: 캐시에서 즉시 반환 (비용 0)
    """

    def __init__(self, llm_client, redis):
        self.client = llm_client
        self.cache = LLMResultCache(redis)
        self._stats = {"hits": 0, "misses": 0}

    async def chat(
        self,
        messages: list[dict],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        use_cache: bool = True,
        **kwargs,
    ) -> dict:
        """
        캐시 우선 LLM 호출.

        Args:
            messages: LLM 메시지
            model: 모델 ID
            temperature: 0이면 결정적 → 캐시 적중률 높음
            use_cache: False면 캐시 무시 (강제 재생성)

        Returns:
            LLM 응답 dict
        """
        # 캐시 조회
        if use_cache:
            cached = await self.cache.get(messages, model)
            if cached:
                self._stats["hits"] += 1
                return cached

        self._stats["misses"] += 1

        # LLM 호출
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )

        result = {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

        # 캐시 저장
        if use_cache:
            await self.cache.set(messages, model, result)

        return result

    @property
    def cache_stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "hit_rate": self._stats["hits"] / total if total > 0 else 0,
        }
```

### 3. Step Snapshot Store

```python
"""
backend/app/services/checkpoint_store.py
단계별 중간 결과 스냅샷 저장소
"""
import json
from datetime import timedelta
from redis.asyncio import Redis
from app.services.storage import StorageClient


# 파이프라인 단계 정의 (순서 보장)
PIPELINE_STEPS = [
    "plan",
    "document_analysis",
    "code_analysis",
    "jd_analysis",
    "aggregate_analysis",
    "select_topics",
    "craft_questions",
    "review_quality",
    "finalize",
]


class CheckpointStore:
    """
    각 파이프라인 단계의 결과를 저장/복구하는 저장소.

    저장 계층:
        - Redis: 빠른 접근 (TTL 7일)
        - S3: 영구 백업 (선택적)

    키 구조:
        checkpoint:{job_id}:{step_name} → JSON result
        checkpoint:{job_id}:_meta → 체크포인트 메타정보
    """

    PREFIX = "checkpoint"
    DEFAULT_TTL = timedelta(days=7)

    def __init__(self, redis: Redis, storage: StorageClient | None = None):
        self.redis = redis
        self.storage = storage  # S3 백업 (선택)

    def _key(self, job_id: str, step: str) -> str:
        return f"{self.PREFIX}:{job_id}:{step}"

    def _meta_key(self, job_id: str) -> str:
        return f"{self.PREFIX}:{job_id}:_meta"

    async def save_step(
        self,
        job_id: str,
        step: str,
        data: dict,
        backup_to_s3: bool = False,
    ) -> None:
        """
        단계 완료 시 결과 저장.

        Activity 코드에서 사용:
            checkpoint = CheckpointStore(redis)
            result = await do_analysis(...)
            await checkpoint.save_step(job_id, "document_analysis", result)
        """
        serialized = json.dumps(data, ensure_ascii=False, default=str)

        # Redis에 저장
        await self.redis.setex(
            self._key(job_id, step),
            self.DEFAULT_TTL,
            serialized,
        )

        # 메타 업데이트
        await self.redis.hset(
            self._meta_key(job_id),
            step,
            "completed",
        )
        await self.redis.expire(self._meta_key(job_id), self.DEFAULT_TTL)

        # S3 백업 (선택)
        if backup_to_s3 and self.storage:
            await self.storage.upload(
                bucket="vantict-results",
                key=f"checkpoints/{job_id}/{step}.json",
                data=serialized.encode(),
                content_type="application/json",
            )

    async def load_step(self, job_id: str, step: str) -> dict | None:
        """
        저장된 단계 결과 로드.
        Redis 미스 시 S3에서 복구 시도.
        """
        # Redis에서 조회
        cached = await self.redis.get(self._key(job_id, step))
        if cached:
            return json.loads(cached)

        # S3 폴백
        if self.storage:
            try:
                data = await self.storage.download(
                    bucket="vantict-results",
                    key=f"checkpoints/{job_id}/{step}.json",
                )
                if data:
                    result = json.loads(data)
                    # Redis에 다시 캐시
                    await self.redis.setex(
                        self._key(job_id, step),
                        self.DEFAULT_TTL,
                        data,
                    )
                    return result
            except Exception:
                pass

        return None

    async def get_completed_steps(self, job_id: str) -> list[str]:
        """완료된 단계 목록 반환 (순서 보장)"""
        meta = await self.redis.hgetall(self._meta_key(job_id))
        if not meta:
            return []

        completed = [
            step for step in PIPELINE_STEPS
            if meta.get(step) == "completed" or meta.get(step.encode()) == b"completed"
        ]
        return completed

    async def get_resume_point(self, job_id: str) -> str | None:
        """
        재시작 지점 자동 감지.
        마지막으로 완료된 단계의 다음 단계를 반환.
        """
        completed = await self.get_completed_steps(job_id)
        if not completed:
            return PIPELINE_STEPS[0]

        last_completed = completed[-1]
        last_idx = PIPELINE_STEPS.index(last_completed)

        if last_idx + 1 < len(PIPELINE_STEPS):
            return PIPELINE_STEPS[last_idx + 1]

        return None  # 모든 단계 완료

    async def clear_job(self, job_id: str) -> None:
        """Job의 모든 체크포인트 삭제"""
        keys = [self._key(job_id, step) for step in PIPELINE_STEPS]
        keys.append(self._meta_key(job_id))
        await self.redis.delete(*keys)
```

### 4. Resume-Enabled Workflow

```python
"""
backend/app/workflows/interview_workflow.py
체크포인트/복구 통합 워크플로우 (기존 워크플로우 확장)

변경사항:
    - resume_from 시그널 추가
    - 각 Phase 완료 시 체크포인트 저장
    - 재시작 시 이전 결과 캐시에서 로드
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.activities import (
        planning, document_analysis, code_analysis,
        jd_analysis, question_generation, quality_review,
        finalization, checkpoint_activities,
    )


@workflow.defn
class InterviewGenerationWorkflow:
    """
    면접 질문 생성 워크플로우 (체크포인트 지원)

    신규 기능:
        - resume_from 시그널: 특정 단계부터 재시작
        - 단계별 자동 체크포인트
        - LLM 캐시 통합 (Activity 내부)
    """

    def __init__(self) -> None:
        self._current_phase = "initialized"
        self._progress = 0
        self._resume_from: str | None = None

    @workflow.signal
    def set_resume_from(self, step: str) -> None:
        """재시작 지점 설정 시그널"""
        self._resume_from = step

    @workflow.run
    async def run(self, job_id: str, input_data: dict) -> dict:
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
            non_retryable_error_types=["ValueError", "ValidationError"],
        )
        long_timeout = timedelta(minutes=10)
        short_timeout = timedelta(minutes=2)

        # 재시작 지점 결정
        resume_from = self._resume_from
        if resume_from:
            # 체크포인트에서 이전 결과 로드
            prior_state = await workflow.execute_activity(
                checkpoint_activities.load_prior_state,
                args=[job_id, resume_from],
                start_to_close_timeout=short_timeout,
            )
        else:
            prior_state = {}

        # ================================================================
        # Phase 1: PLANNING
        # ================================================================
        if self._should_run("plan", resume_from):
            self._current_phase = "planning"
            self._progress = 5

            execution_plan = await workflow.execute_activity(
                planning.create_execution_plan,
                args=[job_id, input_data],
                start_to_close_timeout=short_timeout,
                retry_policy=retry_policy,
            )

            # 체크포인트 저장
            await workflow.execute_activity(
                checkpoint_activities.save_checkpoint,
                args=[job_id, "plan", execution_plan],
                start_to_close_timeout=short_timeout,
            )
        else:
            execution_plan = prior_state.get("plan", {})

        # ================================================================
        # Phase 2: PARALLEL ANALYSIS
        # ================================================================
        if self._should_run("document_analysis", resume_from):
            self._current_phase = "analyzing"
            self._progress = 10

            analysis_tasks = []

            # Document Analysis
            if input_data.get("resume_path") or input_data.get("portfolio_path"):
                analysis_tasks.append(
                    workflow.execute_activity(
                        document_analysis.analyze_documents,
                        args=[job_id, input_data],
                        start_to_close_timeout=long_timeout,
                        retry_policy=retry_policy,
                        heartbeat_timeout=timedelta(minutes=2),
                    )
                )
            else:
                analysis_tasks.append(self._empty_doc_result())

            # Code Analysis
            if input_data.get("github_urls"):
                analysis_tasks.append(
                    workflow.execute_activity(
                        code_analysis.analyze_code,
                        args=[job_id, input_data["github_urls"]],
                        start_to_close_timeout=long_timeout,
                        retry_policy=retry_policy,
                        heartbeat_timeout=timedelta(minutes=2),
                    )
                )
            else:
                analysis_tasks.append(self._empty_code_result())

            # JD Analysis
            analysis_tasks.append(
                workflow.execute_activity(
                    jd_analysis.analyze_jd,
                    args=[job_id, input_data["jd_text"]],
                    start_to_close_timeout=short_timeout,
                    retry_policy=retry_policy,
                )
            )

            analysis_results = await workflow.wait_all(analysis_tasks)
            self._progress = 40

            aggregated = {
                "document_analysis": analysis_results[0],
                "code_analysis": analysis_results[1],
                "jd_analysis": analysis_results[2],
            }

            # 체크포인트 저장
            await workflow.execute_activity(
                checkpoint_activities.save_checkpoint,
                args=[job_id, "aggregate_analysis", aggregated],
                start_to_close_timeout=short_timeout,
            )
        else:
            aggregated = prior_state.get("aggregate_analysis", {})

        # ================================================================
        # Phase 3: QUESTION GENERATION
        # ================================================================
        if self._should_run("select_topics", resume_from):
            self._current_phase = "generating"
            self._progress = 45

            selected_topics = await workflow.execute_activity(
                question_generation.select_topics,
                args=[job_id, aggregated, input_data],
                start_to_close_timeout=short_timeout,
                retry_policy=retry_policy,
            )

            await workflow.execute_activity(
                checkpoint_activities.save_checkpoint,
                args=[job_id, "select_topics", selected_topics],
                start_to_close_timeout=short_timeout,
            )
        else:
            selected_topics = prior_state.get("select_topics", [])

        if self._should_run("craft_questions", resume_from):
            self._progress = 50

            question_tasks = [
                workflow.execute_activity(
                    question_generation.craft_question,
                    args=[job_id, topic, aggregated, input_data],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=retry_policy,
                )
                for topic in selected_topics
            ]

            questions = await workflow.wait_all(question_tasks)
            self._progress = 70

            await workflow.execute_activity(
                checkpoint_activities.save_checkpoint,
                args=[job_id, "craft_questions", questions],
                start_to_close_timeout=short_timeout,
            )
        else:
            questions = prior_state.get("craft_questions", [])

        # Review loop
        if self._should_run("review_quality", resume_from):
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

                questions = await workflow.execute_activity(
                    question_generation.revise_questions,
                    args=[job_id, questions, review_result["feedback"]],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                revision_count += 1

            await workflow.execute_activity(
                checkpoint_activities.save_checkpoint,
                args=[job_id, "review_quality", questions],
                start_to_close_timeout=short_timeout,
            )

        self._progress = 85

        # ================================================================
        # Phase 4: FINALIZATION
        # ================================================================
        if self._should_run("finalize", resume_from):
            self._current_phase = "finalizing"

            final_output = await workflow.execute_activity(
                finalization.finalize_output,
                args=[job_id, questions, aggregated, input_data],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            await workflow.execute_activity(
                checkpoint_activities.save_checkpoint,
                args=[job_id, "finalize", final_output],
                start_to_close_timeout=short_timeout,
            )
        else:
            final_output = prior_state.get("finalize", {})

        self._current_phase = "completed"
        self._progress = 100
        return final_output

    def _should_run(self, step: str, resume_from: str | None) -> bool:
        """이 단계를 실행해야 하는지 판단"""
        if resume_from is None:
            return True  # 처음부터 실행

        step_idx = PIPELINE_STEPS.index(step) if step in PIPELINE_STEPS else -1
        resume_idx = PIPELINE_STEPS.index(resume_from) if resume_from in PIPELINE_STEPS else 0

        return step_idx >= resume_idx

    async def _empty_doc_result(self):
        return {"name": "Unknown", "experience_years": 0, "skills": [], "education": [], "work_history": [], "projects": [], "summary": "문서가 제공되지 않았습니다."}

    async def _empty_code_result(self):
        return {"repositories": [], "combined_tech_stack": [], "total_patterns": 0, "total_notable_implementations": 0, "top_question_candidates": []}

    @workflow.query
    def get_progress(self) -> dict:
        return {"phase": self._current_phase, "progress": self._progress}

    @workflow.signal
    def cancel_workflow(self) -> None:
        self._current_phase = "cancelled"
        raise workflow.CancelledError("Workflow cancelled by user")


# 파이프라인 단계 정의 (checkpoint_store.py와 동기화)
PIPELINE_STEPS = [
    "plan", "document_analysis", "code_analysis", "jd_analysis",
    "aggregate_analysis", "select_topics", "craft_questions",
    "review_quality", "finalize",
]
```

### 5. Checkpoint Activities

```python
"""
backend/app/workflows/activities/checkpoint_activities.py
체크포인트 관련 Activity 정의
"""
from temporalio import activity
from app.services.checkpoint_store import CheckpointStore, PIPELINE_STEPS


@activity.defn
async def save_checkpoint(job_id: str, step: str, data: dict) -> None:
    """단계 완료 시 결과 저장"""
    from app.core.deps import get_redis, get_storage

    redis = get_redis()
    storage = get_storage()

    store = CheckpointStore(redis, storage)
    await store.save_step(job_id, step, data, backup_to_s3=True)

    activity.logger.info(f"Checkpoint saved: job={job_id} step={step}")


@activity.defn
async def load_prior_state(job_id: str, resume_from: str) -> dict:
    """
    재시작 시 이전 단계 결과를 모두 로드.

    resume_from 이전의 모든 완료된 단계 결과를 dict로 반환.

    Returns:
        {
            "plan": {...},
            "aggregate_analysis": {...},
            "select_topics": [...],
            ...
        }
    """
    from app.core.deps import get_redis, get_storage

    redis = get_redis()
    storage = get_storage()

    store = CheckpointStore(redis, storage)

    state = {}
    resume_idx = PIPELINE_STEPS.index(resume_from)

    for step in PIPELINE_STEPS[:resume_idx]:
        data = await store.load_step(job_id, step)
        if data:
            state[step] = data
            activity.logger.info(f"Loaded checkpoint: job={job_id} step={step}")
        else:
            activity.logger.warning(
                f"Missing checkpoint: job={job_id} step={step}. "
                f"Will re-run from earlier step."
            )
            # 체크포인트 누락 시 더 앞에서 재시작
            break

    return state


@activity.defn
async def get_checkpoint_status(job_id: str) -> dict:
    """
    Job의 체크포인트 상태 조회.

    Returns:
        {
            "job_id": str,
            "completed_steps": ["plan", "document_analysis", ...],
            "resume_point": "select_topics",
            "total_steps": 9,
            "completed_count": 4,
        }
    """
    from app.core.deps import get_redis

    redis = get_redis()
    store = CheckpointStore(redis)

    completed = await store.get_completed_steps(job_id)
    resume_point = await store.get_resume_point(job_id)

    return {
        "job_id": job_id,
        "completed_steps": completed,
        "resume_point": resume_point,
        "total_steps": len(PIPELINE_STEPS),
        "completed_count": len(completed),
    }
```

### 6. Activity Heartbeat 패턴 (기존 Activity 개선)

```python
"""
Activity 내부 heartbeat 체크포인트 패턴.
긴 Activity (코드 분석 등)에서 중간 진행을 저장한다.

기존 코드에서 변경이 필요한 패턴:
"""

# === BEFORE (기존) ===
@activity.defn
async def analyze_code(job_id: str, github_urls: list[str]) -> dict:
    repositories = []
    for i, url in enumerate(github_urls):
        activity.heartbeat(f"Analyzing repo {i+1}/{len(github_urls)}")
        result = await _analyze_single_repo(url, job_id)
        repositories.append(result)
    return aggregate_code_analysis(repositories)


# === AFTER (개선) ===
@activity.defn
async def analyze_code(job_id: str, github_urls: list[str]) -> dict:
    """
    GitHub 코드 분석 (heartbeat 체크포인트 지원)

    실패 복구:
        - heartbeat에 완료된 인덱스 저장
        - 재시도 시 activity.info().heartbeat_details로 복구
        - 이미 분석한 레포는 건너뜀
    """
    repositories = []

    # 이전 heartbeat에서 저장된 진행상황 복구
    heartbeat_details = activity.info().heartbeat_details
    start_index = 0
    if heartbeat_details:
        start_index = heartbeat_details[0]  # 완료된 repo 수
        repositories = heartbeat_details[1]  # 이전 결과

    for i in range(start_index, len(github_urls)):
        url = github_urls[i]

        result = await _analyze_single_repo(url, job_id)
        repositories.append(result)

        # 진행상황을 heartbeat에 저장
        # → 실패 시 이 지점부터 재개
        activity.heartbeat(i + 1, repositories)

    return aggregate_code_analysis(repositories)
```

---

## API 엔드포인트 (신규)

### Retry from Step

```http
POST /api/v1/jobs/{job_id}/retry
```

```python
"""
backend/app/api/v1/jobs.py (추가)
"""

@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    from_step: str | None = None,
    api_key: str = Depends(verify_api_key),
    temporal: Client = Depends(get_temporal_client),
    redis: Redis = Depends(get_redis),
):
    """
    실패한 작업을 특정 단계부터 재시작.

    Args:
        job_id: 작업 ID
        from_step: 재시작 지점 (null이면 자동 감지)
            - plan, document_analysis, code_analysis, jd_analysis
            - aggregate_analysis, select_topics, craft_questions
            - review_quality, finalize

    Returns:
        {
            "job_id": str,
            "status": "retrying",
            "resume_from": str,
            "skipped_steps": list[str],
        }
    """
    store = CheckpointStore(redis)

    if from_step is None:
        from_step = await store.get_resume_point(job_id)

    if from_step is None:
        raise HTTPException(400, "No checkpoint found and no step specified")

    if from_step not in PIPELINE_STEPS:
        raise HTTPException(400, f"Invalid step: {from_step}. Valid: {PIPELINE_STEPS}")

    # 기존 워크플로우에 시그널 전송
    handle = temporal.get_workflow_handle(f"interview-{job_id}")

    try:
        await handle.signal("set_resume_from", from_step)
    except Exception:
        # 워크플로우가 종료된 경우 새로 시작
        original_input = await redis.get(f"job:{job_id}:input")
        if not original_input:
            raise HTTPException(404, "Original input not found")

        await temporal.start_workflow(
            InterviewGenerationWorkflow.run,
            args=[job_id, json.loads(original_input)],
            id=f"interview-{job_id}-retry",
            task_queue="interview-generation",
        )

    completed = await store.get_completed_steps(job_id)
    step_idx = PIPELINE_STEPS.index(from_step)
    skipped = PIPELINE_STEPS[:step_idx]

    return {
        "job_id": job_id,
        "status": "retrying",
        "resume_from": from_step,
        "skipped_steps": [s for s in skipped if s in completed],
        "cached_steps": completed,
    }


@router.get("/{job_id}/checkpoints")
async def get_checkpoints(
    job_id: str,
    api_key: str = Depends(verify_api_key),
    redis: Redis = Depends(get_redis),
):
    """
    Job의 체크포인트 상태 조회.

    Returns:
        {
            "job_id": str,
            "completed_steps": list,
            "resume_point": str | null,
            "total_steps": int,
        }
    """
    store = CheckpointStore(redis)
    completed = await store.get_completed_steps(job_id)
    resume = await store.get_resume_point(job_id)

    return {
        "job_id": job_id,
        "steps": [
            {
                "name": step,
                "status": "completed" if step in completed else "pending",
            }
            for step in PIPELINE_STEPS
        ],
        "resume_point": resume,
        "total_steps": len(PIPELINE_STEPS),
        "completed_count": len(completed),
    }
```

---

## Redis 키 구조 (추가)

```
# LLM 결과 캐시
llm_cache:{model}:{prompt_hash} → JSON (TTL 24h)

# 단계별 체크포인트
checkpoint:{job_id}:{step_name} → JSON (TTL 7d)
checkpoint:{job_id}:_meta → Hash { step: "completed" }

# 원본 입력 (재시작용)
job:{job_id}:input → JSON (TTL 7d)
```

## S3 저장 구조 (추가)

```
s3://vantict-results/
├── checkpoints/
│   └── {job_id}/
│       ├── plan.json
│       ├── aggregate_analysis.json
│       ├── select_topics.json
│       ├── craft_questions.json
│       ├── review_quality.json
│       └── finalize.json
```

---

## 의존성

| 구성요소 | 의존 대상 | 용도 |
|----------|----------|------|
| LLMResultCache | Redis | 프롬프트-결과 캐싱 |
| CheckpointStore | Redis + S3 | 단계별 스냅샷 |
| CachedLLMService | LLMResultCache + OpenAI/Anthropic | 통합 LLM 호출 |
| checkpoint_activities | CheckpointStore | Temporal Activity |
| Workflow | checkpoint_activities | 체크포인트 저장/로드 |
| API retry endpoint | CheckpointStore + Temporal Client | 수동 재시작 |

---

## 관련 파일

```
backend/app/
├── services/
│   ├── llm_cache.py              # LLM 결과 캐시
│   ├── llm_service.py            # 캐시 통합 LLM 서비스 (수정)
│   └── checkpoint_store.py       # 단계별 스냅샷 저장소
├── workflows/
│   ├── interview_workflow.py     # 체크포인트 통합 워크플로우 (수정)
│   └── activities/
│       └── checkpoint_activities.py  # 체크포인트 Activity (신규)
└── api/
    └── v1/
        └── jobs.py               # retry, checkpoints 엔드포인트 (추가)
```

---

## 구현 우선순위

| 순서 | 항목 | 효과 | 난이도 |
|------|------|------|--------|
| 1 | Activity heartbeat 개선 | 긴 Activity 중간 복구 | 낮음 |
| 2 | LLMResultCache | 재시도 비용 0 | 낮음 |
| 3 | CheckpointStore | 단계별 스냅샷 | 중간 |
| 4 | Workflow resume_from | 수동 재시작 | 중간 |
| 5 | Retry API 엔드포인트 | 사용자 재시작 인터페이스 | 낮음 |
| 6 | S3 백업 | 영구 체크포인트 보존 | 낮음 |
