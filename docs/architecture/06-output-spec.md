# 06. 최종 출력 명세 (Output Specification)

> 면접 스크립트 최종 출력물의 구조, 질문 설계 원칙, 프론트엔드 뷰 구조 정의

---

## 1. 질문 카테고리 체계

### 1.1 카테고리 정의

| 카테고리 | 영문 ID | 목적 | 아이콘 |
|---------|---------|------|--------|
| **역할 적합성** | `role_fit` | 포지션/조직 문화 적합도 확인 | 🎯 |
| **기술 역량** | `technical_depth` | 실제 기술력과 설계 능력 검증 | ⚙️ |
| **실행 & 오너십** | `execution_ownership` | 실행력, 의사결정, 책임감 확인 | 🚀 |
| **소통 & 협업** | `communication` | 팀워크, 이해관계자 소통 능력 | 💬 |
| **위험 신호 검증** | `risk_flags` | 이력서/코드에서 발견된 우려사항 직접 확인 | ⚠️ |

### 1.2 카테고리별 질문 배분 (기본 25문항)

| 카테고리 | CTO/VP | 시니어 | 주니어 |
|---------|--------|--------|--------|
| 역할 적합성 | 5 | 5 | 5 |
| 기술 역량 | 5 | 5 | 5 |
| 실행 & 오너십 | 5 | 5 | 5 |
| 소통 & 협업 | 5 | 5 | 5 |
| 위험 신호 검증 | 5 | 5 | 5 |

> 카테고리별 5문항 고정 배분 (난이도: Easy 2 / Medium 2 / Hard 1)
> 위험 신호 질문은 이력서/GitHub 분석에서 탐지된 flag에 기반하여 생성

---

## 2. 레벨별 질문 생성 프롬프트 차별화

### 2.1 CTO / VP Engineering

```yaml
prompt_context:
  perspective: "경영진 관점 — 전략, 조직 빌딩, 기술 비전"
  question_style:
    - 시나리오 기반 ("이런 상황에서 어떻게 하시겠습니까?")
    - 의사결정 프레임워크 요구 ("기준은 무엇이며, 왜?")
    - 트레이드오프 탐색 ("A와 B 중 어떤 것을, 왜?")
  evaluation_focus:
    - 전략적 사고력 (비즈니스-기술 연결)
    - 조직 빌딩 & 스케일링 역량
    - 불확실성 하의 의사결정
    - 이해관계자 커뮤니케이션
  code_reference_usage: "코드 품질/아키텍처 패턴 수준에서 참조"
  difficulty_distribution:
    easy: 2
    medium: 5
    hard: 3
  expected_answer_level:
    focus: "전략적 사고 + 조직 관점의 구체적 경험 사례"
    example: "단순히 '마이크로서비스로 전환했다'가 아닌 '왜 그 시점에 전환했는지, 팀을 어떻게 재편했는지, 이해관계자를 어떻게 설득했는지' 등 전략적 맥락과 실행 경험이 담긴 답변"
```

### 2.2 시니어 엔지니어

```yaml
prompt_context:
  perspective: "기술 리드 관점 — 설계, 멘토링, 기술적 깊이"
  question_style:
    - 구체적 기술 시나리오 ("이 시스템을 설계해주세요")
    - 코드 기반 질문 ("이 코드에서 어떤 문제가 보이시나요?")
    - 경험 기반 ("비슷한 문제를 해결한 경험은?")
  evaluation_focus:
    - 시스템 설계 역량
    - 코드 품질 의식
    - 주니어 멘토링 능력
    - 기술적 의사결정 근거
  code_reference_usage: "구체적 코드 스니펫 기반 질문 빈번"
  difficulty_distribution:
    easy: 1
    medium: 5
    hard: 4
  expected_answer_level:
    focus: "기술 깊이 + 실제 프로젝트 사례"
    example: "'Redis를 사용했다'가 아닌 '어떤 문제를 해결하기 위해 Redis를 선택했는지, 다른 대안은 무엇이었는지, 실제 성능 개선 수치는 얼마였는지' 등 기술적 깊이와 실무 경험이 결합된 답변"
```

### 2.3 주니어 엔지니어

```yaml
prompt_context:
  perspective: "성장 잠재력 관점 — 기초, 학습 능력, 태도"
  question_style:
    - 개념 확인 ("X가 무엇이고 왜 중요한가요?")
    - 경험 기반 ("프로젝트에서 어떤 역할을 했나요?")
    - 문제 해결 과정 ("이 버그를 어떻게 디버깅하시겠습니까?")
  evaluation_focus:
    - 기초 CS 지식
    - 학습 속도와 태도
    - 커뮤니케이션 명확성
    - 팀워크 적합성
  code_reference_usage: "GitHub 프로젝트의 구체적 코드에서 질문"
  difficulty_distribution:
    easy: 4
    medium: 5
    hard: 1
  expected_answer_level:
    focus: "기본 개념 이해 + 학습 의지"
    example: "'REST API를 만들었다'가 아닌 'REST가 무엇인지 이해하고, 프로젝트에서 어떻게 구현했는지, 어려웠던 점을 어떻게 해결했는지, 무엇을 배웠는지' 등 개념 이해와 성장 과정이 드러나는 답변"
```

---

## 3. 질문 데이터 모델 (확장)

### 3.1 InterviewQuestion (확장된 모델)

```python
class AnswerKeyword(BaseModel):
    """답변에서 기대되는 핵심 키워드"""
    keyword: str                    # "Strangler Fig Pattern"
    importance: Literal["must", "good_to_have"]  # 필수 vs 언급하면 가산
    explanation: str                # 왜 이 키워드가 중요한지

class TerminologyEntry(BaseModel):
    """기술 용어 설명"""
    term: str                       # "Strangler Fig Pattern"
    definition: str                 # 전문 정의
    plain_language_explanation: str # 비개발자용 쉬운 설명 (NEW)
    # 예: "Strangler Fig Pattern" → "오래된 시스템을 한번에 바꾸지 않고, 새 시스템을 옆에 만들면서 조금씩 옮겨가는 방법. 마치 오래된 집을 부수지 않고 옆에 새 집을 지으면서 하나씩 이사가는 것과 비슷합니다."
    context: str                    # 이 질문에서 왜 이 용어가 등장하는지

class CodeReference(BaseModel):
    """코드 참조 정보 (확장)"""
    repo_name: str                  # "username/project-name" (NEW)
    file_path: str                  # "src/services/auth.py" (NEW)
    line_range: str                 # "L45-L67" (NEW)
    permalink: str                  # GitHub permalink URL (NEW)
    snippet: str                    # 코드 스니펫
    explanation: str                # 이 코드가 왜 중요한지
    plain_language_summary: str     # 비개발자용 설명 (NEW)
    # 예: "이 코드는 사용자 로그인을 처리하는 부분입니다. 여기서 비밀번호를 어떻게 안전하게 저장하는지 확인할 수 있습니다."

class FollowUpQuestion(BaseModel):
    """꼬리질문 (메인질문 답변 수준에 따라 분기)"""
    id: str                         # "q1-f1"
    trigger_level: Literal["expert", "mid", "low", "any"]
    # expert: 우수 답변 시 더 깊이 파고드는 질문
    # mid: 보통 답변 시 구체성을 유도하는 질문
    # low: 미흡 답변 시 기본을 확인하는 질문
    # any: 모든 수준에서 물어볼 수 있는 질문

    question_text: str              # 꼬리질문 텍스트
    why_matters: str                # 이 꼬리질문이 중요한 이유
    listen_for: str                 # 답변에서 들어야 할 것

    # 채점 (간소화된 2단계)
    scoring: FollowUpScoring

    # 용어 (필요 시)
    terminology: list[TerminologyEntry]

class FollowUpScoring(BaseModel):
    """꼬리질문 채점 (2단계 간소화)"""
    good: str                       # 좋은 답변 시나리오
    good_score: int                 # +5 ~ +10
    poor: str                       # 부족한 답변 시나리오
    poor_score: int                 # 0 ~ -5

class ExpectedAnswer(BaseModel):
    """예상 답변 (확장)"""
    core_answer: str                # 불릿 포인트 핵심 답변
    example_script: str             # 자연스러운 답변 예시

    # 핵심 키워드 (NEW)
    answer_keywords: list[AnswerKeyword]

    # 레벨별 기대치
    depth_expectations: dict[str, str]

    # 코드 증거
    code_evidence: list[CodeEvidence]
    key_points: list[str]

class InterviewQuestion(BaseModel):
    """면접 질문 (확장된 최종 모델)"""
    id: str
    sequence: int
    category: QuestionCategory      # role_fit | technical_depth | ...
    topic: str
    difficulty: Difficulty

    # 질문 본체
    question_text: str
    context_bridge: str             # 상황 설정
    alternative_phrasings: list[str]

    # 면접관 가이드
    why_matters: str
    listen_for: str

    # 코드 참조 (확장)
    code_reference: CodeReference | None

    # 채점 루브릭 (3단계)
    evaluation_scenarios: EvaluationScenario

    # 꼬리질문 (답변 수준별 분기) (NEW)
    follow_ups: list[FollowUpQuestion]

    # 예상 답변 (키워드 포함) (ENHANCED)
    expected_answer: ExpectedAnswer

    # 용어집 (확장)
    terminology: list[TerminologyEntry]

    # 메타데이터
    language: str
    estimated_time_minutes: int
    skills_assessed: list[str]

    # 질문 생성 근거 (NEW)
    generation_rationale: str       # 왜 이 질문이 선택되었는지

    # JD 역량 연결 (NEW)
    jd_competency_link: str         # 이 질문이 채용공고의 어떤 역량 요구사항과 연결되는지
    # 예: "채용공고 요구사항: 'MSA 아키텍처 설계 및 전환 경험 3년 이상' → 이 질문으로 실제 전환 경험과 의사결정 능력 검증"
```

