---
name: arch-prompt
description: LLM 프롬프트 엔지니어링. 질문 생성 프롬프트, Pydantic AI, LiteLLM, Langfuse, 구조화 출력 관련 구현 시 사용.
argument-hint: [prompt-type] (예: topic-selection, question-craft, quality-review, terminology)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Prompt Engineering Architecture Skill

LLM 프롬프트 설계 및 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/07-prompt-guide.md` — 프롬프트 엔지니어링 가이드 전체
2. `docs/architecture/06-output-spec.md` — 출력 구조 (프롬프트의 목표 출력)
3. `docs/architecture/03-workflow.md` — 어떤 단계에서 어떤 프롬프트가 필요한지

## LLM 스택
```
Pydantic AI — 에이전트 오케스트레이션 (구조화 출력의 기본 레이어)
LiteLLM    — 게이트웨이 (모델 라우팅, 캐싱, fallback)
Instructor — 복잡한 구조화 추출 보완 (Pydantic AI 부족분)
Langfuse   — 관측 (프롬프트 관리, 토큰/비용 추적)
```

## Phase별 프롬프트

### Phase 0: Input Enrichment
- URL 추출 프롬프트 (PDF/DOCX 텍스트에서 GitHub/LinkedIn URL 발견)

### Phase 2: Analysis
- Document Analysis: 이력서/포트폴리오 → 구조화된 프로필
- Code Analysis: 코드 스니펫 → 기술적 의미 분석
- JD Analysis: 채용공고 → 구조화된 요구사항

### Phase 3: Question Generation (핵심)
1. **Topic Selection**: 25개 토픽 선정 프롬프트
2. **Question Crafting**: 개별 질문 생성 (구조화 출력)
3. **Terminology Definition**: 용어 → 비개발자 설명
4. **Follow-up Design**: 3단계 분기 후속질문
5. **Evaluation Scenario**: Expert/Mid/Low 평가 기준
6. **Code Linking**: 코드 참조 연결
7. **Interviewer Note**: 비즈니스 해석 + 일상 비유

### Phase 4: Quality Review
- 중복 검사, 연관성 검증, 흐름 최적화 프롬프트

## 구현 패턴

### Pydantic AI 구조화 출력
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

### CachedLLMService
```python
class CachedLLMService:
    async def generate(self, prompt, model="gpt-4o", cache_key=None):
        # 1. Redis 캐시 확인
        # 2. 캐시 miss → LiteLLM 호출
        # 3. 결과 캐시 저장
        # 4. Langfuse 로깅
```

### 프롬프트 템플릿 (Jinja2)
```
backend/app/prompts/
├── topic_selection.j2
├── question_craft.j2
├── terminology.j2
├── follow_up.j2
├── evaluation.j2
├── code_link.j2
├── interviewer_note.j2
└── quality_review.j2
```

## 규칙
- 모든 LLM 호출: `CachedLLMService` 경유 (직접 API 호출 금지)
- 구조화 출력: Pydantic AI `result_type` 필수
- 프롬프트: Jinja2 템플릿 분리 (코드에 하드코딩 금지)
- 비개발자 친화: 모든 출력에 plain_language 설명 포함
- Hallucination 방지: 코드 참조 필수, 없으면 질문 생성 거부
