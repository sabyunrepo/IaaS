# 02. 문서 분석 (이력서/포트폴리오)

> AI를 활용하여 이력서와 포트폴리오에서 핵심 정보 추출

---

## 목표

이력서와 포트폴리오에서 면접 질문 생성에 필요한 정보를 구조화된 형태로 추출합니다.

---

## 프롬프트 1: 이력서 분석

### 사용 시점
이력서(PDF/텍스트)가 준비되었을 때

### AI 프롬프트

```
당신은 채용 전문가입니다. 다음 이력서를 분석하여 구조화된 정보를 추출해주세요.

## 이력서 내용
[여기에 이력서 내용을 붙여넣기]

## 추출할 정보
다음 JSON 형식으로 응답해주세요:

{
  "name": "이름",
  "total_experience_years": 숫자,
  "experience_level": "신입/주니어/미들/시니어 중 하나",
  "summary": "지원자를 2-3문장으로 요약",
  "skills": {
    "languages": ["프로그래밍 언어 목록"],
    "frameworks": ["프레임워크 목록"],
    "databases": ["데이터베이스 목록"],
    "tools": ["도구/플랫폼 목록"]
  },
  "work_experience": [
    {
      "company": "회사명",
      "position": "직책",
      "period": "YYYY.MM - YYYY.MM",
      "duration_months": 숫자,
      "responsibilities": ["주요 업무 1", "주요 업무 2"],
      "technologies": ["사용 기술"],
      "achievements": ["성과/결과"]
    }
  ],
  "education": [
    {
      "school": "학교명",
      "major": "전공",
      "degree": "학위",
      "graduation_year": "YYYY"
    }
  ],
  "certifications": ["자격증 목록"],
  "notable_points": ["면접에서 물어볼 만한 특이사항 3-5개"]
}

정보가 명시되지 않은 경우 null 또는 빈 배열로 표시하세요.
추측하지 말고, 이력서에 있는 내용만 추출하세요.
```

### 예상 출력 예시

```json
{
  "name": "김개발",
  "total_experience_years": 5,
  "experience_level": "미들",
  "summary": "5년차 백엔드 개발자로, Python/FastAPI 기반 API 개발과 AWS 인프라 운영 경험이 풍부합니다. 스타트업에서 MAU 100만 서비스의 백엔드를 담당했습니다.",
  "skills": {
    "languages": ["Python", "JavaScript", "Go"],
    "frameworks": ["FastAPI", "Django", "React"],
    "databases": ["PostgreSQL", "Redis", "MongoDB"],
    "tools": ["Docker", "Kubernetes", "AWS", "GitHub Actions"]
  },
  "work_experience": [
    {
      "company": "ABC 테크",
      "position": "백엔드 개발자",
      "period": "2021.03 - 현재",
      "duration_months": 34,
      "responsibilities": [
        "결제 시스템 API 설계 및 개발",
        "레거시 시스템 마이크로서비스 전환"
      ],
      "technologies": ["Python", "FastAPI", "PostgreSQL", "Redis"],
      "achievements": [
        "결제 처리 속도 40% 개선",
        "서버 비용 30% 절감"
      ]
    }
  ],
  "notable_points": [
    "레거시 시스템을 마이크로서비스로 전환한 경험",
    "결제 시스템 개발 경험 (금융 도메인)",
    "대용량 트래픽 처리 경험 (MAU 100만)",
    "인프라 비용 최적화 경험"
  ]
}
```

---

## 프롬프트 2: 포트폴리오 분석

### 사용 시점
포트폴리오 문서가 있을 때 (없으면 건너뛰기)

### AI 프롬프트

```
당신은 기술 면접관입니다. 다음 포트폴리오를 분석하여 면접 질문에 활용할 정보를 추출해주세요.

## 포트폴리오 내용
[여기에 포트폴리오 내용을 붙여넣기]

## 추출할 정보
다음 JSON 형식으로 응답해주세요:

{
  "projects": [
    {
      "name": "프로젝트명",
      "period": "기간",
      "role": "역할 (개인/팀 리더/팀원)",
      "team_size": 숫자 또는 null,
      "description": "프로젝트 설명 (2-3문장)",
      "technologies": ["사용 기술"],
      "my_contributions": ["본인이 담당한 구체적인 작업"],
      "challenges": ["해결한 기술적 도전"],
      "results": ["성과/결과"],
      "question_opportunities": [
        "이 프로젝트에 대해 물어볼 수 있는 구체적인 질문 2-3개"
      ]
    }
  ],
  "overall_strengths": ["포트폴리오에서 드러나는 강점"],
  "potential_weaknesses": ["보완이 필요해 보이는 부분"],
  "interview_focus_areas": ["면접에서 깊게 파볼 영역"]
}
```

