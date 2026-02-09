# Prompt A/B Testing Strategy (상세)

> CLAUDE.md에서 분리된 상세 문서. 핵심 요약은 CLAUDE.md 본문 참조.

## A/B 테스트 대상 프롬프트 (6개)

| 프롬프트 YAML | Activity | 품질 영향도 | 우선순위 |
|---------------|----------|-----------|---------|
| `question_generation.yaml` (select_topics) | `select_topics()` | CRITICAL | P0 |
| `quality_review.yaml` (review) | `review_questions()` | CRITICAL | P0 |
| `document_analysis.yaml` (extract_profile) | `analyze_documents()` | HIGH | P1 |
| `v2_generation.yaml` (competency_matching) | Intel/Deep/Decision | HIGH | P1 |
| `jd_analysis.yaml` (analyze) | `analyze_jd()` | MEDIUM | P2 |
| `finalization.yaml` (candidate_summary) | `finalize_output()` | MEDIUM | P2 |

## Langfuse Experiments 워크플로우

```
1. GOLDEN DATASET → 고품질 입출력 쌍 수집 (≥20개)
   ↓
2. PROMPT A (현재) + PROMPT B (후보) → 동일 입력으로 실행
   ↓
3. EVALUATORS → LLM-as-Judge + 구조적 검증 + Phoenix 배치
   ↓
4. COMPARE → 통계적 유의성 + 품질 ≥5% 향상 + 비용 트레이드오프
   ↓
5. PROMOTE or ROLLBACK → Langfuse production label
```

## Langfuse Experiments API 예시

```python
from langfuse import Langfuse
langfuse = Langfuse()

# 1. 골든 데이터셋
dataset = langfuse.create_dataset(name="interview_questions_golden_v1")
for item in curated_high_quality_results:
    langfuse.create_dataset_item(
        dataset_name="interview_questions_golden_v1",
        input=item["input"],
        expected_output=item["output"],
        metadata={"source": "production", "quality_score": item["score"]}
    )

# 2. 실험 실행
def run_prompt_variant(dataset_item, prompt_version: str):
    prompt = langfuse.get_prompt(name="select_topics", version=prompt_version)
    return llm_service.generate(prompt, dataset_item.input)

# 3. 평가자
def evaluate_question_quality(output, expected_output) -> dict:
    return {
        "relevance": llm_judge(output, expected_output, "relevance"),
        "specificity": structural_check(output, "specificity"),
        "evidence_grounding": evidence_check(output),
        "category_balance": distribution_check(output),
        "cost": calculate_token_cost(output),
    }

# 4. 실행 + 비교
experiment_a = langfuse.run_experiment(
    name="select_topics_v2.0", dataset_name="interview_questions_golden_v1",
    task=lambda item: run_prompt_variant(item, "v2.0"),
    evaluators=[evaluate_question_quality],
)
experiment_b = langfuse.run_experiment(
    name="select_topics_v2.1", dataset_name="interview_questions_golden_v1",
    task=lambda item: run_prompt_variant(item, "v2.1"),
    evaluators=[evaluate_question_quality],
)
```

## Phoenix 기반 병렬 평가

```python
from phoenix.evals import create_classifier, LLM, run_evals
import pandas as pd

llm = LLM(provider="openai", model="gpt-4o")
evaluators = {
    "profile_completeness": create_classifier(name="profile_completeness", llm=llm,
        prompt_template="[추출된 프로필]: {extracted_profile}\n[원본]: {resume_text}\n완전한가?",
        choices={"complete": 1.0, "partial": 0.5, "incomplete": 0.0}),
    "intel_brief_accuracy": create_classifier(name="intel_brief_accuracy", llm=llm,
        prompt_template="[요약]: {intel_brief}\n[데이터]: {analysis_data}\n정확한가?",
        choices={"accurate": 1.0, "mostly_accurate": 0.5, "inaccurate": 0.0}),
    "decision_consistency": create_classifier(name="decision_consistency", llm=llm,
        prompt_template="[점수]: {radar_scores}\n[추천]: {recommendation}\n[위험]: {risk_assessment}\n일관적인가?",
        choices={"consistent": 1.0, "minor_inconsistency": 0.5, "contradictory": 0.0}),
    "question_specificity": create_classifier(name="specificity", llm=llm,
        prompt_template="[배경]: {candidate_summary}\n[질문]: {question}\n맞춤인가?",
        choices={"specific": 1.0, "somewhat_specific": 0.5, "generic": 0.0}),
}
df = pd.DataFrame(test_data)
results = run_evals(df, evaluators=list(evaluators.values()), concurrency=10)
```