### 3.2 QuestionCategory Enum

```python
class QuestionCategory(str, Enum):
    ROLE_FIT = "role_fit"
    TECHNICAL_DEPTH = "technical_depth"
    EXECUTION_OWNERSHIP = "execution_ownership"
    COMMUNICATION = "communication"
    RISK_FLAGS = "risk_flags"
```

### 3.3 JDCompetencyMapping (NEW)

```python
class JDCompetencyMapping(BaseModel):
    """채용공고 역량 매핑"""
    competency: str                 # "MSA 아키텍처 설계 경험"
    jd_original_text: str           # 채용공고 원문 발췌
    # 예: "마이크로서비스 아키텍처 설계 및 모놀리스 전환 경험 3년 이상"

    why_important: str              # 왜 이 역량이 이 직무에 중요한지 (쉬운 말로)
    # 예: "회사가 현재 오래된 시스템을 새 시스템으로 바꾸는 중이어서, 이런 전환 경험이 있는 사람이 필요합니다. 시행착오를 줄이고 안전하게 전환할 수 있기 때문입니다."

    related_questions: list[str]    # 관련 질문 ID 리스트
    # 예: ["q2", "q3", "q7"] - 이 역량을 검증하는 질문들

    assessment_weight: float        # 이 역량의 중요도 (0.0 ~ 1.0)
    # 예: 0.8 - 매우 중요한 핵심 역량
```

---

## 4. 프론트엔드 뷰 구조

### 4.1 전체 레이아웃

```
┌──────────────────────────────────────────────────────────────────┐
│ [Sidebar]              [Main Content Area]                       │
│                                                                  │
│  Verdict Logo          ┌─────────────────────────────────────┐  │
│  ─────────            │ Header: 후보자명, 역할, 점수          │  │
│  Candidate List        │ Tabs: Intel | Analysis | Interview |  │  │
│  • Alex Chen ●        │       Decision                        │  │
│  • Sarah C            │                                       │  │
│  ─────────            │ [Tab Content Area]                    │  │
│  Archived              │                                       │  │
│  • John D (x)         │                                       │  │
│  ─────────            │                                       │  │
│  [+ New Interview]     └─────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Tab 3: Live Interview 상세 구조

```
┌─────────────────────────────────────────────────────────────────┐
│  [비개발자 면접관 안내 배너]                                        │
│  "개발 용어를 모르셔도 됩니다..."                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ── 섹션: 🎯 역할 적합성 (Role Fit) ──────────────────────        │
│                                                                   │
│  ┌─ Q1 ──────────────────────────────────────────────────────┐  │
│  │ [카테고리 뱃지] [난이도]                          Q1 / 10  │  │
│  │ 제목: "첫 90일 우선순위"                                    │  │
│  │                                                             │  │
│  │ ┌──────────────┐  ┌──────────────┐                        │  │
│  │ │ 이 질문이     │  │ 이런 답변을   │                        │  │
│  │ │ 중요한 이유   │  │ 들어보세요    │                        │  │
│  │ └──────────────┘  └──────────────┘                        │  │
│  │                                                             │  │
│  │ ┌─ 질문 (그대로 읽어주세요) ──────────────────────────┐    │  │
│  │ │ Context: "현재 저희는..."                             │    │  │
│  │ │ "CTO로서 첫 90일 동안..."                            │    │  │
│  │ └──────────────────────────────────────────────────────┘    │  │
│  │                                                             │  │
│  │ ▶ 코드 참조 (있는 경우)                                     │  │
│  │   저장소: user/project  파일: src/auth.py  라인: 45-67     │  │
│  │   쉬운 설명: "이 코드는 사용자 로그인을 처리하는..."         │  │
│  │                                                             │  │
│  │ ▶ 용어 설명 (3개)                                          │  │
│  │   • Strangler Fig Pattern                                  │  │
│  │     → 비개발자용: "오래된 집을 부수지 않고 옆에 새 집을..."  │  │
│  │                                                             │  │
│  │ ── 답변 채점 ──                                             │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐                   │  │
│  │ │ 🟢 우수   │ │ 🟡 보통   │ │ 🔴 미흡   │                   │  │
│  │ │ +20점     │ │ +10점     │ │ 0점       │                   │  │
│  │ │ [설명]    │ │ [설명]    │ │ [설명]    │                   │  │
│  │ └──────────┘ └──────────┘ └──────────┘                   │  │
│  │                                                             │  │
│  │ ── 핵심 키워드 체크 ──                                      │  │
│  │ [필수] Strangler Fig  [가산] Domain Boundary  ...          │  │
│  │                                                             │  │
│  │ ── 꼬리질문 (채점 후 자동 확장) ──                          │  │
│  │ 🟢 우수 선택 시만 표시:                                     │  │
│  │   "진단 결과 팀 역량이 부족하면 어떻게 대응하시겠습니까?"     │  │
│  │   왜 중요: "..."  들어볼 것: "..."  [+8] / [+0]            │  │
│  │                                                             │  │
│  │ (보통/미흡 수준의 꼬리질문은 완전히 숨김)                     │  │
│  │                                                             │  │
│  │ ▶ 면접관 참고 노트 (접기) ──                                │  │
│  │   • 비개발자 관점 해석: "이 답변은 회사가 변화를..."         │  │
│  │   • 일상 비유: "집을 리모델링할 때 먼저 골조를 확인하듯..."  │  │
│  │   • CTO 수준 기대치: "단순히 기술 선택이 아닌, 조직 영향과..."│  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─ Q2 ────── ... ───────────────────────────────────────────┐  │
│                                                                   │
│  ── 섹션: ⚙️ 기술 역량 (Technical Depth) ─────────────────      │
│  ┌─ Q3 ────── ... ──────────────────────────────────────────┐   │
│  ...                                                              │
└─────────────────────────────────────────────────────────────────┘

