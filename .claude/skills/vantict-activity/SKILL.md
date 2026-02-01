---
name: vantict-activity
description: Activity 보일러플레이트 생성. 새 Activity를 만들거나 Activity 템플릿이 필요할 때 사용.
argument-hint: [activity_name] [description]
allowed-tools: Read, Grep, Write, Edit, Glob
---

# Vantict Activity Generator

새 Temporal Activity 보일러플레이트를 생성합니다.

## 생성 절차

1. `docs/architecture/03-workflow.md` 읽어서 현재 파이프라인 구조 확인
2. `docs/architecture/skills/common-tools/SKILL.md` 읽어서 공통 패턴 확인
3. Activity 파일 생성: `backend/app/workflows/activities/{name}.py`
4. `backend/app/workflows/worker.py`에 Activity 등록

## 필수 포함 요소

- `@activity.defn` 데코레이터
- 입력/출력 dataclass 정의
- heartbeat (30초 이상 작업 시)
- 에러 핸들링 (RetryableError / NonRetryableError)
- CachedLLMService (LLM 호출 시)
- ActivityLogger 사용
- S3 저장소 연동 (필요 시)

## 네이밍
- 함수명: `snake_case` (예: `analyze_documents`, `craft_question`)
- 입력 클래스: `{Name}Input`
- 출력 클래스: `{Name}Output`

## 참고
- `docs/architecture/03-workflow.md`
- `docs/architecture/skills/common-tools/SKILL.md`
