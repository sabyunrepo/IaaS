# Supervisor Skill

> 워크플로우 조율 및 품질 관리 에이전트

---

## 역할

전체 워크플로우를 조율하고, 최종 결과물의 품질을 검증합니다.

## 책임

1. **워크플로우 조율**: 각 Phase 실행 순서 및 병렬화 관리
2. **상태 추적**: 작업 진행 상황 모니터링
3. **에러 복구**: 실패 시 재시도 또는 대체 전략 실행
4. **품질 검증**: 최종 결과물 품질 검사
5. **결과 집계**: 모든 분석 결과를 통합하여 최종 출력 생성

---

## Activity 정의

### supervise_workflow

```python
@activity.defn
async def supervise_workflow(job_id: str, plan: dict) -> dict:
    """
    워크플로우 감독 및 실행

    Input:
        job_id: 작업 ID
        plan: ExecutionPlan (Planner 출력)

    Output:
        WorkflowResult: {
            job_id: str,
            status: "completed" | "partial" | "failed",
            phases_completed: list[str],
            phases_failed: list[str],
            execution_time_seconds: int,
            errors: list[dict],
        }
    """
```

### validate_output

```python
@activity.defn
async def validate_output(job_id: str, questions: list[dict]) -> dict:
    """
    최종 출력 품질 검증

    Input:
        job_id: 작업 ID
        questions: 생성된 질문 목록

    Output:
        ValidationResult: {
            is_valid: bool,
            quality_score: float,
            issues: list[str],
            suggestions: list[str],
        }
    """
```

---

## 워크플로우 상태 관리

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class JobStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    PLANNING = "planning"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class PhaseStatus(Enum):
    """Phase 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class JobState:
    """작업 상태 추적"""
    job_id: str
    status: JobStatus
    current_phase: str | None
    phases: dict[str, PhaseStatus]
    started_at: datetime
    updated_at: datetime
    errors: list[dict]
    progress_percent: int


class StateManager:
    """상태 관리자"""

    def __init__(self, job_id: str, redis_client):
        self.job_id = job_id
        self.redis = redis_client
        self.key = f"job:{job_id}:state"

    async def initialize(self, phases: list[str]) -> JobState:
        """상태 초기화"""
        state = JobState(
            job_id=self.job_id,
            status=JobStatus.PENDING,
            current_phase=None,
            phases={p: PhaseStatus.PENDING for p in phases},
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            errors=[],
            progress_percent=0,
        )
        await self._save(state)
        return state

    async def update_phase(
        self,
        phase: str,
        status: PhaseStatus,
        error: dict | None = None,
    ) -> JobState:
        """Phase 상태 업데이트"""
        state = await self._load()
        state.phases[phase] = status
        state.updated_at = datetime.utcnow()

        if status == PhaseStatus.RUNNING:
            state.current_phase = phase
        elif status == PhaseStatus.FAILED and error:
            state.errors.append(error)

        # 진행률 계산
        completed = sum(
            1 for s in state.phases.values()
            if s in [PhaseStatus.COMPLETED, PhaseStatus.SKIPPED]
        )
        state.progress_percent = int(completed / len(state.phases) * 100)

        await self._save(state)
        return state

    async def _save(self, state: JobState) -> None:
        """Redis에 상태 저장"""
        await self.redis.hset(
            self.key,
            mapping={
                "status": state.status.value,
                "current_phase": state.current_phase or "",
                "phases": json.dumps({k: v.value for k, v in state.phases.items()}),
                "progress_percent": state.progress_percent,
                "errors": json.dumps(state.errors),
                "updated_at": state.updated_at.isoformat(),
            }
        )
        # 이벤트 발행 (실시간 업데이트용)
        await self.redis.publish(
            f"job:{self.job_id}:updates",
            json.dumps({"progress": state.progress_percent}),
        )
```

---

## 에러 복구 전략

```python
from typing import Callable, Any
import asyncio

class RetryStrategy:
    """재시도 전략"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """재시도 로직으로 함수 실행"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except RetryableError as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay,
                    )
                    await asyncio.sleep(delay)
            except NonRetryableError:
                raise

        raise last_error


# 재시도 가능한 에러 정의
class RetryableError(Exception):
    """재시도 가능한 에러"""
    pass

class NonRetryableError(Exception):
    """재시도 불가능한 에러"""
    pass

# 에러 분류
ERROR_CLASSIFICATION = {
    "RateLimitError": RetryableError,
    "TimeoutError": RetryableError,
    "ConnectionError": RetryableError,
    "ValidationError": NonRetryableError,
    "AuthenticationError": NonRetryableError,
    "InvalidInputError": NonRetryableError,
}