**Progressive Disclosure 패턴 (질문 카드 상태):**

초기 상태 (질문 읽기 전):
├── 질문 제목
├── 왜 중요한지 (why_matters)
├── 들어볼 것 (listen_for)
└── [질문 텍스트 펼치기 버튼]

질문 읽는 중:
├── 질문 텍스트 (context + 본문)
├── 코드 참조 (있는 경우)
├── 용어 설명
├── 답변 채점 버튼 (우수/보통/미흡)
└── 핵심 키워드 체크리스트

채점 후 (예: 우수 선택):
├── 선택한 수준의 채점 결과 강조
├── 해당 수준의 꼬리질문만 자동 확장 표시
├── 면접관 참고 노트 펼치기 가능
└── 다음 질문으로 이동 버튼
```

### 4.3 Tab 4: Decision 상세 구조

```
┌─────────────────────────────────────────────────────────────────┐
│  후보자 요약 카드                                                  │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                                   │
│  │7년  │ │78% │ │시니어│ │점수 │                                   │
│  │경력  │ │매칭 │ │레벨  │ │/200│                                   │
│  └────┘ └────┘ └────┘ └────┘                                   │
│                                                                   │
│  강점 / 확인 필요 사항                                             │
├─────────────────────────────────────────────────────────────────┤
│  카테고리별 점수 (섹션별)                                          │
│  🎯 역할 적합성        ████████░░  32/40                          │
│  ⚙️ 기술 역량          ██████░░░░  37/50                          │
│  🚀 실행 & 오너십      ███████░░░  30/40                          │
│  💬 소통 & 협업         ████████░░  28/35                          │
│  ⚠️ 위험 신호 검증     █████░░░░░  13/35                          │
│  ── 꼬리질문 보너스 ──  ████░░░░░░  15/50 (est.)                  │
├─────────────────────────────────────────────────────────────────┤
│  면접관 가이드                                                     │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ 면접 시간 / 순서   │  │ 진행 팁 / 주의신호│                     │
│  └──────────────────┘  └──────────────────┘                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   STRONG HIRE / HIRE / NO HIRE              │  │
│  │                   종합 추천 + 근거 설명                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 꼬리질문 설계 원칙

### 5.1 답변 수준별 분기 로직

```
메인 질문 답변 채점
├── 🟢 우수 (Expert) 선택 시
│   → "더 깊이 파고드는" 꼬리질문 표시
│   → 목적: 진짜 전문가인지 확인, 추가 가산점 기회
│   → 예: "그 전략이 실패했다면 Plan B는?"
│
├── 🟡 보통 (Mid) 선택 시
│   → "구체성을 유도하는" 꼬리질문 표시
│   → 목적: 경험의 깊이 탐색, 만회 기회 부여
│   → 예: "구체적으로 어떤 프로젝트에서 그 경험을?"
│
└── 🔴 미흡 (Low) 선택 시
    → "기본을 확인하는" 꼬리질문 표시
    → 목적: 진짜 모르는 건지, 긴장인지 구분
    → 예: "그렇다면 X라는 개념은 어떻게 이해하고 계신가요?"
```

### 5.2 꼬리질문 채점

- 메인 질문 점수: 0 ~ 25점
- 꼬리질문 보너스: -5 ~ +10점
- 꼬리질문은 **선택적** — 면접관이 시간/상황에 따라 판단
- 꼬리질문 점수는 별도 "보너스" 영역으로 합산

### 5.3 핵심 키워드 체크 원칙

```yaml
keyword_types:
  must:
    description: "이 키워드가 나오지 않으면 전문성 의심"
    visual: "빨간 테두리 필수 뱃지"
    example: "Strangler Fig Pattern (MSA 전환 질문에서)"

  good_to_have:
    description: "언급하면 깊이 있는 이해를 보여줌"
    visual: "파란 테두리 가산 뱃지"
    example: "Circuit Breaker (시스템 설계 질문에서)"
```

---

## 6. 위험 신호 질문 생성 규칙

### 6.1 자동 탐지 소스

| 소스 | 탐지 항목 | 질문 유형 |
|------|----------|----------|
| **이력서** | 경력 공백, 짧은 재직, 타이틀 갭 | 직접 확인 ("이 기간에 무엇을?") |
| **GitHub** | 활동 공백, 낮은 기여, 포크 위주 | 코드 활동 확인 ("이 기간 활동이 적은 이유?") |
| **코드 분석** | 안티패턴, 낮은 테스트, 보안 이슈 | 기술 인식 확인 ("테스트를 적게 작성한 이유?") |
| **JD 매칭** | 핵심 스킬 미매칭 | 역량 확인 ("X 경험이 부족한데 어떻게?") |
| **LinkedIn** | 이력서와 불일치 | 정합성 확인 ("LinkedIn과 다른 부분이 있는데?") |

### 6.2 위험 신호 질문 톤 가이드

```yaml
tone_principles:
  - 비난이 아닌 확인: "~가 보이는데, 말씀해주실 수 있나요?"
  - 기회 부여: 후보자가 설명할 수 있는 공간을 충분히 줌
  - 후속 관찰: 답변의 솔직함과 일관성에 집중
  - 감점 가능: 회피/거짓은 감점, 솔직함은 가산
```

---

## 7. 점수 체계

### 7.1 점수 구조

```yaml
scoring_structure:
  main_questions:
    total: ~500  # 25문항 × 평균 20점
    per_question:
      expert: 15-25
      mid: 8-12
      low: -10 ~ 5

  follow_up_bonus:
    total: ~125  # 최대 보너스 (25문항 × ~5점)
    per_follow_up:
      good: 5-10
      poor: -5 ~ 0

  grand_total: ~625  # 메인 + 꼬리질문 보너스

decision_thresholds:  # 만점 대비 비율 기반
  strong_hire: ">= 90%"   # 만점의 90% 이상
  hire: ">= 60%"          # 만점의 60% 이상
  maybe: ">= 35%"         # 만점의 35% 이상
  no_hire: "< 35%"        # 만점의 35% 미만
```

### 7.2 카테고리별 가중치

| 카테고리 | CTO 가중치 | 시니어 가중치 | 주니어 가중치 |
|---------|-----------|-------------|-------------|
| 역할 적합성 | 25% | 15% | 15% |
| 기술 역량 | 20% | 35% | 35% |
| 실행 & 오너십 | 20% | 25% | 20% |
| 소통 & 협업 | 20% | 10% | 10% |
| 위험 신호 검증 | 15% | 15% | 20% |

---

## 8. 프론트 뷰 인터랙션 명세

### 8.1 카테고리 섹션 네비게이션

- 각 카테고리를 **섹션 헤더**로 구분하여 시각적으로 그룹화
- 섹션 헤더: 아이콘 + 카테고리명 + 질문 수 + 해당 섹션 점수
- 섹션 간 이동 가능한 사이드 네비게이션 (스크롤 추적)

### 8.2 꼬리질문 인터랙션

```
1. 면접관이 메인 질문 채점 (Expert/Mid/Low 클릭)
2. 해당 수준의 꼬리질문만 자동으로 표시 (다른 수준은 완전히 숨김)
3. 꼬리질문 채점: Good/Poor 2단계 (선택적)
4. 꼬리질문 점수는 "보너스" 영역에 별도 합산
```

### 8.3 키워드 체크 인터랙션

```
1. 각 질문 하단에 "핵심 키워드" 영역 표시
2. [필수] 빨간 뱃지, [가산] 파란 뱃지
3. 면접관이 후보자 답변에서 키워드를 들으면 클릭하여 체크
4. 체크된 키워드 수로 추가 참고 정보 제공 (점수에 미반영, 참고용)
```

