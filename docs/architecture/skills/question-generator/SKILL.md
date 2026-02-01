# Question Generator Skill

> 면접 질문 생성 에이전트

---

## 역할

수집된 모든 분석 결과를 종합하여 맞춤형 면접 질문과 예상 답변 스크립트를 생성합니다.

## 책임

1. **컨텍스트 통합**: 문서/코드/JD 분석 결과 종합
2. **질문 후보 생성**: 다양한 유형의 질문 후보 생성
3. **질문 선별**: 중복 제거 및 난이도 균형 조정
4. **예상 답변 생성**: 각 질문에 대한 평가 기준과 모범 답변 작성
5. **스크립트 포맷팅**: 면접관용 최종 스크립트 생성

---

## Activity 정의

### generate_questions

```python
@activity.defn
async def generate_questions(
    job_id: str,
    context: dict,
    config: dict,
) -> dict:
    """
    면접 질문 생성

    Input:
        job_id: 작업 ID
        context: {
            candidate_profile: CandidateProfile,
            code_analysis: CodeAnalysis,
            jd_analysis: JDAnalysis,
        }
        config: {
            question_count: int,  # 기본 10개
            language: str,
            experience_level: str,
            difficulty_distribution: dict,  # easy/medium/hard 비율
        }

    Output:
        QuestionSet: {
            questions: list[InterviewQuestion],
            metadata: {
                total_count: int,
                categories: dict[str, int],
                avg_difficulty: float,
            },
            interview_script: str,
        }
    """
```

---

## 질문 유형 분류

```python
from enum import Enum
from dataclasses import dataclass

class QuestionCategory(Enum):
    """질문 카테고리"""
    TECHNICAL_CONCEPT = "technical_concept"  # 기술 개념
    CODE_IMPLEMENTATION = "code_implementation"  # 코드 구현
    ARCHITECTURE = "architecture"  # 아키텍처/설계
    PROBLEM_SOLVING = "problem_solving"  # 문제 해결
    EXPERIENCE_BASED = "experience_based"  # 경험 기반
    BEHAVIORAL = "behavioral"  # 행동 면접

class Difficulty(Enum):
    """난이도"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class InterviewQuestion:
    """면접 질문"""
    id: str
    question_text: str
    category: QuestionCategory
    difficulty: Difficulty
    time_limit_minutes: int
    source: str  # code/resume/jd
    evidence: str  # 질문 근거 (코드 스니펫, 경력 등)
    expected_answer: ExpectedAnswer
    follow_up_questions: list[str]
    terminology_hints: list[str]

@dataclass
class ExpectedAnswer:
    """예상 답변"""
    key_points: list[str]  # 반드시 포함해야 할 핵심 포인트
    good_answer_example: str  # 좋은 답변 예시
    poor_answer_indicators: list[str]  # 나쁜 답변 징후
    evaluation_criteria: dict[str, str]  # 평가 기준
    scoring_rubric: dict[str, int]  # 점수 기준
```

---

## 경험 레벨별 질문 전략

```python
EXPERIENCE_LEVEL_CONFIG = {
    "신입": {
        "difficulty_distribution": {
            "easy": 0.5,
            "medium": 0.4,
            "hard": 0.1,
        },
        "category_weights": {
            "technical_concept": 0.4,
            "code_implementation": 0.3,
            "problem_solving": 0.2,
            "behavioral": 0.1,
        },
        "focus_areas": [
            "기본 개념 이해도",
            "학습 의지",
            "잠재력",
            "문제 해결 접근법",
        ],
        "avoid": [
            "깊은 시스템 설계",
            "대규모 서비스 운영 경험",
        ],
    },
    "주니어": {
        "difficulty_distribution": {
            "easy": 0.3,
            "medium": 0.5,
            "hard": 0.2,
        },
        "category_weights": {
            "technical_concept": 0.3,
            "code_implementation": 0.35,
            "experience_based": 0.2,
            "problem_solving": 0.15,
        },
        "focus_areas": [
            "실무 적용 능력",
            "코드 품질 의식",
            "협업 경험",
        ],
    },
    "미들": {
        "difficulty_distribution": {
            "easy": 0.1,
            "medium": 0.5,
            "hard": 0.4,
        },
        "category_weights": {
            "architecture": 0.3,
            "code_implementation": 0.25,
            "experience_based": 0.25,
            "problem_solving": 0.2,
        },
        "focus_areas": [
            "설계 능력",
            "기술적 의사결정",
            "성능 최적화",
            "레거시 개선 경험",
        ],
    },
    "시니어": {
        "difficulty_distribution": {
            "easy": 0.0,
            "medium": 0.3,
            "hard": 0.7,
        },
        "category_weights": {
            "architecture": 0.35,
            "problem_solving": 0.25,
            "experience_based": 0.25,
            "behavioral": 0.15,
        },
        "focus_areas": [
            "시스템 설계",
            "기술 리더십",
            "트레이드오프 판단",
            "멘토링/코칭",
        ],
    },
}
```

