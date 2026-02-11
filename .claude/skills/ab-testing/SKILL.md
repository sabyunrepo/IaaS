# Prompt A/B Testing Strategy (프롬프트 A/B 테스트 전략)

> GOLDEN DATASET → PROMPT A/B 실행 → EVALUATORS → COMPARE → PROMOTE/ROLLBACK

## 대상 프롬프트 (6개)

| YAML | Activity | 우선순위 |
|------|----------|---------|
| `question_generation.yaml` | `select_topics()` | P0 |
| `quality_review.yaml` | `review_questions()` | P0 |
| `document_analysis.yaml` | `analyze_documents()` | P1 |
| `v2_generation.yaml` | Intel/Deep/Decision | P1 |
| `jd_analysis.yaml` | `analyze_jd()` | P2 |
| `finalization.yaml` | `finalize_output()` | P2 |

## 승격/롤백 기준

| 항목 | 승격 (B→Prod) | 롤백 |
|------|--------------|------|
| 품질 | avg(B) > avg(A) + 5% | avg(B) < avg(A) |
| 환각 | hallu(B) ≤ hallu(A) | hallu(B) > hallu(A) + 2% |
| 비용 | cost(B) ≤ cost(A) × 1.2 | cost(B) > cost(A) × 1.5 |
| 샘플 | n ≥ 50 | n < 30 |

## 실행 주기

- **Daily**: 6개 프롬프트 × (A 5회 + B 5회) = 60회/일
- **5일 누적** → 통계적 유의성 → 승격/롤백
- **졸업 기준**: P0 Evidence ≥80, P1 정확도 ≥85%, 환각 0% (50회 연속)

## 품질 개선 전략 (권장 순서)

프롬프트 최적화 → Few-shot 강화 → Eval 게이트 (Langfuse+Phoenix) → 파인튜닝 (Fireworks AI LoRA)

## 자동 개선 루프

`GENERATE → EVALUATE → SCORE & RECORD → ANALYZE TRENDS → (low score) → REVISE → GENERATE` + A/B 승자 자동 승격

## 상세 참조

Langfuse API/Phoenix 코드, 12개 LLM-as-Judge 평가자, 골든 데이터셋, 파인튜닝 현황 → `docs/claude-references/prompt-ab-testing.md`