async def execute_phase_with_recovery(
    phase_name: str,
    phase_func: Callable,
    fallback_func: Callable | None = None,
    *args,
    **kwargs,
) -> dict:
    """
    Phase 실행 (복구 전략 포함)

    전략:
    1. 기본 실행 시도
    2. 실패 시 재시도 (RetryableError인 경우)
    3. 재시도 실패 시 fallback 실행
    4. fallback도 실패하면 에러 반환
    """
    retry = RetryStrategy(max_retries=3)

    try:
        return await retry.execute(phase_func, *args, **kwargs)
    except Exception as e:
        if fallback_func:
            try:
                return await fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                return {
                    "status": "failed",
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                }
        return {
            "status": "failed",
            "error": str(e),
        }
```

---

## 품질 검증

```python
@dataclass
class QualityMetrics:
    """품질 메트릭"""
    coverage_score: float  # 요구사항 커버리지
    diversity_score: float  # 질문 다양성
    difficulty_balance: float  # 난이도 균형
    evidence_quality: float  # 근거 품질
    answer_quality: float  # 예상 답변 품질

    @property
    def overall_score(self) -> float:
        """종합 점수"""
        weights = {
            "coverage": 0.25,
            "diversity": 0.20,
            "difficulty": 0.15,
            "evidence": 0.20,
            "answer": 0.20,
        }
        return (
            self.coverage_score * weights["coverage"] +
            self.diversity_score * weights["diversity"] +
            self.difficulty_balance * weights["difficulty"] +
            self.evidence_quality * weights["evidence"] +
            self.answer_quality * weights["answer"]
        )


async def validate_questions(
    questions: list[dict],
    jd_analysis: dict,
    config: dict,
) -> dict:
    """
    생성된 질문 품질 검증

    검증 항목:
    1. 요구사항 커버리지 (JD의 필수 스킬이 질문에 포함되었는가)
    2. 질문 다양성 (카테고리, 소스 분포)
    3. 난이도 균형 (경험 레벨에 맞는 분포)
    4. 근거 품질 (각 질문에 명확한 근거가 있는가)
    5. 예상 답변 품질 (평가 기준이 명확한가)
    """
    metrics = QualityMetrics(
        coverage_score=calculate_coverage(questions, jd_analysis),
        diversity_score=calculate_diversity(questions),
        difficulty_balance=calculate_difficulty_balance(questions, config),
        evidence_quality=calculate_evidence_quality(questions),
        answer_quality=calculate_answer_quality(questions),
    )

    issues = []
    suggestions = []

    # 커버리지 체크
    if metrics.coverage_score < 0.6:
        issues.append("필수 기술 커버리지가 낮습니다")
        suggestions.append("JD의 필수 기술에 대한 질문을 추가하세요")

    # 다양성 체크
    if metrics.diversity_score < 0.5:
        issues.append("질문 유형이 단조롭습니다")
        suggestions.append("다양한 카테고리의 질문을 추가하세요")

    # 난이도 체크
    if metrics.difficulty_balance < 0.6:
        issues.append("난이도 분포가 불균형합니다")
        suggestions.append("경험 레벨에 맞게 난이도를 조정하세요")

    return {
        "is_valid": metrics.overall_score >= 0.7 and len(issues) == 0,
        "quality_score": metrics.overall_score,
        "metrics": {
            "coverage": metrics.coverage_score,
            "diversity": metrics.diversity_score,
            "difficulty_balance": metrics.difficulty_balance,
            "evidence_quality": metrics.evidence_quality,
            "answer_quality": metrics.answer_quality,
        },
        "issues": issues,
        "suggestions": suggestions,
    }


def calculate_coverage(questions: list[dict], jd_analysis: dict) -> float:
    """요구사항 커버리지 계산"""
    required_skills = set(jd_analysis.get("required_skills", []))
    if not required_skills:
        return 1.0

    covered_skills = set()
    for q in questions:
        # 질문에서 언급된 스킬 추출
        for skill in required_skills:
            if skill.lower() in q.get("question_text", "").lower():
                covered_skills.add(skill)
            if skill.lower() in str(q.get("terminology_hints", [])).lower():
                covered_skills.add(skill)

    return len(covered_skills) / len(required_skills)


def calculate_diversity(questions: list[dict]) -> float:
    """질문 다양성 계산"""
    if not questions:
        return 0.0

    categories = set(q.get("category") for q in questions)
    sources = set(q.get("source") for q in questions)

    # 카테고리 다양성 (최소 3개 이상)
    category_score = min(len(categories) / 3, 1.0)

    # 소스 다양성 (code, resume, jd 등)
    source_score = min(len(sources) / 3, 1.0)

    return (category_score + source_score) / 2