---

## 9. 향후 확장 계획

- [ ] 녹음 연동 시 키워드 자동 탐지
- [ ] 면접 후 리포트 자동 생성 (PDF)
- [ ] 다국어 질문 on-demand 번역
- [ ] A/B 테스트: 질문 조합별 면접 효과 측정
- [ ] 파인튜닝 피드백 루프: 면접 결과 → 질문 품질 개선

---

## 10. 비개발자 친화 원칙

### 10.1 핵심 원칙

비개발자 면접관이 기술 면접을 진행할 수 있도록 모든 컨텐츠는 **일상 언어와 비유**로 작성합니다.

### 10.2 구체적 작성 규칙

#### 금지 표현 예시
| ❌ 추상적 표현 | ✅ 구체적 설명 |
|--------------|--------------|
| "스케일링 전략 부족" | "많은 사용자가 동시 접속할 때 대응 방법을 모름" |
| "아키텍처 설계 미흡" | "시스템을 어떻게 나눌지 계획이 없음" |
| "코드 품질 낮음" | "다른 개발자가 이해하기 어렵게 작성됨" |
| "기술 부채 누적" | "나중에 고치기 힘든 임시방편 코드가 쌓임" |
| "리팩토링 필요" | "더 깔끔하게 다시 작성해야 함" |

#### 코드 참조 표현 규칙
모든 코드 참조는 다음 형식으로 작성:

```
"어떤 저장소의 어떤 파일 몇 번째 줄에서 무엇을 하는지"

예시:
✅ "user/e-commerce 저장소의 src/payment/processor.py 파일 45-67번째 줄에서
    결제 처리 로직을 구현했습니다. 여기서 신용카드 정보를 어떻게 안전하게
    처리하는지 확인할 수 있습니다."

❌ "payment processor implementation in the codebase"
```

#### 예상 답변 작성 원칙

**CTO/VP 수준 예상 답변:**
```yaml
비유_중심:
  - "마치 큰 배를 운항하면서 동시에 선체를 수리하는 것처럼..."
  - "레고 블록을 하나씩 교체하듯이..."

전략적_맥락:
  - "왜 그 시점에 그 결정을 했는지"
  - "팀을 어떻게 설득했는지"
  - "실패했을 때 어떻게 대응했는지"

조직_영향:
  - "팀 구조를 어떻게 재편했는지"
  - "이해관계자들과 어떻게 소통했는지"
```

**시니어 수준 예상 답변:**
```yaml
구체적_수치:
  - "응답 시간이 500ms에서 50ms로 개선"
  - "메모리 사용량 30% 감소"
  - "배포 시간 2시간에서 10분으로 단축"

기술_선택_근거:
  - "Redis를 선택한 이유: 속도가 필요했고, 데이터가 날아가도 괜찮았기 때문"
  - "Kafka 대신 RabbitMQ: 팀이 익숙하고, 우리 규모에서는 충분했음"

실제_경험:
  - "처음에는 X를 시도했다가 Y 문제로 실패"
  - "결국 Z 방법으로 해결"
  - "이 경험에서 A를 배움"
```

**주니어 수준 예상 답변:**
```yaml
개념_이해:
  - "REST API는 웹에서 데이터를 주고받는 규칙입니다"
  - "왜냐하면 모든 프로그램이 같은 방식으로 통신해야 하니까요"

학습_과정:
  - "처음에는 이해가 안 됐지만, 튜토리얼을 따라하면서 배웠습니다"
  - "에러가 나면 구글링하고, 스택오버플로우를 찾아봤습니다"
  - "선배 개발자에게 질문해서 해결했습니다"

성장_의지:
  - "아직 모르는 게 많지만, 계속 공부하고 싶습니다"
  - "다음에는 더 나은 방법으로 구현하고 싶습니다"
```

#### 면접관 참고 노트 작성 규칙

기존 "예상 답변"을 **"면접관 참고 노트"**로 리네이밍하고 다음 섹션으로 구성:

```yaml
비개발자_관점_해석:
  purpose: "기술 답변을 비즈니스/조직 관점으로 번역"
  example:
    기술_답변: "마이크로서비스로 전환했습니다"
    비개발자_해석: "큰 시스템을 작은 조각으로 나눠서, 한 팀이 한 조각만 책임지게 만들었습니다.
                   이렇게 하면 한 부분이 고장나도 전체가 멈추지 않고, 팀들이 독립적으로 일할 수 있습니다."

일상_비유:
  purpose: "왜 이 답변이 좋은지/나쁜지를 일상 경험으로 설명"
  good_answer_analogy:
    - "집을 리모델링할 때 먼저 골조를 확인하는 것처럼, 시스템의 기초부터 점검했다는 답변"
    - "요리할 때 재료를 먼저 준비하듯, 계획을 세우고 실행했다는 과정"

  poor_answer_analogy:
    - "지도 없이 여행하는 것처럼, 계획 없이 시작했다는 신호"
    - "불이 난 후에 소화기를 사는 것처럼, 문제가 생긴 후에야 대응했다는 의미"

직급별_기대치:
  CTO:
    - "전략: 왜 그 방향을 선택했는지, 다른 옵션은 무엇이었는지"
    - "조직: 팀을 어떻게 움직였는지, 갈등을 어떻게 해결했는지"
    - "영향: 비즈니스에 어떤 영향을 줬는지, 수치로 설명할 수 있는지"

  시니어:
    - "깊이: 기술적 선택의 이유를 명확히 설명할 수 있는지"
    - "경험: 실제 프로젝트에서 직접 해본 것인지, 책으로만 아는지"
    - "멘토링: 주니어에게 어떻게 가르칠 것인지 말할 수 있는지"

  주니어:
    - "이해: 개념을 자기 말로 설명할 수 있는지"
    - "태도: 모르는 것을 인정하고, 배우려는 자세가 있는지"
    - "성장: 실수에서 무엇을 배웠는지 말할 수 있는지"
```

### 10.3 용어 설명 작성 예시

```python
# ❌ 나쁜 예시
TerminologyEntry(
    term="Circuit Breaker Pattern",
    definition="A design pattern used in modern software development...",
    plain_language_explanation="Circuit breaker pattern",  # 그대로 반복
    context="Used in microservices"
)

# ✅ 좋은 예시
TerminologyEntry(
    term="Circuit Breaker Pattern",
    definition="시스템 장애 전파를 막기 위한 설계 패턴. 호출 실패가 임계치를 넘으면 자동으로 차단.",
    plain_language_explanation="""집에 있는 두꺼비집(차단기)과 똑같습니다.
        전기가 너무 많이 흐르면 자동으로 전기를 차단해서 집이 불나는 걸 막죠.
        프로그램도 마찬가지로, 한 부분에서 계속 에러가 나면 자동으로 차단해서
        전체 시스템이 다운되는 걸 막습니다.""",
    context="마이크로서비스 시스템에서 한 서비스의 장애가 다른 서비스로 번지는 것을 방지하기 위해 사용"
)
```

### 10.4 검증 체크리스트

모든 면접 스크립트 생성 시 다음 항목을 검증:

- [ ] 모든 기술 용어에 `plain_language_explanation` 포함
- [ ] 코드 참조는 "저장소명/파일경로/라인번호" 형식
- [ ] 예상 답변은 비유와 구체적 수치 포함
- [ ] "면접관 참고 노트"에 비개발자 관점 해석 포함
- [ ] 추상적 표현 금지 (스케일링, 아키텍처 등 → 구체적 설명)
- [ ] 모든 설명이 "초등학생도 이해할 수 있는" 수준

---

## 11. Multi-Agent Roles (Phase 3 상세)

Phase 3 QUESTION GENERATION은 8개의 전문화된 에이전트가 순차/병렬로 협업하여 완성됩니다.