### 예상 출력 예시

```json
{
  "projects": [
    {
      "name": "실시간 주문 처리 시스템",
      "period": "2023.01 - 2023.06",
      "role": "팀 리더",
      "team_size": 4,
      "description": "초당 1000건 이상의 주문을 처리하는 실시간 시스템. Kafka를 활용한 이벤트 기반 아키텍처로 구현.",
      "technologies": ["Python", "FastAPI", "Kafka", "Redis", "PostgreSQL"],
      "my_contributions": [
        "전체 아키텍처 설계",
        "Kafka Consumer 구현",
        "Redis 캐싱 전략 설계"
      ],
      "challenges": [
        "대용량 트래픽에서 데이터 정합성 보장",
        "Kafka Consumer 장애 복구 전략"
      ],
      "results": [
        "주문 처리 지연시간 500ms → 50ms",
        "시스템 가용성 99.9% 달성"
      ],
      "question_opportunities": [
        "Kafka Consumer 장애 시 메시지 유실을 어떻게 방지했나요?",
        "Redis 캐시 일관성은 어떻게 유지했나요?",
        "초당 1000건 처리를 위해 어떤 최적화를 했나요?"
      ]
    }
  ],
  "overall_strengths": [
    "대용량 트래픽 처리 경험",
    "이벤트 기반 아키텍처 설계 능력",
    "성능 최적화 경험"
  ],
  "potential_weaknesses": [
    "프론트엔드 경험이 상대적으로 적음",
    "테스트 관련 언급이 적음"
  ],
  "interview_focus_areas": [
    "분산 시스템 설계 능력",
    "장애 대응 및 복구 전략",
    "성능 측정 및 최적화 방법론"
  ]
}
```

---

## 프롬프트 3: 스킬 매칭 분석

### 사용 시점
이력서 분석과 JD가 모두 준비되었을 때

### AI 프롬프트

```
다음 지원자의 기술 스택과 채용공고의 요구사항을 비교 분석해주세요.

## 지원자 기술 스택
[이전 단계에서 추출한 skills 정보 붙여넣기]

## 채용공고 요구사항
### 필수
[JD의 필수 기술 목록]

### 우대
[JD의 우대 기술 목록]

## 분석 요청
다음 형식으로 응답해주세요:

{
  "matched_required": ["JD 필수 기술 중 지원자가 보유한 것"],
  "missing_required": ["JD 필수 기술 중 지원자에게 없는 것"],
  "matched_preferred": ["JD 우대 기술 중 지원자가 보유한 것"],
  "extra_skills": ["JD에 없지만 지원자가 가진 관련 기술"],
  "match_score": "상/중/하",
  "recommendations": [
    "면접에서 집중해서 확인해야 할 포인트"
  ]
}
```

---

## 결과 정리

모든 프롬프트 실행 후, 결과를 다음 형식으로 정리합니다:

```markdown
# 문서 분석 결과

## 지원자 프로필 요약
- 이름: [이름]
- 경력: [N년차 / 레벨]
- 핵심 역량: [2-3가지]
- 요약: [2-3문장 요약]

## 기술 스택
### 보유 기술
- 언어: [목록]
- 프레임워크: [목록]
- 데이터베이스: [목록]
- 기타: [목록]

### JD 매칭 분석
- 필수 기술 매칭: [N/M개]
- 우대 기술 매칭: [N/M개]
- 누락 기술: [목록]

## 주요 경력/프로젝트
### [프로젝트/경력 1]
- 역할: [역할]
- 기술: [기술]
- 성과: [성과]
- 질문 후보: [질문]

### [프로젝트/경력 2]
...

## 면접 질문 후보 (문서 기반)
1. [질문1]
2. [질문2]
3. [질문3]
```

---

## 다음 단계

문서 분석이 완료되면 GitHub 코드 분석으로 진행합니다.

**다음**: [03. 코드 분석](./03-code-analysis.md)

---

## 팁

- **이력서가 영문인 경우**: 프롬프트에 "한국어로 응답해주세요"를 추가합니다.

- **포트폴리오가 없는 경우**: 이력서의 프로젝트 설명을 포트폴리오 대신 활용합니다.

- **정보가 부족한 경우**: AI에게 "추측하지 말고, 확인된 정보만 추출하세요"라고 강조합니다.
