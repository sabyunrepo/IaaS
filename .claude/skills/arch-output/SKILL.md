---
name: arch-output
description: 면접 스크립트 출력 구현. InterviewScript 구조, 25개 질문, 카테고리, 평가 시나리오, 용어 설명, 면접관 노트 관련 구현 시 사용.
argument-hint: [section] (예: question-structure, evaluation, terminology, interviewer-note)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Output Specification Architecture Skill

25개 면접 질문 + 면접 스크립트 출력 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/06-output-spec.md` — 출력 명세 전체 (1549줄)
2. `docs/architecture/02-data-models.md` — InterviewQuestion 모델

## 출력 구조

```
InterviewScript
├── candidate_summary
│   ├── 핵심 기술 스택
│   ├── 경력 요약
│   └── JD 매칭 점수
│
├── questions[25] (5카테고리 × 5)
│   ├── category: role_fit | technical | execution | communication | risk_flags
│   ├── difficulty: easy | medium | hard
│   ├── main_question
│   ├── alternative_phrasings[2-3]
│   ├── follow_up_questions[3] (expert/mid/low trigger)
│   ├── evaluation_scenarios[3] (expert/mid/low)
│   ├── keywords[] (must / good_to_have)
│   ├── terminology[] (plain_language_explanation)
│   ├── code_reference (GitHub permalink + plain_language_summary)
│   └── interviewer_note (business_interpretation + daily_analogy)
│
├── decision_guide
│   ├── 카테고리별 가중치 (레벨별)
│   ├── 의사결정 임계값 (90%/60%/35%)
│   └── 종합 추천
│
└── interviewer_guide
    ├── 전체 소요 시간
    ├── 질문 순서 가이드
    └── 주의사항
```

## 카테고리별 질문 분배
| 카테고리 | 한국어 | 질문 수 | 난이도 분배 |
|---------|--------|---------|------------|
| role_fit | 역할 적합성 | 5 | Easy 2 + Medium 2 + Hard 1 |
| technical | 기술 역량 | 5 | Easy 2 + Medium 2 + Hard 1 |
| execution | 실행 능력 | 5 | Easy 2 + Medium 2 + Hard 1 |
| communication | 커뮤니케이션 | 5 | Easy 2 + Medium 2 + Hard 1 |
| risk_flags | 리스크 | 5 | Easy 2 + Medium 2 + Hard 1 |

## 레벨별 카테고리 가중치
```
CTO:    role_fit 25%, tech 20%, exec 20%, comm 20%, risk 15%
Senior: role_fit 15%, tech 35%, exec 25%, comm 10%, risk 15%
Junior: role_fit 15%, tech 35%, exec 20%, comm 10%, risk 20%
```

## 핵심 필드 구현

### follow_up_questions (후속질문 분기)
```python
class FollowUpQuestion(BaseModel):
    id: str
    trigger: Literal["expert", "mid", "low"]
    question: str
    purpose: str  # 왜 이 질문을 하는지
```

### evaluation_scenarios (평가 시나리오)
```python
class EvaluationScenario(BaseModel):
    level: Literal["expert", "mid", "low"]
    description: str  # 이 레벨의 답변 특징
    indicators: list[str]  # 구체적 판단 기준
```

### code_reference (코드 참조)
```python
class CodeReference(BaseModel):
    permalink: str  # GitHub permalink (필수, null 금지)
    file_path: str
    line_range: str
    plain_language_summary: str  # 비개발자용 코드 설명
```

### interviewer_note (면접관 노트)
```python
class InterviewerNote(BaseModel):
    business_interpretation: str  # 비즈니스 관점 해석
    daily_analogy: str  # 일상 비유
    red_flags: list[str]  # 경계 신호
```

## 8-Agent 질문 생성 파이프라인
1. Topic Selector → 25개 토픽 선정
2. Question Crafter (×10 병렬) → 기본 질문 생성
3. Terminology Definer → 용어 설명 추가
4. Follow-up Designer → 후속질문 3가지 분기
5. Evaluation Scenario Writer → 평가 시나리오
6. Code Linker → GitHub 코드 참조 연결
7. Interviewer Note Writer → 면접관 노트
8. Quality Reviewer → 최종 검증 (최대 3회)

## 규칙
- 모든 질문에 code_reference 필수 (null 허용 안 함)
- 용어 설명: 비개발자가 이해할 수 있는 일상 비유 포함
- 면접관 노트: 기술 → 비즈니스 가치 변환
- Hallucination 방지: 실제 코드 기반 질문만 허용