### 11.1 Agent Execution Flow

```
3a. Topic Selector Agent (순차)
      ↓
3b. Question Crafter Agent (병렬 10개)
      ↓
┌─────────────────────────────────────────┐
│ 3c. Terminology Agent (병렬)             │
│ 3d. Scenario Writer Agent (병렬)         │
│ 3e. Follow-up Designer Agent (병렬)      │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│ 3f. Interviewer Note Agent (병렬)        │
│ 3g. Decision Guide Agent (병렬)          │
└─────────────────────────────────────────┘
      ↓
3h. Quality Reviewer Agent (순차, 최대 3회 반복)
```

### 11.2 Agent Specifications

#### 3a. Topic Selector Agent

**Responsibility:** 10개의 면접 질문 주제를 선정

**Input:**
```python
{
    "job_id": str,
    "aggregated_analysis": {
        "document_analysis": dict,  # 이력서/포트폴리오 분석
        "code_analysis": dict,      # GitHub 코드 분석
        "jd_analysis": dict,        # 채용공고 분석
    },
    "enriched_input": {
        "raw_input": dict,          # 경력 레벨, 최대 질문 수 등
        "github_urls": list,
        "linkedin_profile": dict,
    }
}
```

**Output:**
```python
[
    {
        "topic": "MSA 전환 경험",
        "source": "code",  # code | jd_match | document
        "evidence": {...},
        "category": "technical_depth",
        "score": 0.85,
        "rationale": "후보자가 실제로 모놀리스를 MSA로 전환한 커밋이 발견됨"
    },
    # ... 총 10개
]
```

**Prompt Guidelines:**
```yaml
selection_criteria:
  - 코드에서 발견된 주목할 만한 구현 우선
  - JD 핵심 요구사항과 매칭되는 주제
  - 경력 레벨에 맞는 난이도 분포 (CTO/시니어/주니어)
  - 카테고리별 배분 준수 (role_fit: 2, technical_depth: 2-3, ...)

avoid:
  - 코드 증거가 없는 추상적 질문
  - 이력서에만 언급된 허위 가능 항목
  - JD와 무관한 기술
```

---

#### 3b. Question Crafter Agent

**Responsibility:** 질문 본체 생성 (병렬 10개)

**Input (per question):**
```python
{
    "job_id": str,
    "topic": {
        "topic": str,
        "source": str,
        "evidence": dict,
        "category": QuestionCategory,
    },
    "aggregated_analysis": dict,
    "enriched_input": dict,
}
```

**Output (per question):**
```python
{
    "id": "q1",
    "sequence": 1,
    "category": "technical_depth",
    "topic": "MSA 전환 경험",
    "difficulty": "hard",
    "question_text": "...",
    "context_bridge": "...",
    "alternative_phrasings": [...],
    "why_matters": "...",
    "listen_for": "...",
    "code_reference": CodeReference | None,
    "expected_answer": {
        "core_answer": "...",
        "example_script": "...",
        "answer_keywords": [...]  # 핵심 키워드 (must/good_to_have)
    },
    "language": "ko",
    "estimated_time_minutes": 8,
    "skills_assessed": ["system_design", "migration_strategy"],
    "generation_rationale": "...",
    "jd_competency_link": "...",
}
```

**Prompt Guidelines:**
```yaml
question_style_by_level:
  CTO:
    - 시나리오 기반 ("이런 상황에서 어떻게?")
    - 의사결정 프레임워크 요구 ("기준은 무엇이며, 왜?")
    - 트레이드오프 탐색 ("A vs B, 어떤 것을 왜?")
  시니어:
    - 구체적 기술 시나리오 ("이 시스템을 설계해주세요")
    - 코드 기반 질문 ("이 코드에서 어떤 문제가?")
  주니어:
    - 개념 확인 ("X가 무엇이고 왜 중요한가요?")
    - 문제 해결 과정 ("이 버그를 어떻게 디버깅?")

code_reference_rules:
  - 코드가 있으면 반드시 포함
  - 저장소명/파일경로/라인번호 명시
  - plain_language_summary 필수 (비개발자용)
  - GitHub permalink 생성

jd_competency_link_required:
  - 모든 질문은 JD 요구사항과 연결
  - 예: "채용공고 요구사항: 'MSA 설계 경험 3년 이상' → 이 질문으로 실제 전환 경험 검증"
```

---

#### 3c. Terminology Agent

**Responsibility:** 모든 기술 용어 설명 생성 및 비개발자 친화 검증

**Input:**
```python
{
    "job_id": str,
    "questions": [  # 3b에서 생성된 질문들
        {
            "id": "q1",
            "question_text": "...",
            "code_reference": {...},
            "expected_answer": {...},
            # ... 기타 필드
        },
        # ... 10개
    ]
}
```

**Output:**
```python
{
    "q1": [
        {
            "term": "Strangler Fig Pattern",
            "definition": "시스템 장애 없이 레거시를 점진적으로 교체하는 패턴",
            "plain_language_explanation": """오래된 집을 부수지 않고,
                옆에 새 집을 지으면서 하나씩 이사가는 것과 비슷합니다.
                한번에 바꾸면 위험하니, 조금씩 옮기면서 안전하게 전환하는 방법입니다.""",
            "context": "이 질문에서 MSA 전환 전략을 평가하기 위해 사용"
        },
        {
            "term": "API Gateway",
            "definition": "마이크로서비스의 단일 진입점 역할을 하는 서버",
            "plain_language_explanation": """호텔 프론트 데스크처럼,
                손님(요청)이 어느 방(서비스)으로 가야 할지 안내해주는 역할입니다.""",
            "context": "MSA 아키텍처에서 서비스 간 통신 관리를 이해하기 위해"
        },
        # ...
    ],
    "q2": [...],
    # ... 10개 질문 모두
}
```

**Prompt Guidelines:**
```yaml
terminology_checklist:
  scan_targets:
    - question_text (모든 기술 용어)
    - code_reference.snippet (코드 내 용어)
    - expected_answer.core_answer (답변 예시의 용어)

  extraction_rules:
    - 프레임워크명: React, FastAPI, PostgreSQL → 설명 필수
    - 아키텍처 패턴: MSA, CQRS, Event Sourcing → 설명 필수
    - 디자인 패턴: Singleton, Factory, Observer → 설명 필수
    - 약어: API, REST, JWT, CI/CD → 풀네임 + 설명 필수
    - 알고리즘/자료구조: Hash Table, Binary Search → 설명 필수

  non_technical_validation:
    assumption: "비개발자 = 프로그래밍 지식 제로"
    test_question: "비개발 HR 담당자가 이 설명을 읽고 이해할 수 있는가?"

  plain_language_principles:
    - 일상 비유 사용 (집, 호텔, 요리, 여행 등)
    - 초등학생도 이해 가능한 수준
    - 추상적 표현 금지 ("효율적", "최적화" → 구체적 설명)
    - "무엇을 하는지" + "왜 필요한지" 모두 설명

forbidden_explanations:
    - ❌ "Strangler Fig Pattern은 마이크로서비스 전환 패턴입니다"
    - ❌ "API Gateway는 게이트웨이입니다"
    - ❌ "효율적인 데이터 구조입니다"
    - ✅ "오래된 집을 부수지 않고 옆에 새 집을 지으면서..."
```

---

#### 3d. Scenario Writer Agent

**Responsibility:** 채점 시나리오 텍스트 생성 (우수/보통/미흡)

**Input:**
```python
{
    "job_id": str,
    "questions": [...]  # 3b에서 생성된 질문들
    "enriched_input": {
        "raw_input": {
            "experience_level": "CTO" | "시니어" | "주니어"
        }
    }
}
```

