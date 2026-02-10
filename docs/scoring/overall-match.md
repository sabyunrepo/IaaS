# Overall Match (종합 매치율)

> 코드: `scoring_formulas.py:calculate_overall_match()`
> 반환: `ScoringResult(score, source, confidence, components, human_source)`

## 가중치 공식

```
overall_match = skill_match × 35% + code_quality × 25% + experience_fit × 25% + jd_match × 15%
```

| 구성 요소 | 가중치 | 설명 | 입력 범위 |
|----------|--------|------|----------|
| `skill_match` | 35% | 스킬 매칭 평균 점수 | 0-100 |
| `code_quality` | 25% | 코드 품질 종합 점수 | 0-100 |
| `experience_fit` | 25% | 경력 적합도 점수 | 0-100 |
| `jd_match` | 15% | JD 매칭 점수 (0-1 → 0-100 정규화) | 0-100 |

## 가중치 근거

- **skill_match (35%)**: 가장 직접적인 역량 지표. JD 스킬과 후보자 스킬의 매칭도
- **code_quality (25%)**: 코드 실력의 객관적 지표. GitHub 분석 기반
- **experience_fit (25%)**: SFIA 프레임워크 기반 경력 수준 적합도
- **jd_match (15%)**: JD 전체 요구사항 충족률 (스킬 외 조건 포함)

## 추천 등급 매핑

| 점수 | 등급 | 의미 |
|------|------|------|
| 80-100% | Strong Hire | 적극 추천. 해당 직무에 매우 적합 |
| 60-79% | Hire | 추천. 대부분의 요구사항 충족 |
| 40-59% | Leaning No | 보류. 일부 영역 보완 필요 |
| 0-39% | No Hire | 비추천. 현재 직무에 적합하지 않음 |

## 코드 위치

- 가중치 상수: `scoring_formulas.py:OVERALL_MATCH_WEIGHTS`
- 계산 함수: `scoring_formulas.py:calculate_overall_match()`
- 호출 위치: `analysis_generation.py:730-736`
