# 04. 채용공고(JD) 분석

> AI를 활용하여 채용공고에서 면접 질문 기준 추출

---

## 목표

채용공고에서 필수/우대 기술, 역할 요구사항을 추출하고, 면접관용 기술 용어집을 생성합니다.

---

## 프롬프트 1: JD 구조화 분석

### AI 프롬프트

```
당신은 채용 전문가입니다. 다음 채용공고를 분석하여 구조화된 정보를 추출해주세요.

## 채용공고
[여기에 채용공고 전문을 붙여넣기]

## 추출할 정보
다음 JSON 형식으로 응답해주세요:

{
  "position": "포지션명",
  "department": "부서명 (없으면 null)",
  "experience_level": "신입/주니어/미들/시니어 중 추정",
  "experience_years": "N년 이상 (명시된 경우)",

  "required_skills": [
    {
      "skill": "기술명",
      "detail": "구체적 요구사항 (있으면)",
      "priority": "high/medium"
    }
  ],

  "preferred_skills": [
    {
      "skill": "기술명",
      "detail": "구체적 요구사항 (있으면)"
    }
  ],

  "responsibilities": [
    "담당 업무 1",
    "담당 업무 2"
  ],

  "qualifications": [
    "자격 요건 1",
    "자격 요건 2"
  ],

  "tech_keywords": ["모든 기술 키워드 목록"],

  "company_culture_hints": ["회사 문화 관련 키워드"],

  "red_flags_to_check": [
    "면접에서 확인해야 할 위험 신호 (예: 경력 부풀리기 가능성)"
  ]
}

정보가 명시되지 않은 경우 null 또는 빈 배열로 표시하세요.
```

### 예상 출력 예시

```json
{
  "position": "백엔드 개발자",
  "department": "플랫폼팀",
  "experience_level": "미들",
  "experience_years": "3년 이상",

  "required_skills": [
    {"skill": "Python", "detail": "3년 이상", "priority": "high"},
    {"skill": "FastAPI", "detail": "또는 Django", "priority": "high"},
    {"skill": "PostgreSQL", "detail": null, "priority": "high"},
    {"skill": "Docker", "detail": "기반 개발 경험", "priority": "medium"}
  ],

  "preferred_skills": [
    {"skill": "Kubernetes", "detail": "운영 경험"},
    {"skill": "Redis", "detail": null},
    {"skill": "대용량 트래픽", "detail": "처리 경험"}
  ],

  "responsibilities": [
    "REST API 설계 및 개발",
    "데이터베이스 설계 및 최적화",
    "CI/CD 파이프라인 구축",
    "코드 리뷰 및 기술 문서 작성"
  ],

  "tech_keywords": [
    "Python", "FastAPI", "Django", "PostgreSQL", "Docker",
    "Kubernetes", "Redis", "REST API", "CI/CD"
  ],

  "red_flags_to_check": [
    "Python 3년 경력 주장 시 깊이 확인 필요",
    "대용량 트래픽 경험 주장 시 구체적 수치 확인"
  ]
}
```

---

## 프롬프트 2: 기술 용어집 생성

### AI 프롬프트

```
다음 기술 키워드들에 대해 면접관용 용어집을 만들어주세요.
면접관은 비개발자일 수 있으므로, 쉽게 이해할 수 있는 설명이 필요합니다.

## 기술 키워드
[이전 단계에서 추출한 tech_keywords 목록]

## 요청사항
각 기술에 대해 다음 정보를 제공해주세요:

{
  "terminology": [
    {
      "term": "기술명",
      "simple_definition": "비개발자도 이해할 수 있는 1-2문장 설명",
      "technical_definition": "개발자용 정확한 정의",
      "category": "language/framework/database/devops/concept 중 하나",
      "difficulty": "basic/intermediate/advanced",
      "why_important": "이 기술이 왜 중요한지 (채용 관점)",
      "related_terms": ["관련 기술"],
      "good_sign": "지원자가 이 기술을 잘 아는 경우 보이는 신호",
      "warning_sign": "지원자가 이 기술을 모르는 경우 보이는 신호",
      "sample_questions": [
        "이 기술에 대해 물어볼 수 있는 간단한 질문 2개"
      ]
    }
  ]
}
```

### 예상 출력 예시

```json
{
  "terminology": [
    {
      "term": "FastAPI",
      "simple_definition": "Python으로 웹 서버를 만드는 도구입니다. 빠르고 현대적인 방식으로 API를 만들 수 있습니다.",
      "technical_definition": "Python 3.6+ 기반의 고성능 비동기 웹 프레임워크로, Starlette과 Pydantic을 기반으로 하며 자동 API 문서화를 제공합니다.",
      "category": "framework",
      "difficulty": "intermediate",
      "why_important": "최신 Python 웹 개발의 표준으로 자리잡고 있으며, 비동기 처리와 타입 안정성을 제공합니다.",
      "related_terms": ["Pydantic", "Starlette", "ASGI", "uvicorn"],
      "good_sign": "의존성 주입, Pydantic 모델, 비동기 처리에 대해 구체적으로 설명할 수 있음",
      "warning_sign": "Flask와의 차이점을 설명 못하거나, 비동기 개념을 이해 못함",
      "sample_questions": [
        "FastAPI를 선택한 이유가 무엇인가요?",
        "FastAPI에서 의존성 주입을 어떻게 사용하셨나요?"
      ]
    },
    {
      "term": "Docker",
      "simple_definition": "애플리케이션을 어디서든 동일하게 실행할 수 있도록 포장하는 기술입니다. 마치 택배 상자처럼 앱을 담아서 옮깁니다.",
      "technical_definition": "컨테이너 기반 애플리케이션 패키징 및 배포 플랫폼으로, OS 레벨 가상화를 통해 격리된 환경을 제공합니다.",
      "category": "devops",
      "difficulty": "basic",
      "why_important": "개발/테스트/배포 환경의 일관성을 보장하고, 마이크로서비스 아키텍처의 기반입니다.",
      "related_terms": ["컨테이너", "이미지", "Dockerfile", "docker-compose", "Kubernetes"],
      "good_sign": "Dockerfile 작성 경험, 멀티스테이지 빌드, 이미지 최적화 경험",
      "warning_sign": "가상머신과 컨테이너의 차이를 설명 못함",
      "sample_questions": [
        "Dockerfile을 직접 작성해보셨나요? 어떻게 구성하셨나요?",
        "Docker를 사용하면서 겪은 어려움이 있었나요?"
      ]
    }
  ]
}
```