---

## 질문 생성 파이프라인

### 1. 컨텍스트 통합

```python
async def integrate_context(
    profile: dict,
    code_analysis: dict,
    jd_analysis: dict,
) -> dict:
    """
    분석 결과 통합

    Returns:
        {
            "skill_match": {
                "matched": ["Python", "FastAPI", ...],
                "missing": ["Kubernetes", ...],
                "extra": ["Vue.js", ...],
            },
            "experience_match": {
                "relevant": [...],
                "gaps": [...],
            },
            "code_highlights": [...],
            "question_opportunities": [...],
        }
    """
    # JD 요구사항과 프로필 스킬 매칭
    required = set(jd_analysis.get("required_skills", []))
    candidate = set(profile.get("skills", []))

    skill_match = {
        "matched": list(required & candidate),
        "missing": list(required - candidate),
        "extra": list(candidate - required),
    }

    # 코드에서 질문 후보 추출
    code_highlights = []
    for impl in code_analysis.get("top_question_candidates", []):
        code_highlights.append({
            "title": impl["title"],
            "code": impl["code"],
            "why_notable": impl["why_notable"],
            "question_potential": impl["question_potential"],
        })

    return {
        "skill_match": skill_match,
        "code_highlights": code_highlights,
        "responsibilities": jd_analysis.get("responsibilities", []),
        "terminology": jd_analysis.get("terminology", []),
    }
```

### 2. 질문 후보 생성

```python
async def generate_question_candidates(
    integrated_context: dict,
    config: dict,
    llm_client,
) -> list[dict]:
    """
    LLM으로 질문 후보 생성

    전략:
    1. 코드 기반 질문 (구현 세부사항)
    2. 스킬 매칭 기반 질문 (강점/약점)
    3. JD 기반 질문 (역할 관련)
    4. 경험 기반 질문 (프로젝트 경험)
    """
    candidates = []

    # 코드 기반 질문
    for highlight in integrated_context["code_highlights"][:5]:
        questions = await llm_client.generate_code_questions(
            code=highlight["code"],
            title=highlight["title"],
            language=config["language"],
            experience_level=config["experience_level"],
        )
        candidates.extend(questions)

    # 스킬 기반 질문
    for skill in integrated_context["skill_match"]["matched"][:5]:
        questions = await llm_client.generate_skill_questions(
            skill=skill,
            language=config["language"],
            experience_level=config["experience_level"],
        )
        candidates.extend(questions)

    # 경험 기반 질문 (경력이 있는 경우)
    if config["experience_level"] != "신입":
        questions = await llm_client.generate_experience_questions(
            responsibilities=integrated_context["responsibilities"],
            language=config["language"],
            experience_level=config["experience_level"],
        )
        candidates.extend(questions)

    return candidates
```

### 3. 질문 선별 및 밸런싱

