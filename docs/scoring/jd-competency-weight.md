# JD Competency Weight (JD 역량 가중치)

> 코드: `decision_generation.py:_map_jd_competencies()`
> 반환: `list[JDCompetencyWeight]` — competency, weight, related_questions

## 개요

JD에서 추출한 **핵심 역량(competency)**에 가중치를 부여하고,
생성된 면접 질문과의 매핑 관계를 표시한다.
면접관이 어떤 역량이 중요하고, 어떤 질문이 해당 역량을 검증하는지 한눈에 파악할 수 있도록 돕는다.

## 계산 공식

### 1단계: 기본 가중치 (균등 배분)

```
base_weight = 1.0 / total_requirements
```

- JD 요구사항 수에 따라 균등 배분
- 최대 5개 역량까지 처리 (상위 5개)

### 2단계: 질문 매핑

각 역량에 대해 관련 질문을 탐색:

```
for each question:
  if competency_name in question_text  → related
  if competency_name in skills_assessed → related
```

- 질문 텍스트에 역량명 포함 여부 (case-insensitive)
- 질문의 `skills_assessed` 배열에 역량명 포함 여부
- 관련 질문 인덱스는 1-based (UI 표시용)
- 최대 5개 관련 질문까지 표시

### 3단계: 가중치 조정

```
weight = base_weight + 0.05 × len(related_questions)
weight = min(0.4, weight)  # 상한선 40%
```

- 관련 질문이 많을수록 해당 역량의 가중치 상승
- 단일 역량이 전체의 40%를 초과하지 않도록 상한선 적용

### 4단계: 정규화

```
for each competency:
  weight = weight / sum(all_weights)
```

- 전체 가중치 합이 1.0 (100%)이 되도록 정규화
- 소수점 2자리까지 반올림

## 예시

JD 요구사항 3개, 질문 15개인 경우:

| 역량 | 기본 가중치 | 관련 질문 수 | 조정 가중치 | 정규화 |
|------|-----------|------------|-----------|--------|
| Python | 0.33 | 4 | 0.40 (상한) | 0.40 |
| AWS | 0.33 | 2 | 0.40 (상한) | 0.33 |
| Docker | 0.33 | 1 | 0.38 | 0.27 |

## 비개발자 해석

> "Python 역량이 40%로 가장 중요하고, 관련 질문이 4개입니다"는
> 이 직무에서 Python 실력이 가장 핵심이며, 면접 질문 중 4개가
> 이 역량을 직접 검증한다는 의미입니다.

## 코드 위치

- 매핑 함수: `decision_generation.py:_map_jd_competencies()` (431-474)
- 호출 위치: `decision_generation.py:547`
- 모델 정의: `models/decision.py:JDCompetencyWeight`
- UI 표시: `DecisionTab.tsx` (JD Competency Map 섹션)