---

## 프롬프트 3: JD-지원자 매칭 분석

### AI 프롬프트

```
채용공고 요구사항과 지원자 프로필을 비교 분석해주세요.

## 채용공고 요구사항
### 필수 기술
[JD에서 추출한 required_skills]

### 우대 기술
[JD에서 추출한 preferred_skills]

### 담당 업무
[JD에서 추출한 responsibilities]

## 지원자 프로필
### 보유 기술
[이력서에서 추출한 skills]

### 주요 경험
[이력서에서 추출한 경력/프로젝트 요약]

## 분석 요청
다음 형식으로 매칭 분석을 해주세요:

{
  "skill_match": {
    "required_matched": [
      {"skill": "기술명", "evidence": "지원자의 어떤 경험에서 확인됨"}
    ],
    "required_missing": [
      {"skill": "기술명", "risk_level": "high/medium/low", "mitigation": "대안 또는 확인 방법"}
    ],
    "preferred_matched": [],
    "extra_relevant": [
      {"skill": "기술명", "relevance": "JD와의 관련성"}
    ]
  },

  "experience_match": {
    "relevant_experience": [
      {"responsibility": "JD 업무", "candidate_experience": "지원자 경험", "match_level": "high/medium/low"}
    ],
    "gaps": [
      {"responsibility": "JD 업무", "concern": "우려사항", "question_to_verify": "확인할 질문"}
    ]
  },

  "overall_fit": {
    "score": "1-10",
    "strengths": ["강점 3가지"],
    "concerns": ["우려사항 2가지"],
    "must_verify": ["면접에서 반드시 확인할 것"]
  },

  "interview_focus": [
    "면접에서 집중해야 할 영역과 이유"
  ]
}
```

---

## 결과 정리 템플릿

```markdown
# JD 분석 결과

## 포지션 정보
- 포지션: [포지션명]
- 부서: [부서명]
- 경력 요건: [N년 이상 / 레벨]

## 기술 요구사항

### 필수 기술 (Must Have)
| 기술 | 세부 요건 | 지원자 보유 | 비고 |
|------|-----------|-------------|------|
| Python | 3년 이상 | ✅ 5년 | |
| FastAPI | - | ✅ | |
| PostgreSQL | - | ✅ | |
| Docker | - | ✅ | |

### 우대 기술 (Nice to Have)
| 기술 | 지원자 보유 | 비고 |
|------|-------------|------|
| Kubernetes | ❌ | 확인 필요 |
| Redis | ✅ | |
| 대용량 트래픽 | ⚠️ | 구체적 확인 필요 |

## 담당 업무 매칭
| JD 업무 | 관련 경험 | 매칭도 |
|---------|-----------|--------|
| REST API 설계 | ABC사 결제 API 개발 | 높음 |
| DB 최적화 | 쿼리 튜닝 경험 | 중간 |
| CI/CD 구축 | GitHub Actions 경험 | 높음 |

## 면접 집중 영역
1. **대용량 트래픽 경험 검증** - MAU 100만 주장의 구체적 내용
2. **Kubernetes 역량 확인** - 우대사항이지만 팀에서 사용 중
3. **설계 능력 평가** - 미들 레벨에 맞는 아키텍처 이해도

## 기술 용어집 (면접관용)

### FastAPI
- **쉬운 설명**: Python으로 웹 API를 만드는 현대적인 도구
- **왜 중요**: 우리 팀 주력 기술, 비동기 처리 필수
- **확인 질문**: "FastAPI의 의존성 주입을 어떻게 활용하셨나요?"

### Docker
- **쉬운 설명**: 앱을 어디서든 동일하게 실행하도록 포장하는 기술
- **왜 중요**: 배포 환경 일관성, 우리 인프라 기반
- **확인 질문**: "Dockerfile 작성 시 이미지 크기 최적화는 어떻게 하셨나요?"

[... 기타 용어]
```

---

## 다음 단계

JD 분석이 완료되면 면접 질문 생성으로 진행합니다.

**다음**: [05. 면접 질문 생성](./05-question-generation.md)

---

## 팁

- **JD가 모호한 경우**: AI에게 "일반적인 [포지션] 채용 시 요구되는 기술을 추가로 추천해줘"라고 요청

- **기술 용어집 확장**: 면접관이 비개발자라면, 용어집에 "면접 중 이 단어가 나오면 이렇게 이해하세요" 같은 팁 추가

- **매칭 분석 활용**: 매칭이 낮은 영역은 "왜 이 기술을 선택하지 않았는지" 또는 "어떻게 학습할 계획인지"를 질문