```python
async def select_and_balance_questions(
    candidates: list[dict],
    config: dict,
) -> list[dict]:
    """
    질문 선별 및 난이도/카테고리 균형 조정

    규칙:
    1. 중복 제거 (유사도 기반)
    2. 난이도 분포 맞추기
    3. 카테고리 다양성 확보
    4. 높은 품질 우선
    """
    level_config = EXPERIENCE_LEVEL_CONFIG[config["experience_level"]]
    target_count = config.get("question_count", 10)

    # 중복 제거
    unique = remove_duplicates(candidates, similarity_threshold=0.8)

    # 난이도별 목표 개수
    difficulty_targets = {
        diff: int(target_count * ratio)
        for diff, ratio in level_config["difficulty_distribution"].items()
    }

    # 카테고리별 목표 개수
    category_targets = {
        cat: int(target_count * ratio)
        for cat, ratio in level_config["category_weights"].items()
    }

    # 선별 알고리즘
    selected = []
    difficulty_counts = {d: 0 for d in difficulty_targets}
    category_counts = {c: 0 for c in category_targets}

    # 품질 순 정렬
    sorted_candidates = sorted(
        unique,
        key=lambda x: x.get("quality_score", 0),
        reverse=True,
    )

    for candidate in sorted_candidates:
        if len(selected) >= target_count:
            break

        diff = candidate["difficulty"]
        cat = candidate["category"]

        # 목표 도달 여부 체크
        if (difficulty_counts.get(diff, 0) < difficulty_targets.get(diff, 0) and
            category_counts.get(cat, 0) < category_targets.get(cat, float('inf'))):
            selected.append(candidate)
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            category_counts[cat] = category_counts.get(cat, 0) + 1

    return selected
```

---

## 예상 답변 생성

```python
async def generate_expected_answer(
    question: dict,
    context: dict,
    llm_client,
    language: str,
) -> ExpectedAnswer:
    """
    질문에 대한 예상 답변 생성

    포함 요소:
    1. 핵심 포인트 (반드시 언급해야 할 내용)
    2. 좋은 답변 예시
    3. 나쁜 답변 징후
    4. 평가 기준
    5. 점수 rubric
    """
    prompt = f"""
    다음 면접 질문에 대한 평가 가이드를 생성하세요.

    ## 질문
    {question["question_text"]}

    ## 질문 근거
    {question.get("evidence", "N/A")}

    ## 응답 형식 (JSON)
    {{
        "key_points": [
            "핵심 포인트 1 - 반드시 언급해야 함",
            "핵심 포인트 2",
            "핵심 포인트 3"
        ],
        "good_answer_example": "좋은 답변 예시 (2-3문장)",
        "poor_answer_indicators": [
            "이런 답변은 부족함을 나타냄",
            "이런 답변도 주의"
        ],
        "evaluation_criteria": {{
            "기술적 정확성": "개념을 정확히 이해하고 있는가",
            "실무 적용력": "실제 경험과 연결지어 설명하는가",
            "커뮤니케이션": "명확하고 논리적으로 설명하는가"
        }},
        "scoring_rubric": {{
            "5점": "모든 핵심 포인트를 정확히 설명하고 추가 인사이트 제공",
            "4점": "대부분의 핵심 포인트를 정확히 설명",
            "3점": "기본적인 이해는 있으나 깊이가 부족",
            "2점": "일부 이해는 있으나 중요한 부분 누락",
            "1점": "기본 개념 이해 부족"
        }}
    }}

    언어: {language}
    """

    response = await llm_client.generate(prompt)
    return ExpectedAnswer(**response)
```

---

## 면접 스크립트 포맷팅

