---
title: "진정성 지표 (Authenticity Metric)"
type: component
layer: domain
parent: "[[domain/scoring-system/MOC]]"
depends-on:
  - "[[infrastructure/plagiarism-detection/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# 진정성 지표 (Authenticity Metric)

> 전체 최종 점수에서 **20%** 기여.
> 제출된 코드를 후보자가 실제로 직접 작성했는지를 다각도로 검증한다.
> 인간 타이핑 패턴, 순수 기여도, 표절 비율, 스타일 일관성 4축으로 평가.
> 순수 기여 비율이 높을수록 고득점.

## 세부 항목 및 가중치

| 세부 지표 | 내부 가중치 | 측정 도구 | Worker | 설명 |
|----------|------------|---------|--------|------|
| 인간 타이핑 속도 (WPM) | 30% | Vibector | W3 | 커밋 타임스탬프 기반 입력 속도 패턴 분석 |
| 순수 기여도 | 30% | Blame + AST Pruning | W2 | AI/복사 코드를 제외한 실제 작성 LoC 비율 |
| 표절/복사 비율 | 20% | Datasketch (LSH) | W5 | MinHash + LSH로 유사 코드 탐지 |
| 스타일 일관성 | 20% | CLAVE | W4 | 커밋 간 코딩 스타일의 일관성 및 개인 특성 |

## 측정 도구 상세

### Vibector (인간 타이핑 속도)

```
분석 방법:
  커밋 타임스탬프와 변경 LoC를 이용해 입력 속도(WPM) 추정
  정상 인간 범위: 30-120 WPM
  AI 복붙 패턴: 수천 LoC가 수 초 내 단일 커밋으로 등장

플래그 조건:
  WPM > 500 → AI/Paste 의심 (high suspicion)
  WPM > 200 → 검토 필요 (medium suspicion)
  WPM <= 120 → 정상 범위 (human)
```

### Blame + AST Pruning (순수 기여도)

```
순수 기여도 산출:
  1. git blame으로 각 라인의 저자 확인
  2. AST Pruning으로 생성 코드 제거:
     - import 구문, boilerplate, scaffold 코드
     - LLM 생성 패턴 (특정 주석 패턴, 반복 구조)
  3. 최종 계산:
     LoC_pure = LoC_total - LoC_AI - LoC_copy - LoC_boilerplate
     originality_ratio = LoC_pure / LoC_total
```

### Datasketch MinHash + LSH (표절 탐지)

[[infrastructure/plagiarism-detection/MOC]] 에서 MinHash 서명을 받아 유사도를 비교한다.

```
LSH (Locality-Sensitive Hashing) 프로세스:
  1. 코드 파일을 k-shingle (k=5)으로 분해
  2. MinHash로 서명 생성 (128 해시 함수)
  3. LSH 버킷에서 유사 코드 검색
  4. Jaccard 유사도 ≥ 0.8 → 표절 판정

plagiarism_ratio = 표절 판정 LoC / LoC_total
```

### CLAVE (스타일 일관성)

```
분석 항목:
  - 들여쓰기 패턴 일관성
  - 변수명 명명 규칙 일관성 (camelCase vs snake_case 혼용)
  - 주석 스타일 (docstring vs inline)
  - 함수 길이 분포의 개인 패턴

불일관성 = 코드 일부가 다른 사람/AI 스타일인 신호
```

## 산출 수학적 모델

```python
# domain/scoring/metrics/authenticity.py

def calculate_authenticity_score(
    human_wpm: float,          # 추정 WPM (정상: 0-120)
    originality_ratio: float,  # 순수 기여 비율 (0.0~1.0)
    plagiarism_ratio: float,   # 표절 비율 (0.0~1.0)
    style_consistency: float,  # 스타일 일관성 (0.0~1.0)
) -> float:
    """
    진정성 지표 점수 산출.
    순수 기여가 높고 표절이 낮을수록 고득점.
    """
    # 인간 타이핑 속도: 정상 범위(0-120 WPM)에서 최고점
    # 120 이상부터 감점, 500 이상은 0점
    score_wpm = max(0.0, min(100.0, (1 - max(0, human_wpm - 120) / 380) * 100))

    # 순수 기여도: 비율 직접 환산
    score_originality = originality_ratio * 100

    # 표절 비율: 역산 (표절 0% → 100점, 표절 100% → 0점)
    score_plagiarism = max(0.0, (1 - plagiarism_ratio) * 100)

    # 스타일 일관성: 비율 직접 환산
    score_style = style_consistency * 100

    # 내부 가중치 합산
    return (
        score_wpm * 0.30
        + score_originality * 0.30
        + score_plagiarism * 0.20
        + score_style * 0.20
    )
```

## AuthenticityScore 모델 연동

```python
# domain/analysis/models.py (발췌)
class AuthenticityScore(BaseModel):
    model_config = ConfigDict(strict=True)

    human_typing_ratio: float = Field(ge=0, le=1)
    originality_ratio: float = Field(ge=0, le=1)
    ai_code_suspicion: float = Field(ge=0, le=1)
    plagiarism_ratio: float = Field(ge=0, le=1)
    style_consistency: float = Field(ge=0, le=1)
```

## 전체 진정성 점수 기여

```python
# domain/scoring/calculator.py (발췌)
Index_authenticity = (LoC_total - LoC_AI - LoC_copy) / LoC_total * 100
# 최종 점수 기여: Index_authenticity * 0.20
```

## 인프라 의존성

[[infrastructure/plagiarism-detection/MOC]] 에서 다음 정보를 받아 사용한다:

- MinHash 서명 (코드 파일별)
- LSH 버킷 유사도 검색 결과
- Jaccard 유사도 행렬

Domain 계층은 MinHash 계산을 직접 수행하지 않는다 (DDD 규칙).