## 승격/롤백 기준

| 항목 | 승격 (B→Prod) | 롤백 (B→Archive) |
|------|-------------|-----------------|
| 품질 점수 | avg(B) > avg(A) + 5% | avg(B) < avg(A) |
| 환각 비율 | hallu(B) ≤ hallu(A) | hallu(B) > hallu(A) + 2% |
| 토큰 비용 | cost(B) ≤ cost(A) × 1.2 | cost(B) > cost(A) × 1.5 |
| 샘플 수 | n ≥ 50 | n < 30 |
| 응답 속도 | latency(B) ≤ latency(A) × 1.3 | latency(B) > latency(A) × 2.0 |

## 실행 주기 (사전 런칭 집중 모드)

- **Daily**: 6개 프롬프트 × (A 5회 + B 5회) = 60회/일
- **5일 누적** → 통계적 유의성 확보 → 승격/롤백 판정
- **On-demand**: 프롬프트 수정 시 즉시 10회 테스트

### 런칭 전 졸업 기준
- P0 프롬프트 Evidence Score 평균 ≥ 80
- P1 프롬프트 정확도 ≥ 85%
- Phase 4 교차 일관성 모순 0개 (10회 연속)
- 환각 비율 0% (50회 연속)

### 테스트 실행 명령
```bash
for i in 1 2 3 4 5; do
  docker compose exec backend python scripts/create_test_job.py \
    --email test${i}@example.com \
    --level $(echo "주니어 시니어 CTO/VP 리드 미들" | cut -d' ' -f$i) \
    --lang $(echo "ko en ko en ko" | cut -d' ' -f$i) \
    --questions $(echo "15 20 25 10 20" | cut -d' ' -f$i)
done
```

## Langfuse Eval 통합 방안

### LLM-as-Judge 평가자 (12개)

| 평가자 | 대상 Activity |
|--------|-------------|
| `profile_extraction_quality` | `analyze_documents` |
| `jd_analysis_quality` | `analyze_jd` |
| `code_analysis_depth` | `analyze_code` |
| `kg_entity_accuracy` | `build_knowledge_graph` |
| `question_relevance` | `craft_question` |
| `question_specificity` | `craft_question` |
| `evidence_grounding` | `craft_question` |
| `followup_quality` | `design_follow_ups` |
| `intel_brief_accuracy` | `generate_intel_brief` |
| `radar_score_grounding` | `generate_deep_analysis` |
| `decision_consistency` | `generate_decision_support` |
| `cross_tab_consistency` | `finalize_output` |

### SDK 스코어 기록 패턴
```python
from app.core.evaluation import create_score
# Phase 2: create_score(trace_id, f"{activity}_completeness", val)
# Phase 3: create_score(trace_id, "question_quality", score/10)
# Phase 4: create_score(trace_id, f"{tab}_consistency", val)
```

### 골든 데이터셋 (Activity별, 각 ≥20개)
`profile_extraction_golden`, `jd_analysis_golden`, `topic_selection_golden`,
`question_generation_golden`, `intel_brief_golden`, `deep_analysis_golden`, `decision_support_golden`

### Annotation Queue
- 채용 담당자 직접 평가 → Cohen's Kappa로 자동 평가 신뢰도 측정

## Kimi K2.5 파인튜닝 현황

| 항목 | 상태 |
|------|------|
| Moonshot Platform API | ❌ 미지원 (추론만) |
| Open-source (HuggingFace) | ✅ (1T params, 32B active, MoE) |
| LoRA (LlamaFactory) | ✅ (2x RTX 4090) |
| Fireworks AI 관리형 | ✅ |

**권장**: Phase 1 프롬프트 최적화 → Phase 2 Few-shot → Phase 3 Eval 게이트 → Phase 4 파인튜닝

## 품질 자동 개선 루프

```
GENERATE → EVALUATE → SCORE & RECORD
    ↑                      ↓
  REVISE ← LOW SCORE ← ANALYZE TRENDS
                           ↓
                    A/B TEST & PROMOTE
```

자동화 트리거:
- Phase 2: 완전성 <90% / 누락 >2개 / HYBRID 미완수 → 프롬프트 검토
- Phase 3: Evidence <70 → revise / 환각 → REJECT / 중복 → 제거 / 불균형 → 추가
- Phase 4: 사실 오류 / 근거 부족 / 모순 → 재생성
- Langfuse 주간 리포트 → 하락 Activity → A/B 테스트 트리거