```python
async def format_interview_script(
    questions: list[InterviewQuestion],
    terminology: list[dict],
    config: dict,
) -> str:
    """
    면접관용 최종 스크립트 생성

    구성:
    1. 면접 개요
    2. 질문별 상세 가이드
    3. 용어집 (면접관 참고용)
    4. 평가 요약표
    """
    language = config.get("language", "ko")

    script_parts = []

    # 1. 면접 개요
    script_parts.append(format_overview(questions, language))

    # 2. 질문별 가이드
    for i, q in enumerate(questions, 1):
        script_parts.append(format_question_guide(i, q, language))

    # 3. 용어집
    script_parts.append(format_terminology_section(terminology, language))

    # 4. 평가 요약표
    script_parts.append(format_evaluation_summary(questions, language))

    return "\n\n---\n\n".join(script_parts)


def format_question_guide(index: int, question: InterviewQuestion, language: str) -> str:
    """개별 질문 가이드 포맷"""
    templates = {
        "ko": """
## 질문 {index}: {category}

### 질문
> {question_text}

**난이도**: {difficulty} | **예상 소요 시간**: {time_limit}분

### 질문 의도
{evidence}

### 핵심 평가 포인트
{key_points}

### 좋은 답변 예시
{good_answer}

### 주의할 답변 패턴
{poor_indicators}

### 꼬리 질문 (선택)
{follow_ups}

### 관련 용어
{terminology_hints}
""",
        "en": """
## Question {index}: {category}

### Question
> {question_text}

**Difficulty**: {difficulty} | **Expected Time**: {time_limit} min

### Question Intent
{evidence}

### Key Evaluation Points
{key_points}

### Good Answer Example
{good_answer}

### Warning Signs
{poor_indicators}

### Follow-up Questions (Optional)
{follow_ups}

### Related Terms
{terminology_hints}
""",
    }

    template = templates.get(language, templates["en"])

    return template.format(
        index=index,
        category=question.category.value,
        question_text=question.question_text,
        difficulty=question.difficulty.value,
        time_limit=question.time_limit_minutes,
        evidence=question.evidence,
        key_points="\n".join(f"- {p}" for p in question.expected_answer.key_points),
        good_answer=question.expected_answer.good_answer_example,
        poor_indicators="\n".join(f"- {i}" for i in question.expected_answer.poor_answer_indicators),
        follow_ups="\n".join(f"- {f}" for f in question.follow_up_questions),
        terminology_hints=", ".join(question.terminology_hints),
    )
```

---

## 출력 예시

```json
{
  "questions": [
    {
      "id": "q-001",
      "question_text": "이 코드에서 Redis 캐싱을 구현하셨는데, 캐시 무효화 전략은 어떻게 설계하셨나요?",
      "category": "code_implementation",
      "difficulty": "medium",
      "time_limit_minutes": 5,
      "source": "code",
      "evidence": "app/services/user_service.py의 get_user_with_cache 함수에서 Redis 캐싱 구현 확인",
      "expected_answer": {
        "key_points": [
          "TTL(Time To Live) 기반 만료 전략",
          "데이터 변경 시 명시적 캐시 삭제",
          "캐시 스탬피드 방지를 위한 락 메커니즘"
        ],
        "good_answer_example": "TTL을 설정하여 자동 만료시키고, 사용자 정보 업데이트 시 해당 키를 삭제합니다. 캐시 스탬피드 방지를 위해 분산 락을 사용합니다.",
        "poor_answer_indicators": [
          "캐시 무효화를 고려하지 않음",
          "TTL만 의존하고 명시적 삭제 없음"
        ],
        "evaluation_criteria": {
          "기술적 정확성": "캐시 무효화 패턴을 정확히 이해하고 있는가",
          "실무 적용력": "실제 발생할 수 있는 문제(스탬피드 등)를 고려했는가"
        },
        "scoring_rubric": {
          "5점": "다양한 무효화 전략을 설명하고 트레이드오프 분석",
          "4점": "TTL과 명시적 삭제를 모두 설명",
          "3점": "기본적인 무효화 개념은 이해",
          "2점": "단편적인 이해",
          "1점": "캐시 무효화 개념 부재"
        }
      },
      "follow_up_questions": [
        "캐시 스탬피드가 발생하면 어떻게 대응하시겠습니까?",
        "분산 환경에서 캐시 일관성은 어떻게 유지하나요?"
      ],
      "terminology_hints": ["TTL", "Cache Invalidation", "Cache Stampede"]
    }
  ],
  "metadata": {
    "total_count": 10,
    "categories": {
      "code_implementation": 3,
      "technical_concept": 3,
      "experience_based": 2,
      "architecture": 2
    },
    "avg_difficulty": 2.3
  },
  "interview_script": "..."
}
```

---

## 관련 파일

- `backend/app/workflows/activities/question_generation.py`
- `backend/app/services/question_generator.py`
- `backend/app/prompts/question_generation/`

---

## 의존성

- **외부 서비스**: LLM (질문/답변 생성)
- **내부 서비스**: Vector Store (컨텍스트 조회)
- **입력 데이터**: CandidateProfile, CodeAnalysis, JDAnalysis