def calculate_difficulty_balance(questions: list[dict], config: dict) -> float:
    """난이도 균형 계산"""
    from collections import Counter

    experience_level = config.get("experience_level", "미들")
    target = EXPERIENCE_LEVEL_CONFIG[experience_level]["difficulty_distribution"]

    actual = Counter(q.get("difficulty") for q in questions)
    total = len(questions)

    if total == 0:
        return 0.0

    actual_dist = {d: actual.get(d, 0) / total for d in target}

    # 목표 분포와의 차이 계산
    diff = sum(abs(target[d] - actual_dist.get(d, 0)) for d in target)
    # 차이가 0이면 1.0, 차이가 클수록 점수 낮아짐
    return max(0, 1 - diff / 2)
```

---

## 결과 집계

```python
async def aggregate_results(
    job_id: str,
    profile: dict,
    code_analysis: dict,
    jd_analysis: dict,
    questions: list[dict],
    validation: dict,
) -> dict:
    """
    모든 분석 결과를 최종 출력으로 집계

    Output:
        {
            job_id: str,
            candidate: {
                name: str,
                summary: str,
                skills: list[str],
            },
            position: str,
            questions: list[InterviewQuestion],
            interview_script: str,
            metadata: {
                generated_at: str,
                quality_score: float,
                sources_used: list[str],
            },
        }
    """
    return {
        "job_id": job_id,
        "candidate": {
            "name": profile.get("name", "Unknown"),
            "summary": profile.get("summary", ""),
            "skills": profile.get("skills", []),
            "experience_years": profile.get("experience_years", 0),
        },
        "position": jd_analysis.get("position", ""),
        "questions": questions,
        "interview_script": format_final_script(
            questions,
            jd_analysis.get("terminology", []),
            profile,
        ),
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "quality_score": validation.get("quality_score", 0),
            "sources_used": get_sources_used(profile, code_analysis),
            "total_questions": len(questions),
            "categories": get_category_counts(questions),
            "avg_difficulty": get_avg_difficulty(questions),
        },
    }


def get_sources_used(profile: dict, code_analysis: dict) -> list[str]:
    """사용된 소스 목록"""
    sources = []

    if profile.get("source_files"):
        sources.extend(profile["source_files"])

    for repo in code_analysis.get("repositories", []):
        sources.append(repo.get("repo_url", ""))

    return sources
```

---

## 출력 예시

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "phases_completed": [
    "planning",
    "document_analysis",
    "code_analysis",
    "jd_analysis",
    "question_generation",
    "validation"
  ],
  "phases_failed": [],
  "execution_time_seconds": 145,
  "quality_score": 0.87,
  "candidate": {
    "name": "김개발",
    "summary": "5년차 백엔드 개발자",
    "skills": ["Python", "FastAPI", "PostgreSQL"]
  },
  "questions_count": 10,
  "errors": []
}
```

---

## 관련 파일

- `backend/app/workflows/interview_workflow.py`
- `backend/app/services/supervisor.py`
- `backend/app/services/quality_validator.py`

---

## Checkpoint Manager 연동

Supervisor는 Checkpoint Manager와 연동하여 내구성을 보장합니다.

### 연동 포인트

```python
"""
Supervisor → Checkpoint Manager 연동 패턴

1. Phase 완료 시 체크포인트 저장 요청
2. 실패 복구 시 체크포인트에서 이전 결과 로드
3. 품질 검증 실패 시 review_quality 단계만 재실행
"""

async def execute_phase_with_checkpoint(
    phase_name: str,
    phase_func: Callable,
    job_id: str,
    checkpoint_store: CheckpointStore,
    *args,
    **kwargs,
) -> dict:
    """체크포인트 통합 Phase 실행"""

    # 1. 기존 체크포인트 확인
    cached = await checkpoint_store.load_step(job_id, phase_name)
    if cached:
        return cached  # 캐시 히트 → 재실행 불필요

    # 2. Phase 실행 (복구 전략 포함)
    result = await execute_phase_with_recovery(
        phase_name, phase_func, *args, **kwargs
    )

    # 3. 성공 시 체크포인트 저장
    if result.get("status") != "failed":
        await checkpoint_store.save_step(
            job_id, phase_name, result, backup_to_s3=True
        )

    return result
```

### LLM 서비스 의존성 변경

모든 Activity는 `CachedLLMService`를 사용해야 합니다:

```python
# BEFORE (직접 호출)
llm = get_llm_client()
result = await llm.chat(messages)

# AFTER (캐시 통합)
from app.services.llm_service import CachedLLMService
llm = CachedLLMService(openai_client, redis)
result = await llm.chat(messages)  # 캐시 히트 시 비용 0
```

---

## 의존성

- **외부 서비스**: Redis (상태 관리), LLM (품질 검증)
- **내부 서비스**: 모든 Analysis Phase, Checkpoint Manager
- **역할**: 워크플로우 오케스트레이터
- **참조**: [checkpoint-manager/SKILL.md](../checkpoint-manager/SKILL.md)
