---
title: "Question Generation"
type: moc
layer: domain
parent: "[[domain/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-106", "JIT-107", "JIT-108", "JIT-109", "JIT-110"]
---

# Question Generation

## 개요

Question Generation은 후보자의 실제 코드에서 **비개발자 면접관도 판단할 수 있는 구조화된 면접 질문을 생성**하는 도메인 레이어다. 3가지 고유 전략을 통해 후보자가 코드를 실제로 작성했는지, 트레이드오프를 이해하는지, 유지보수 경험이 있는지를 검증한다.

### 전체 파이프라인

```
TopicSelector
  - pgvector 벡터 검색으로 JD 관련성 높은 코드 청크 선별
  - 3전략별 토픽 분배 (Negative / Complexity / Evolution)
        |
        v
QuestionCrafter x 3 (병렬)
  - 전략 A: Negative Selection   -> InterviewQuestion
  - 전략 B: Intentional Complexity -> InterviewQuestion
  - 전략 C: Code Evolution        -> InterviewQuestion
        |
        v
EnhancementAgents x 5 (병렬)
  - 용어 설명 Agent
  - 답변 가이드 Agent
  - 파생 질문 Agent
  - Red Flag Agent
  - 코드 레퍼런스 Agent
        |
        v
QualityGate (Reviewer + Reviser, 최대 2회 루프)
        |
        v
OutputAssembler
```

### 3전략 비교

| 전략 | 분석 로직 | 핵심 목적 |
|------|-----------|-----------|
| Negative Selection | 사용되지 않은 패턴/기술 AST 감지 | 의도적 선택 vs 단순 무지 판별 |
| Intentional Complexity | Halstead D + 순환 복잡도 높은 구간 식별 | 복잡도 유지의 아키텍처적 근거 검증 |
| Code Evolution | Git Churn 높은 구간, 대규모 리팩토링 추적 | 직접 작성 및 유지보수 진정성 검증 |

---

## 구성 요소

- [[domain/question-generation/three-strategies]] — 3전략 개요 및 비교
- [[domain/question-generation/negative-selection]] — 전략 A: 미사용 패턴에서 질문 도출
- [[domain/question-generation/intentional-complexity]] — 전략 B: 높은 복잡도 구간에서 질문 도출
- [[domain/question-generation/code-evolution]] — 전략 C: Git 변경 이력에서 질문 도출

---

## Dataview

```dataview
TABLE type, status
FROM "docs/architecture/domain/question-generation"
WHERE type = "component"
SORT file.name ASC
```