**Output:**
```python
{
    "q1": {
        "expert": {
            "description": "전략적 사고 + 조직 관점의 구체적 경험",
            "indicators": [
                "Strangler Fig Pattern 언급",
                "팀 재편 방법 설명",
                "이해관계자 설득 과정 공유",
                "실패 시 Plan B 준비"
            ],
            "score": 20
        },
        "mid": {
            "description": "기술적 이해는 있으나 경험 깊이 부족",
            "indicators": [
                "MSA 개념 이해",
                "전환 과정은 설명하지만 구체성 부족",
                "조직 영향 언급 없음"
            ],
            "score": 10
        },
        "low": {
            "description": "개념 이해 부족 또는 경험 없음",
            "indicators": [
                "MSA가 무엇인지 모름",
                "전환 경험이 실제로 없음",
                "회피성 답변"
            ],
            "score": 0
        }
    },
    # ... 10개 질문 모두
}
```

**Prompt Guidelines:**
```yaml
scenario_principles:
  expert_level:
    - 레벨별 기대치 반영 (CTO: 전략, 시니어: 기술 깊이, 주니어: 개념 이해)
    - 구체적 지표 5-7개
    - 핵심 키워드 포함 여부 체크
    - 경험의 진정성 판단 기준

  mid_level:
    - "알지만 경험 부족" 시나리오
    - 만회 기회 부여 (꼬리질문으로 깊이 탐색)

  low_level:
    - "모름" vs "회피" 구분
    - 솔직함은 가산점, 거짓은 감점

  tone:
    - 비난 금지, 객관적 관찰
    - "이런 답변이 나오면 이 수준으로 판단" 형태
```

---

#### 3e. Follow-up Designer Agent

**Responsibility:** 꼬리질문 설계 (답변 수준별 분기)

**Input:**
```python
{
    "job_id": str,
    "questions": [...]  # 3b에서 생성된 질문들
    "enriched_input": {...}
}
```

**Output:**
```python
{
    "q1": [
        {
            "id": "q1-f1",
            "trigger_level": "expert",
            "question_text": "그 전략이 실패했다면 Plan B는 무엇이었나요?",
            "why_matters": "진짜 전문가는 항상 백업 계획을 가지고 있음",
            "listen_for": "구체적 대안, 리스크 평가 과정",
            "scoring": {
                "good": "구체적 Plan B + 리스크 평가 과정 설명",
                "good_score": 8,
                "poor": "Plan B 없었음 또는 회피",
                "poor_score": 0
            },
            "terminology": [...]
        },
        {
            "id": "q1-f2",
            "trigger_level": "mid",
            "question_text": "구체적으로 어떤 프로젝트에서 그 경험을 하셨나요?",
            "why_matters": "경험의 진정성 확인",
            "listen_for": "프로젝트명, 시기, 역할, 결과 수치",
            "scoring": {...}
        },
        {
            "id": "q1-f3",
            "trigger_level": "low",
            "question_text": "MSA가 무엇인지는 알고 계신가요?",
            "why_matters": "진짜 모르는지, 긴장인지 구분",
            "listen_for": "기본 개념 이해도, 솔직함",
            "scoring": {...}
        }
    ],
    # ... 10개 질문 모두
}
```

**Prompt Guidelines:**
```yaml
follow_up_design:
  expert_trigger:
    purpose: "더 깊이 파고들기, 추가 가산점 기회"
    examples:
      - "그 전략이 실패했다면?"
      - "다른 팀에서는 어떻게 적용했나요?"
      - "지금 다시 한다면 무엇을 바꾸시겠습니까?"

  mid_trigger:
    purpose: "구체성 유도, 만회 기회"
    examples:
      - "구체적으로 어떤 프로젝트에서?"
      - "그 기술을 선택한 이유는?"
      - "어려웠던 점은 무엇이었나요?"

  low_trigger:
    purpose: "기본 확인, 긴장 vs 무지 구분"
    examples:
      - "X 개념은 알고 계신가요?"
      - "비슷한 경험이라도 있으신가요?"
      - "어떤 부분이 어려우셨나요?"

  scoring:
    - 메인 질문: 0-25점
    - 꼬리질문: -5 ~ +10점 (보너스)
    - 꼬리질문은 선택적 (시간/상황 따라)
    - Good/Poor 2단계만 (간소화)
```

---

#### 3f. Interviewer Note Agent

**Responsibility:** 면접관 참고 노트 생성 (비개발자 관점 해석)

**Input:**
```python
{
    "job_id": str,
    "questions": [...]  # 3b-3e까지 Enhancement된 질문들
    "enriched_input": {...}
}
```

**Output:**
```python
{
    "q1": {
        "non_technical_interpretation": """비개발자 관점:
            이 질문은 후보자가 큰 변화를 어떻게 관리하는지 확인합니다.
            기술적으로는 '마이크로서비스 전환'이지만, 본질은
            '오래된 시스템을 안전하게 새 시스템으로 바꾸는 능력'입니다.

            비즈니스 임팩트:
            - 시스템 중단 없이 변화 관리 → 매출 손실 방지
            - 팀 재편 능력 → 조직 효율성 향상
            - 이해관계자 설득 → 리더십 역량""",

        "everyday_analogy": {
            "good_answer": """집을 리모델링할 때 먼저 골조를 확인하고,
                살면서 조금씩 고치는 것처럼, 시스템도 한번에 바꾸지 않고
                단계적으로 전환했다는 답변입니다.""",

            "poor_answer": """지도 없이 여행하는 것처럼, 계획 없이
                시작했다는 신호입니다. 이런 접근은 프로젝트 실패 위험이 높습니다."""
        },

        "level_expectations": {
            "CTO": """전략적 사고 + 조직 영향:
                - 왜 그 시점에 전환했는지 (비즈니스 근거)
                - 팀을 어떻게 재편했는지 (조직 설계)
                - 이해관계자를 어떻게 설득했는지 (리더십)
                - 실패 시 Plan B가 있었는지 (리스크 관리)""",

            "시니어": """기술 깊이 + 실무 경험:
                - 어떤 기술을 선택했고 왜? (의사결정)
                - 성능 개선 수치는? (결과 측정)
                - 어려웠던 점과 해결 방법? (문제 해결)
                - 주니어에게 어떻게 가르칠 것인지? (멘토링)""",

            "주니어": """개념 이해 + 학습 태도:
                - MSA가 무엇인지 자기 말로 설명 가능? (개념 이해)
                - 프로젝트에서 어떤 역할? (경험 범위)
                - 어려운 점을 어떻게 해결? (학습 능력)
                - 무엇을 배웠는지? (성장 의지)"""
        }
    },
    # ... 10개 질문 모두
}
```

**Prompt Guidelines:**
```yaml
interviewer_note_structure:
  non_technical_interpretation:
    - 기술 용어를 비즈니스 언어로 번역
    - 이 질문이 "진짜 무엇을 확인하는지" 설명
    - 비즈니스 임팩트 연결

  everyday_analogy:
    - 일상 경험으로 설명 (집, 요리, 여행 등)
    - 좋은 답변 비유 + 나쁜 답변 비유
    - "왜 이 답변이 좋은/나쁜지" 설명

  level_expectations:
    - CTO: 전략, 조직, 리더십
    - 시니어: 기술 깊이, 실무 경험, 멘토링
    - 주니어: 개념 이해, 학습 태도, 성장 의지

forbidden_expressions:
    - ❌ "스케일링 전략 부족" → ✅ "많은 사용자가 동시 접속할 때 대응 방법 모름"
    - ❌ "아키텍처 설계 미흡" → ✅ "시스템을 어떻게 나눌지 계획 없음"
    - ❌ "코드 품질 낮음" → ✅ "다른 개발자가 이해하기 어렵게 작성"
```

---

#### 3g. Decision Guide Agent

