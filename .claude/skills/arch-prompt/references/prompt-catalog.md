# Prompt Catalog Reference

전체 LLM 프롬프트 타입과 YAML 파일 목록.

## Phase별 프롬프트 매핑

### Phase 0: Input Enrichment
| 프롬프트 | YAML 파일 | Activity | 모델 |
|---------|-----------|----------|------|
| URL 추출 | (inline) | enrich_input | Kimi K2.5 |

### Phase 2: Analysis
| 프롬프트 | YAML 파일 | Activity | 모델 |
|---------|-----------|----------|------|
| 이력서 분석 | `document_analysis.yaml` | analyze_documents | Kimi K2.5 |
| 코드 분석 | (inline + LLM) | analyze_code | Kimi K2.5 |
| JD 분석 | `jd_analysis.yaml` | analyze_jd | Kimi K2.5 |

### Phase 3: Question Generation
| 프롬프트 | YAML 파일 | Activity | 모델 |
|---------|-----------|----------|------|
| 토픽 선정 | `question_generation.yaml` (select_topics) | select_topics | Kimi K2.5 |
| 질문 생성 | `question_generation.yaml` (craft_question) | craft_question | Kimi K2.5 |
| 용어 설명 | `question_generation.yaml` (terminology) | enhance_terminology | Kimi K2.5 |
| 평가 시나리오 | `question_generation.yaml` (evaluation) | craft_evaluation_scenarios | Kimi K2.5 |
| 꼬리질문 | `question_generation.yaml` (follow_up) | design_follow_ups | Kimi K2.5 |
| 품질 리뷰 | `quality_review.yaml` | review_questions | Kimi K2.5 |

### Phase 4: Result Generation
| 프롬프트 | YAML 파일 | Activity | 모델 |
|---------|-----------|----------|------|
| Intel Brief | `v2_generation.yaml` (intel_brief) | generate_intel_brief | Kimi K2.5 |
| Deep Analysis | `v2_generation.yaml` (deep_analysis) | generate_deep_analysis | Kimi K2.5 |
| Decision Support | `v2_generation.yaml` (decision_support) | generate_decision_support | Kimi K2.5 |
| 면접 가이드 | `finalization.yaml` (interviewer_guide) | finalize_output | Kimi K2.5 |
| 후보자 요약 | `finalization.yaml` (candidate_summary) | finalize_output | Kimi K2.5 |

## Pydantic AI 구조화 출력 패턴

```python
from pydantic_ai import Agent

agent = Agent(
    "openai:gpt-4o",
    result_type=InterviewQuestion,  # Pydantic 모델로 타입 강제
    system_prompt="...",
)
result = await agent.run(user_prompt)
# result.data → InterviewQuestion 인스턴스
```

## CachedLLMService 호출 패턴

```python
class CachedLLMService:
    async def generate(self, prompt, model="kimi-k2-0905-preview", cache_key=None):
        # 1. Redis 캐시 확인 (cache_key 기반)
        # 2. 캐시 miss → LiteLLM 호출
        # 3. 결과 캐시 저장 (TTL 설정)
        # 4. Langfuse 로깅 (토큰/비용 추적)
```

## 프롬프트 파일 위치

```
backend/app/prompts/
├── question_generation.yaml     — Phase 3: 질문 생성 관련 전체
├── quality_review.yaml          — Phase 3: 품질 리뷰
├── document_analysis.yaml       — Phase 2: 문서 분석
├── jd_analysis.yaml             — Phase 2: JD 분석
├── v2_generation.yaml           — Phase 4: Intel/Deep/Decision 생성
├── finalization.yaml            — Phase 4: 최종화
└── code_analysis.yaml           — Phase 2: 코드 분석 (있는 경우)
```

## 모델 설정 (llm_config.py)

```python
ACTIVITY_MODEL_CONFIG = {
    "default": {"model": "kimi-k2-0905-preview", "temperature": 0.3},
    "question_craft": {"model": "kimi-k2-0905-preview", "temperature": 0.7},
    "quality_review": {"model": "kimi-k2-0905-preview", "temperature": 0.1},
}
```
