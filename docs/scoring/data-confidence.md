# Data Confidence (데이터 신뢰도)

> 코드: `scoring_formulas.py:calculate_data_confidence()`
> 반환: `(tier, score)` where tier is `"high"` / `"medium"` / `"low"`, score is 0-100

## 개요

후보자 분석에 사용된 **데이터 소스의 다양성과 품질**을 정량화한 지표.
데이터가 많고 다양할수록 분석 결과의 신뢰도가 높다.

## 계산 공식

```
score = source_availability + data_quality_bonus + multi_source_bonus
```

### 1단계: Source Availability (소스 확보 점수)

| 소스 | 가산 점수 | 근거 |
|------|----------|------|
| Resume (이력서) | +25 | 가장 기본적인 후보자 데이터 |
| GitHub | +25 | 코드 실력의 객관적 증거 |
| LinkedIn | +20 | 경력/학력 등 프로필 데이터 |

### 2단계: Data Quality Bonus (데이터 품질 보너스)

#### GitHub 커밋 수 기반
| 커밋 수 | 가산 점수 | 의미 |
|---------|----------|------|
| ≥ 50 | +15 | 충분한 코드 활동 |
| 10 - 49 | +8 | 보통 수준의 활동 |
| 1 - 9 | +3 | 최소한의 활동 확인 |
| 0 | +0 | 코드 활동 없음 |

#### LinkedIn 경력 수 기반
| 경력 수 | 가산 점수 | 의미 |
|---------|----------|------|
| ≥ 3 | +10 | 풍부한 경력 정보 |
| 1 - 2 | +5 | 기본 경력 정보 |
| 0 | +0 | 경력 정보 없음 |

### 3단계: Multi-Source Bonus (복수 소스 보너스)

| 조건 | 가산 점수 |
|------|----------|
| GitHub + LinkedIn + Resume 모두 확보 | +5 |

### 최종 점수

```
score = min(100, 합산)
```

## 신뢰도 등급 매핑

| 점수 | 등급 | 아이콘 | 의미 |
|------|------|--------|------|
| 80-100 | high | 🟢 | 3개 소스 + 충분한 데이터. 분석 결과 신뢰 가능 |
| 50-79 | medium | 🟡 | 2+ 소스 또는 1개 소스에 양질의 데이터. 참고용 |
| 0-49 | low | 🔴 | 1개 약한 소스. 분석에 불확실성 높음 |

## 시나리오 예시

| 시나리오 | 계산 | 점수 | 등급 |
|----------|------|------|------|
| Resume + GitHub(100 commits) + LinkedIn(5 positions) | 25+25+20+15+10+5 | 100 | 🟢 high |
| Resume + GitHub(30 commits) | 25+25+8 | 58 | 🟡 medium |
| Resume only | 25 | 25 | 🔴 low |
| Resume + LinkedIn(2 positions) | 25+20+5 | 50 | 🟡 medium |

## 비개발자 해석

> "데이터 신뢰도 75%"는 후보자의 이력서와 GitHub 활동 데이터를 기반으로 분석했으며,
> LinkedIn 정보가 추가되면 더 정확한 평가가 가능하다는 의미입니다.

## 코드 위치

- 계산 함수: `scoring_formulas.py:calculate_data_confidence()`
- 호출 위치: `analysis_generation.py:750-755`
- UI 표시: `DeepAnalysisTab.tsx` (Data Confidence 배지 + 상세 토글)