**Responsibility:** 이력서/커버레터 기반 면접관 가이드 생성

**Input:**
```python
{
    "job_id": str,
    "aggregated_analysis": {
        "document_analysis": {  # 이력서 분석
            "name": str,
            "experience_years": int,
            "work_history": [...],
            "projects": [...],
            "strengths": [...],
            "gaps": [...]
        },
        "code_analysis": {...},
        "jd_analysis": {...}
    },
    "enriched_input": {
        "raw_input": {
            "cover_letter": str | None
        },
        "github_urls": [...],
        "linkedin_profile": {...}
    }
}
```

**Output:**
```python
{
    "candidate_summary": {
        "name": "홍길동",
        "experience_years": 7,
        "current_level": "시니어",
        "jd_match_score": 0.78,
        "key_strengths": [
            "Backend API 설계 경험 풍부 (5년)",
            "MSA 전환 프로젝트 리드 경험",
            "팀 멘토링 경험 (3명)"
        ],
        "areas_to_probe": [
            "프론트엔드 경험 부족 (JD 요구사항과 갭)",
            "최근 1년 GitHub 활동 저조 (왜?)",
            "이직 사유 확인 필요 (2년마다 이직)"
        ]
    },

    "resume_based_tips": [
        {
            "source": "이력서 - ABC사 재직 기간",
            "tip": "MSA 전환 프로젝트를 주도했다고 하는데, Q3(MSA 전환 질문)에서 구체적 역할과 의사결정 과정 확인",
            "related_question_ids": ["q3", "q5"]
        },
        {
            "source": "이력서 - 경력 공백",
            "tip": "2022년 6월~12월 6개월 공백 → 위험 신호 질문에서 확인",
            "related_question_ids": ["q9"]
        }
    ],

    "cover_letter_insights": [
        {
            "claim": "팀 문화 개선에 기여했다고 주장",
            "verification": "Q7(소통&협업)에서 구체적 사례 요청. 숫자로 증명 가능한지 확인",
            "related_question_ids": ["q7"]
        }
    ] | None,  # 커버레터 없으면 None

    "interview_flow": {
        "suggested_order": [
            {
                "phase": "워밍업 (5분)",
                "questions": ["q1"],
                "goal": "긴장 완화, 라포 형성"
            },
            {
                "phase": "핵심 역량 확인 (30분)",
                "questions": ["q2", "q3", "q4", "q5", "q6"],
                "goal": "기술 역량 + 실행력 검증"
            },
            {
                "phase": "위험 신호 확인 (10분)",
                "questions": ["q8", "q9"],
                "goal": "우려사항 직접 확인, 솔직함 평가"
            },
            {
                "phase": "마무리 (5분)",
                "questions": ["q10"],
                "goal": "역질문 기회 제공"
            }
        ],
        "total_estimated_time": "50분"
    },

    "time_allocation": {
        "per_question_average": "5분",
        "flexible_questions": ["q3", "q5"],  # 답변 좋으면 더 파고들기
        "quick_questions": ["q1", "q10"],    # 워밍업/마무리
        "buffer_time": "10분"
    },

    "red_flags_to_watch": [
        {
            "flag": "이력서와 코드 활동 불일치",
            "detail": "이력서: 'React 프로젝트 3년' / GitHub: React 커밋 10개 미만",
            "how_to_verify": "Q4에서 구체적 프로젝트명, 코드 리뷰 경험 질문",
            "related_question_ids": ["q4", "q9"]
        },
        {
            "flag": "짧은 재직 기간 반복",
            "detail": "평균 재직 2년, 3번 이직",
            "how_to_verify": "이직 사유 질문 (우리 회사도 2년 만에 떠날까?)",
            "related_question_ids": ["q8"]
        }
    ],

    "positive_signals_to_explore": [
        {
            "signal": "오픈소스 기여 활발",
            "detail": "FastAPI 프로젝트에 PR 5개 머지됨",
            "how_to_leverage": "Q6에서 오픈소스 기여 경험 상세히 듣기, 커뮤니티 활동 확인",
            "related_question_ids": ["q6"]
        }
    ]
}
```

**Prompt Guidelines:**
```yaml
decision_guide_principles:
  candidate_summary:
    - 한눈에 파악 가능한 요약
    - 강점 3-5개, 확인 필요 사항 3-5개
    - JD 매칭 점수와 근거

  resume_based_tips:
    - 이력서 주장을 질문으로 검증하는 방법
    - "~했다"는 주장 → 구체적 증거 요구
    - 경력 공백, 짧은 재직 → 위험 신호 질문 연결

  cover_letter_insights:
    - 커버레터가 있을 때만 생성
    - "열정", "팀워크" 같은 추상적 주장 → 구체적 사례 요구
    - 커버레터 톤/스타일 분석 (솔직함 vs 과장)

  interview_flow:
    - 워밍업 → 핵심 역량 → 위험 신호 → 마무리 순서
    - 시간 배분 가이드
    - 유연하게 조정 가능한 질문 표시

  red_flags_to_watch:
    - 자동 탐지된 위험 신호 (이력서/코드 불일치, 경력 공백 등)
    - 어떻게 확인할지 구체적 방법
    - 관련 질문 ID 연결

  positive_signals_to_explore:
    - 후보자의 강점을 더 깊이 탐색하는 방법
    - 오픈소스, 블로그, 발표 경험 등
```

---

#### 3h. Quality Reviewer Agent

**Responsibility:** 최종 검토 및 종합 (기존 review_questions Activity)

**Input:**
```python
{
    "job_id": str,
    "questions": [...]  # 3a-3g까지 모든 Enhancement 완료된 질문들
}
```

**Output:**
```python
{
    "verdict": "APPROVED" | "NEEDS_REVISION",
    "issues": [
        {
            "type": "duplicate",
            "questions": ["q2", "q5"],
            "similarity": 0.85,
            "recommendation": "q5를 다른 주제로 교체"
        },
        {
            "type": "terminology_missing",
            "question": "q3",
            "missing_terms": ["Circuit Breaker"],
            "recommendation": "용어 설명 추가"
        },
        {
            "type": "non_technical_validation_failed",
            "question": "q7",
            "problem": "plain_language_explanation이 여전히 추상적",
            "example": "'효율적인 구조' → 구체적 설명 필요"
        }
    ],
    "questions_to_revise": ["q3", "q5", "q7"],
    "feedback": {
        "details": {
            "q3": {
                "reason": "용어 설명 누락",
                "action": "Terminology Agent 재실행"
            },
            "q5": {
                "reason": "q2와 중복",
                "action": "새 주제로 교체"
            },
            "q7": {
                "reason": "비개발자 친화 검증 실패",
                "action": "Interviewer Note Agent 재작성"
            }
        }
    }
}
```

**Prompt Guidelines:**
```yaml
quality_checks:
  1_duplicate_check:
    - question_text 유사도 0.8 이상 → 중복 판정
    - category가 같으면 더 엄격하게 (0.7 이상도 중복)

  2_code_reference_validation:
    - code_reference가 있으면 vector_store로 실제 존재 확인
    - permalink 유효성 검증
    - plain_language_summary 존재 확인

  3_terminology_completeness:
    - 모든 기술 용어에 plain_language_explanation 있는지
    - "비개발자가 이해 가능한가?" 검증
    - 추상적 표현 금지 목록 체크

  4_category_distribution:
    - 카테고리별 질문 수 균형 (role_fit: 2, technical: 2-3, ...)
    - 난이도 분포 적절한지 (CTO: easy 2 / mid 5 / hard 3)

  5_follow_up_quality:
    - 모든 질문에 expert/mid/low 꼬리질문 있는지
    - 꼬리질문 채점 시나리오 명확한지

  6_interviewer_note_validation:
    - non_technical_interpretation 존재하는지
    - everyday_analogy가 실제 일상 비유인지 (기술 용어 재사용 금지)
    - level_expectations가 직급별로 차별화되어 있는지

revision_loop:
  - max 3회 반복
  - 각 반복마다 revise_questions Activity 호출
  - 특정 Agent만 재실행 (예: Terminology Agent만)
  - 3회 후에도 실패 시 경고와 함께 진행
```

