# Scoring Formulas Reference

> 모든 수치의 계산 공식과 학술 출처를 정리한 문서입니다.
> 코드 원본: `backend/app/services/scoring_formulas.py`

## 수치 목록

| 수치 | 문서 | 코드 출처 | 학술 근거 |
|------|------|----------|----------|
| Radar 5축 | [radar-scores.md](./radar-scores.md) | `calculate_radar_scores()` | SFIA v9, McCabe (1976) |
| Overall Match | [overall-match.md](./overall-match.md) | `calculate_overall_match()` | Weighted Composite |
| Data Confidence | [data-confidence.md](./data-confidence.md) | `calculate_data_confidence()` | Source Triangulation |
| Skill Matching | [skill-matching.md](./skill-matching.md) | `intel_generation.py` | Exact/Semantic/Inferred |
| JD Competency Weight | [jd-competency-weight.md](./jd-competency-weight.md) | `decision_generation.py` | LLM + Normalization |

## 설계 원칙

1. **결정론적 공식**: LLM 주관이 아닌 코드 메트릭 → 점수 변환 공식 사용
2. **투명성**: 모든 점수에 `source` (기술적 근거)와 `human_source` (비개발자 설명) 포함
3. **학술 근거**: 가능한 한 논문/프레임워크 출처 명시
4. **일관성**: 동일 입력 → 동일 출력 보장 (Redis 캐시 + deterministic 공식)
