---
name: arch-data
description: 데이터 모델 구현. Pydantic 모델, DB 스키마, PostgreSQL, pgvector, 마이그레이션 관련 구현 시 사용.
argument-hint: [model] (예: job, question, analysis, input)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Data Models Architecture Skill

Pydantic 모델 + PostgreSQL 스키마 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/02-data-models.md` — 전체 데이터 모델 정의 (50+ 모델)
2. `docs/architecture/06-output-spec.md` — 최종 출력 구조 (InterviewScript)

## 모델 계층 구조

```
InputData (Raw)
  → EnrichedInput (Phase 0: 교차 추출 후)
    → CandidateProfile (문서 분석)
    → CodeAnalysis (코드 분석)
    → JDAnalysis (JD 분석)
      → QuestionGenerationState (질문 생성 상태)
        → InterviewScript (최종 출력)
```

## 핵심 모델

### InputData → EnrichedInput
- Raw 입력을 Phase 0에서 교차 추출하여 보강
- LinkedIn URL, GitHub URLs 자동 발견 및 통합

### InterviewQuestion (핵심)
```python
class InterviewQuestion(BaseModel):
    id: str
    category: QuestionCategory  # role_fit, technical, execution, communication, risk_flags
    difficulty: Difficulty       # easy, medium, hard
    main_question: str
    alternative_phrasings: list[str]
    follow_up_questions: list[FollowUpQuestion]  # expert/mid/low trigger
    evaluation_scenarios: list[EvaluationScenario]
    keywords: list[Keyword]     # must / good_to_have
    terminology: list[Terminology]  # plain_language_explanation
    code_reference: CodeReference | None  # GitHub permalink 필수
    interviewer_note: InterviewerNote
```

### DB 테이블
| 테이블 | 용도 |
|--------|------|
| jobs | Job 상태/메타데이터 |
| users | OAuth 사용자 |
| api_keys | API 키 (SHA-256 해시) |
| checkpoints | 단계별 체크포인트 |
| vectors | pgvector 벡터 저장 |

## 파일 배치
```
backend/app/models/job.py       — Job, JobStatus, CreateJobRequest
backend/app/models/question.py  — InterviewQuestion, FollowUp, Evaluation
backend/app/models/analysis.py  — CandidateProfile, CodeAnalysis, JDAnalysis
backend/app/models/input.py     — InputData, EnrichedInput
backend/app/models/output.py    — InterviewScript (최종)
```

## 규칙
- 모든 모델: Pydantic `BaseModel` 사용
- DB 모델: SQLAlchemy + Pydantic 분리 (ORM ↔ API 모델)
- Enum 사용: `QuestionCategory`, `Difficulty`, `JobStatus`
- pgvector: `VECTOR(1536)` 컬럼 타입
- UUID: Job ID, User ID 등 모든 식별자