---

### 11.3 Agent Parallelization Benefits

```yaml
sequential_execution_time:  # 순차 실행 시
  3a: 30s
  3b: 10문 × 60s = 600s
  3c: 120s
  3d: 90s
  3e: 120s
  3f: 90s
  3g: 60s
  3h: 180s
  total: ~21분

parallel_execution_time:  # 병렬 실행 시
  3a: 30s
  3b: 60s (병렬)
  3c+3d+3e: 120s (병렬, 가장 긴 것 기준)
  3f+3g: 90s (병렬)
  3h: 180s
  total: ~8분

time_saved: 13분 (62% 단축)
```

### 11.4 Error Handling per Agent

```yaml
agent_error_strategies:
  3a_topic_selector:
    failure: "토픽 선정 실패 → 워크플로우 중단 (재시도 3회)"

  3b_question_crafter:
    failure: "특정 질문 생성 실패 → 해당 질문만 재생성 (나머지 진행)"

  3c_terminology:
    failure: "용어 설명 실패 → 기본 정의만 제공하고 진행"

  3d_scenario_writer:
    failure: "시나리오 생성 실패 → 템플릿 기반 기본 시나리오 제공"

  3e_follow_up:
    failure: "꼬리질문 실패 → 해당 질문의 꼬리질문 없이 진행"

  3f_interviewer_note:
    failure: "노트 생성 실패 → 기본 템플릿 제공하고 진행"

  3g_decision_guide:
    failure: "가이드 생성 실패 → 기본 가이드 제공하고 진행"

  3h_quality_reviewer:
    failure: "검토 실패 → 경고 로그 남기고 그대로 진행 (최대 3회 재시도 후)"
```

---

## Version History

## 12. Demo Scenario 직급별 분리

### 12.1 시나리오 구조

데모용 3개 시나리오는 각각 다른 직급의 후보자를 면접하는 상황을 보여줍니다.

| 시나리오 | 후보자 | 지원 직급 | 회사 맥락 | JD Match |
|---------|--------|----------|----------|----------|
| Alex Chen | 7년 경력 Engineering Lead | **CTO** | Series A FinTech | 78% |
| Sarah Kim | 1.5년 경력 부트캠프 출신 | **주니어 프론트엔드 개발자** | Series B EdTech | 68% |
| James Park | 8년 경력 Senior Engineer | **시니어 백엔드 개발자** | Series B SaaS | 82% |

### 12.2 직급별 질문 특성

| 구분 | CTO (Alex) | 시니어 (James) | 주니어 (Sarah) |
|-----|-----------|---------------|---------------|
| **난이도** | 전략·조직·시스템 설계 | 설계·트레이드오프·멘토링 | 기초·학습·성장 가능성 |
| **기대 수준** | 비전 + 실행 계획 + 팀 빌딩 | 깊은 기술 역량 + 협업 | 기본기 + 성장 의지 |
| **대표 질문** | "첫 90일 우선순위" | "대용량 API 설계 고려사항" | "state와 props의 차이" |
| **평가 기준** | 경영 + 기술 + 리더십 | 기술 깊이 + 소통 | 학습 태도 + 기본 역량 |

### 12.3 시나리오 데이터 모델

```javascript
window.scenarioXxx = {
  candidate: { name, initials, role, company_context, experience, jd_match, level, current_title },
  intel: { jd_summary, jd_full, competencies, github, linkedin, linkedin_warning },
  analysis: { radar_candidate, radar_required, engineering_dna, risk_flags, skill_table, overall_match },
  decision: { summary, interviewer_guide },
  questions: [ /* 25개 질문 (카테고리별 5개), 각각 terminology 7-10개 포함 */ ]
};
```

각 시나리오 파일은 독립적이며, `index.html`에서 `registerScenario()`로 등록됩니다.

---

| 버전 | 날짜 | 변경 내용 |
|-----|------|----------|
| 1.0 | 2026-01-31 | 초기 출력 명세 작성 (카테고리, 꼬리질문, 키워드, 레벨별 차별화) |
| 1.1 | 2026-01-31 | 비개발자 친화 강화 업데이트:<br>- InterviewQuestion 모델 확장 (jd_competency_link, code_reference 상세화, terminology plain_language_explanation 추가)<br>- JDCompetencyMapping 모델 신규 추가<br>- 꼬리질문 인터랙션 개선 (선택한 수준만 표시, 다른 수준 완전 숨김)<br>- "예상 답변" → "면접관 참고 노트"로 리네이밍 및 차별화 (비개발자 관점 해석, 일상 비유, 직급별 기대치)<br>- Progressive disclosure 패턴 추가 (질문 카드 상태 관리)<br>- Section 10 "비개발자 친화 원칙" 신규 추가 (금지 표현, 코드 참조 규칙, 예상 답변 작성 원칙, 검증 체크리스트)<br>- 레벨별 예상 답변 수준 가이드 추가 (CTO/시니어/주니어) |
| 1.3 | 2026-02-01 | Demo Scenario 직급별 분리:<br>- 3개 시나리오를 직급별로 분리 (CTO / 시니어 / 주니어)<br>- Alex Chen: CTO 후보 (Series A FinTech)<br>- Sarah Kim: 주니어 프론트엔드 개발자 후보 (Series B EdTech)<br>- James Park: 시니어 백엔드 개발자 후보 (Series B SaaS)<br>- 각 시나리오에 직급 맞춤 JD, 질문 10개, 분석, 면접관 가이드 포함<br>- questionSets 하드코딩 제거, 모든 질문을 시나리오 파일 내부로 이동<br>- Section 12 "Demo Scenario 직급별 분리" 추가 |
| 1.4 | 2026-02-02 | 카테고리별 5문항 확장:<br>- 10문항 → 25문항 (카테고리별 2개 → 5개)<br>- 난이도 분포: Easy 2 / Medium 2 / Hard 1 per 카테고리<br>- 만점 200 → ~500 (동적 계산)<br>- 추천 임계값: 절대값 → 비율 기반 (90%/60%/35%)<br>- 시나리오 데이터 모델 questions 10개 → 25개 반영 |
| 1.2 | 2026-02-01 | Multi-Agent Architecture 추가:<br>- Section 11 "Multi-Agent Roles" 신규 추가<br>- Phase 3 QUESTION GENERATION을 8개 전문화된 에이전트로 분해<br>- 3a. Topic Selector Agent (주제 선정)<br>- 3b. Question Crafter Agent (질문 본체 생성, 병렬 10개)<br>- 3c. Terminology Agent (용어 설명 생성/검증, 비개발자 친화 체크리스트)<br>- 3d. Scenario Writer Agent (채점 시나리오 생성)<br>- 3e. Follow-up Designer Agent (꼬리질문 설계)<br>- 3f. Interviewer Note Agent (면접관 참고 노트 생성)<br>- 3g. Decision Guide Agent (이력서/커버레터 기반 면접관 가이드 생성)<br>- 3h. Quality Reviewer Agent (최종 검토/종합)<br>- 각 에이전트별 Input/Output/Responsibility/Prompt Guidelines 상세 정의<br>- 병렬 실행 전략 (3c+3d+3e 병렬, 3f+3g 병렬) → 실행 시간 62% 단축<br>- Agent별 Error Handling 전략 정의 |

---

*이전: [05-api-spec.md](./05-api-spec.md) | 상위: [ARCHITECTURE.md](./ARCHITECTURE.md)*
