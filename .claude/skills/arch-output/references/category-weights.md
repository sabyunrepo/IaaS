# Category Weights Reference

레벨별 카테고리 가중치와 의사결정 임계값.

## 레벨별 카테고리 가중치

| 카테고리 | CTO/VP | Senior | Mid | Junior |
|---------|--------|--------|-----|--------|
| role_fit | 25% | 15% | 15% | 15% |
| technical | 20% | 35% | 35% | 35% |
| execution | 20% | 25% | 25% | 20% |
| communication | 20% | 10% | 10% | 10% |
| risk_flags | 15% | 15% | 15% | 20% |

## 카테고리별 질문 분배

| 카테고리 | 한국어 | 질문 수 | 난이도 분배 |
|---------|--------|---------|------------|
| role_fit | 역할 적합성 | 5 | Easy 2, Medium 2, Hard 1 |
| technical | 기술 역량 | 5 | Easy 2, Medium 2, Hard 1 |
| execution | 실행 능력 | 5 | Easy 2, Medium 2, Hard 1 |
| communication | 커뮤니케이션 | 5 | Easy 2, Medium 2, Hard 1 |
| risk_flags | 리스크 | 5 | Easy 2, Medium 2, Hard 1 |

## 의사결정 임계값

| 구간 | 점수 범위 | 추천 |
|------|----------|------|
| Strong Hire | ≥90% | 즉시 채용 추천 |
| Hire | 60-89% | 조건부 추천 (보완 영역 명시) |
| No Hire | <60% | 비추천 (핵심 부족 영역 명시) |

## 종합 점수 산출

```
match_score = Σ(category_score × category_weight) / Σ(weights)

category_score = avg(question_scores_in_category)
  where question_score = f(evidence_score, relevance, depth)
```
