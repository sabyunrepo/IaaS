---
name: temporal-dev
description: Temporal 워크플로우/Activity 개발. workflow, activity, temporal, worker, signal, query, heartbeat, retry, checkpoint 관련 작업 시 사용.
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Temporal Development Skill

Temporal 워크플로우 및 Activity 개발 시 반드시 따라야 할 패턴과 규칙입니다.

## 필수 규칙

1. **Activity**: 반드시 `@activity.defn` 데코레이터 사용
2. **Heartbeat**: 30초 이상 Activity는 `activity.heartbeat()` 필수
3. **LLM 호출**: `CachedLLMService` 사용 (Redis 캐시, 직접 API 호출 금지)
4. **Checkpoint**: 각 Phase 완료 시 checkpoint 저장
5. **등록**: 새 Activity는 `worker.py`에 반드시 등록
6. **멱등성**: 같은 입력 → 같은 출력 보장
7. **에러 분류**: `RetryableError` vs `NonRetryableError` 구분

## 파일 배치
- 새 Activity: `backend/app/workflows/activities/`
- 새 Workflow: `backend/app/workflows/`
- 서비스: `backend/app/services/`

## 9단계 파이프라인
1. plan → 2~4. document/code/jd 분석 (병렬) → 5. 집계 → 6. 주제 선택 → 7. 질문 생성 (10개 병렬) → 8. 품질 검토 (최대 3회) → 9. 최종화

Step 2~4는 `workflow.wait_all()`로 병렬 실행.

## 참고 문서
- `docs/architecture/03-workflow.md` — 워크플로우 상세
- `docs/architecture/02-data-models.md` — 데이터 모델
- `docs/architecture/skills/checkpoint-manager/SKILL.md` — 체크포인트 패턴
- `docs/architecture/skills/common-tools/SKILL.md` — 공통 인프라

## Activity 템플릿
```python
from temporalio import activity
from app.services.cached_llm import CachedLLMService
from app.common.errors import RetryableError, NonRetryableError

@activity.defn
async def my_activity(input: MyInput) -> MyOutput:
    activity.heartbeat("starting")
    try:
        llm = CachedLLMService()
        result = await llm.generate(prompt)
        activity.heartbeat("completed")
        return MyOutput(data=result)
    except APIError as e:
        raise RetryableError(str(e))
    except ValueError as e:
        raise NonRetryableError(str(e))
```
