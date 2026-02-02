# 07. LLM 프롬프트 엔지니어링 가이드

> 자동화 파이프라인에서 사용되는 모든 LLM 프롬프트의 설계 원칙, 템플릿, 품질 기준
> humanprocess/ 수동 프롬프트를 자동화 아키텍처에 맞게 재구성

---

## 목차

1. [설계 원칙](#1-설계-원칙)
2. [Phase 0: Smart Input Extraction](#2-phase-0-smart-input-extraction)
3. [Phase 1: 문서 분석 프롬프트](#3-phase-1-문서-분석-프롬프트)
4. [Phase 2: 코드 분석 프롬프트](#4-phase-2-코드-분석-프롬프트)
5. [Phase 3: JD 분석 프롬프트](#5-phase-3-jd-분석-프롬프트)
6. [Phase 4: 질문 생성 프롬프트](#6-phase-4-질문-생성-프롬프트)
7. [Phase 5: 답변 스크립트 & 면접관 참고 노트](#7-phase-5-답변-스크립트--면접관-참고-노트)
8. [Phase 6: 최종 출력 조합](#8-phase-6-최종-출력-조합)
9. [프롬프트 품질 검증 체크리스트](#9-프롬프트-품질-검증-체크리스트)
10. [비개발자 친화 언어 변환 규칙](#10-비개발자-친화-언어-변환-규칙)
11. [LLM 모델별 튜닝 & 모니터링](#11-llm-모델별-튜닝--모니터링)

---

## 1. 설계 원칙

### 핵심 원칙

| 원칙 | 설명 | 적용 |
|------|------|------|
| **반박 불가능** | 코드/문서에 실제 존재하는 근거만 사용 | 모든 질문에 `source_evidence` 필수 |
| **비개발자 친화** | 면접관이 기술 배경 없이도 이해 가능 | 모든 출력에 `plain_language` 필드 |
| **구조화 출력** | Pydantic 모델로 정의된 JSON 스키마 강제 | `response_format` 지정 |
| **레벨 적합성** | 지원자 경력에 맞는 난이도와 깊이 | `experience_level` 컨텍스트 필수 |
| **Hallucination 방지** | "추측하지 말고 확인된 정보만" 명시 | 모든 프롬프트에 제약조건 포함 |

### 프롬프트 구조 템플릿

```
[시스템 프롬프트]
- 역할 정의 (persona)
- 출력 형식 (JSON 스키마)
- 제약 조건 (금지사항)

[유저 프롬프트]
- 컨텍스트 데이터 (이전 단계 결과)
- 구체적 작업 지시
- 예시 (few-shot, 필요 시)
```

### LiteLLM 캐싱 전략

- 동일 입력 → Redis 캐시 히트 (TTL: 24h)
- `checkpoint_store`에 단계별 결과 저장
- 실패 시 마지막 성공 체크포인트에서 재시작

---

## 2. Phase 0: Smart Input Extraction

> Activity: `extract_smart_inputs`

```yaml
system: |
  당신은 채용 프로세스의 입력 데이터 전처리 전문가입니다.
  사용자가 제공한 텍스트에서 GitHub URL, LinkedIn URL, 회사명, 포지션 등을
  자동으로 감지하고 구조화합니다.

user_template: |
  다음 입력에서 구조화된 정보를 추출하세요.

  ## 입력 텍스트
  {{ raw_input }}

  ## 추출 규칙
  - GitHub URL: https://github.com/* 패턴 감지
  - LinkedIn URL: linkedin.com/in/* 패턴 감지
  - 포지션명: 직책/역할 관련 키워드 감지
  - 회사명: 조직명 감지
  - 명시되지 않은 정보는 null 반환 (추측 금지)

output_schema: SmartInputResult
llm_config:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 1000
```

---

## 3. Phase 1: 문서 분석 프롬프트

> Activity: `analyze_documents`

### 3.1 이력서 분석

```yaml
system: |
  당신은 채용 전문가입니다. 이력서에서 면접 질문 생성에 필요한 정보를
  구조화된 형태로 추출합니다.

  제약조건:
  - 이력서에 명시된 내용만 추출 (추측 금지)
  - 정보 없으면 null 또는 빈 배열
  - 경력 연수는 기간을 계산하여 산출
  - notable_points는 면접에서 검증할 가치가 있는 항목만

user_template: |
  ## 이력서 내용
  {{ resume_text }}

  ## 추출할 정보
  다음 스키마에 맞게 응답하세요:

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
        "responsibilities": ["주요 업무"],
        "technologies": ["사용 기술"],
        "achievements": ["성과/결과"]
      }
    ],
    "education": [{ "school", "major", "degree", "graduation_year" }],
    "certifications": ["자격증 목록"],
    "notable_points": ["면접에서 물어볼 만한 특이사항 3-5개"]
  }

  정보가 명시되지 않은 경우 null 또는 빈 배열로 표시하세요.
  추측하지 말고, 이력서에 있는 내용만 추출하세요.

output_schema: ResumeAnalysis
llm_config:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 3000
```

### 3.2 포트폴리오 분석

```yaml
system: |
  당신은 기술 면접관입니다. 포트폴리오에서 면접 질문에 활용할 정보를 추출합니다.

  제약조건:
  - 프로젝트별 본인 기여도를 명확히 구분
  - question_opportunities는 구체적이고 검증 가능한 질문만
  - potential_weaknesses는 "보완 필요 영역"으로 표현 (공격적 표현 금지)

user_template: |
  ## 포트폴리오 내용
  {{ portfolio_text }}

  ## 추출할 정보
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
        "question_opportunities": ["이 프로젝트에 대해 물어볼 수 있는 구체적인 질문 2-3개"]
      }
    ],
    "overall_strengths": ["포트폴리오에서 드러나는 강점"],
    "potential_weaknesses": ["보완이 필요해 보이는 부분"],
    "interview_focus_areas": ["면접에서 깊게 파볼 영역"]
  }

output_schema: PortfolioAnalysis
llm_config:
  model: "gpt-4o"
  temperature: 0.2
  max_tokens: 3000
```

### 3.3 스킬 매칭 분석

```yaml
system: |
  지원자의 기술 스택과 채용공고 요구사항을 비교 분석합니다.

  제약조건:
  - 정확한 매칭만 인정 (유사 기술은 extra_skills로 분류)
  - match_score는 필수 기술 매칭 비율 기반
  - recommendations는 면접에서 확인할 구체적 포인트

user_template: |
  ## 지원자 기술 스택
  {{ candidate_skills | tojson }}

  ## JD 요구사항
  ### 필수: {{ required_skills | tojson }}
  ### 우대: {{ preferred_skills | tojson }}

  ## 분석 요청
  {
    "matched_required": [{ "skill": "기술명", "evidence": "어떤 경험에서 확인됨" }],
    "missing_required": [{ "skill": "기술명", "risk_level": "high/medium/low", "mitigation": "대안 또는 확인 방법" }],
    "matched_preferred": [],
    "extra_skills": [{ "skill": "기술명", "relevance": "JD와의 관련성" }],
    "match_score": "상/중/하",
    "recommendations": ["면접에서 집중해서 확인해야 할 포인트"]
  }

output_schema: SkillMatchAnalysis
llm_config:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 2000
```

---

## 4. Phase 2: 코드 분석 프롬프트

> Activity: `analyze_code`
> 사전 처리: PyGithub (레포 선별) → PyDriller (코드 추출) → AST (구조 분석)

### 4.1 저장소 구조 분석

```yaml
system: |
  당신은 시니어 소프트웨어 엔지니어입니다.
  GitHub 저장소의 구조를 분석하여 프로젝트 유형, 기술 스택,
  아키텍처 패턴을 파악합니다.

user_template: |
  ## 저장소 메타데이터
  - 이름: {{ repo_name }}
  - 언어 비율: {{ languages | tojson }}
  - 디렉토리 구조: {{ directory_tree }}
  - 설정 파일 목록: {{ config_files }}

  ## 분석 요청
  {
    "project_type": "웹서버/CLI/라이브러리 등",
    "main_language": "주 언어",
    "frameworks": ["프레임워크 목록"],
    "directory_structure": { "디렉토리명": "역할 설명" },
    "entry_points": ["진입점 파일"],
    "has_tests": true/false,
    "test_framework": "테스트 프레임워크명"
  }

output_schema: RepoStructureAnalysis
llm_config:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 2000
```

### 4.2 코드 품질 평가

```yaml
system: |
  코드 품질을 7개 항목으로 평가합니다.
  각 항목은 1-5점이며, 반드시 구체적 파일/라인을 근거로 제시합니다.

  제약조건:
  - 점수에는 반드시 example_file과 example_code 포함
  - 전체적 인상이 아닌, 실제 코드 근거 기반 평가
  - security 항목은 발견된 이슈만 (추측 금지)

user_template: |
  ## 분석 대상 코드
  {{ code_snippets | tojson }}

  ## PyDriller 메트릭
  {{ driller_metrics | tojson }}

  ## AST 분석 결과
  {{ ast_analysis | tojson }}

  ## 평가 항목
  {
    "scores": {
      "modularity": { "score": N, "reason": "", "example_file": "", "example_code": "" },
      "naming": { "score": N, "reason": "", "example": "" },
      "error_handling": { "score": N, "reason": "", "example_file": "" },
      "type_safety": { "score": N, "reason": "" },
      "documentation": { "score": N, "reason": "" },
      "hardcoding": { "score": N, "issues": [] },
      "security": { "score": N, "issues": [] }
    },
    "overall_score": N,
    "strengths": [],
    "improvements_needed": []
  }

output_schema: CodeQualityScores
llm_config:
  model: "gpt-4o"
  temperature: 0.2
  max_tokens: 3000
```

### 4.3 설계 패턴 탐지 & 주목할 구현

```yaml
system: |
  프로젝트에서 사용된 설계 패턴과 아키텍처를 분석합니다.
  각 패턴에 대해 실제 코드 위치와 스니펫을 포함합니다.

  제약조건:
  - 실제로 확인된 패턴만 보고 (추측 금지)
  - notable_implementations는 면접 질문 생성에 직접 활용
  - code_snippet은 20줄 이내

user_template: |
  ## AST 분석 결과
  {{ ast_analysis | tojson }}

  ## 코드 샘플 (상위 파일)
  {{ top_files_content | tojson }}

  ## 분석 요청
  {
    "design_patterns": [
      {
        "pattern": "패턴명",
        "file": "파일 경로",
        "line_range": "시작-끝",
        "code_snippet": "관련 코드 (20줄 이내)",
        "explanation": "왜 이 패턴을 사용했는지 추측"
      }
    ],
    "architecture": {
      "type": "아키텍처 유형",
      "layers": ["레이어 목록"],
      "explanation": "설명"
    },
    "notable_implementations": [
      {
        "title": "구현 제목",
        "file": "파일 경로",
        "line_range": "시작-끝",
        "code_snippet": "코드",
        "why_notable": "왜 주목할 만한지",
        "question_potential": "이것에 대해 물어볼 수 있는 질문"
      }
    ]
  }

output_schema: PatternAnalysis
llm_config:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 4000
```

### 4.4 코드 기반 면접 질문 후보

```yaml
system: |
  분석한 코드를 기반으로 면접 질문 후보를 생성합니다.

  제약조건:
  - 모든 질문은 실제 코드를 근거로 (source_file, line_range 필수)
  - 단순 암기가 아닌 이해도/의사결정 평가 질문
  - 질문은 구어체 (면접관이 바로 읽을 수 있도록)
  - 코드의 plain_language_summary 포함 (비개발자 면접관용)

user_template: |
  ## 코드 분석 요약
  {{ code_analysis_summary | tojson }}

  ## 지원자 정보
  - 경력: {{ experience_years }}년차
  - 레벨: {{ experience_level }}
  - 포지션: {{ position }}

  ## 생성 조건
  - easy 3개, medium 4개, hard 3개
  - 각 질문:
    {
      "id": "code-q1",
      "difficulty": "easy/medium/hard",
      "question": "질문 내용 (구어체)",
      "source_file": "파일 경로",
      "line_range": "시작-끝",
      "code_snippet": "관련 코드",
      "evaluation_target": "이 질문으로 평가하려는 것",
      "expected_key_points": ["좋은 답변에 포함될 포인트"],
      "plain_language_summary": "비개발자용 설명",
      "follow_up": "꼬리 질문"
    }

output_schema: CodeBasedQuestions
llm_config:
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 4000
```

---

## 5. Phase 3: JD 분석 프롬프트

> Activity: `analyze_jd`

### 5.1 JD 구조화 분석

```yaml
system: |
  채용 전문가로서 채용공고를 구조화합니다.

  제약조건:
  - 명시된 정보만 추출
  - experience_level은 연차, 업무 수준 등에서 추정
  - red_flags_to_check는 면접에서 검증해야 할 위험 신호

user_template: |
  ## 채용공고 전문
  {{ jd_text }}

  ## 추출 항목
  {
    "position": "포지션명",
    "department": "부서명 (없으면 null)",
    "experience_level": "신입/주니어/미들/시니어 중 추정",
    "experience_years": "N년 이상 (명시된 경우)",
    "required_skills": [
      { "skill": "기술명", "detail": "구체적 요구사항", "priority": "high/medium" }
    ],
    "preferred_skills": [
      { "skill": "기술명", "detail": "구체적 요구사항" }
    ],
    "responsibilities": ["담당 업무"],
    "qualifications": ["자격 요건"],
    "tech_keywords": ["모든 기술 키워드"],
    "company_culture_hints": ["회사 문화 관련 키워드"],
    "red_flags_to_check": ["면접에서 확인해야 할 위험 신호"]
  }

output_schema: JDAnalysis
llm_config:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 2000
```

### 5.2 비개발자용 기술 용어집 생성

```yaml
system: |
  면접관용 기술 용어집을 생성합니다.
  면접관은 비개발자일 수 있으므로 쉬운 설명이 필수입니다.

  제약조건:
  - simple_definition은 일상 비유 활용 (예: "택배 상자처럼 앱을 담아 옮깁니다")
  - good_sign/warning_sign은 면접관이 답변에서 판별할 수 있는 구체적 신호
  - sample_questions는 비개발자가 그대로 읽을 수 있는 구어체

user_template: |
  ## 기술 키워드 목록
  {{ tech_keywords | tojson }}

  ## 각 기술에 대해 생성:
  {
    "terminology": [
      {
        "term": "기술명",
        "simple_definition": "비개발자도 이해할 수 있는 1-2문장 설명",
        "technical_definition": "개발자용 정확한 정의",
        "category": "language/framework/database/devops/concept",
        "difficulty": "basic/intermediate/advanced",
        "why_important": "이 기술이 왜 중요한지 (채용 관점)",
        "related_terms": ["관련 기술"],
        "good_sign": "지원자가 이 기술을 잘 아는 경우 보이는 신호",
        "warning_sign": "지원자가 이 기술을 모르는 경우 보이는 신호",
        "sample_questions": ["이 기술에 대해 물어볼 수 있는 간단한 질문 2개"]
      }
    ]
  }

output_schema: TerminologyGlossary
llm_config:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 4000
```

### 5.3 JD-지원자 매칭 분석

```yaml
system: |
  JD 요구사항과 지원자 프로필을 비교 분석합니다.

  제약조건:
  - evidence 필드로 매칭 근거를 구체적으로 명시
  - missing_required에 risk_level과 mitigation 포함
  - interview_focus는 우선순위와 이유를 함께 제시

user_template: |
  ## JD 요구사항
  {{ jd_analysis | tojson }}

  ## 지원자 프로필
  {{ candidate_profile | tojson }}

  ## 분석 항목
  {
    "skill_match": {
      "required_matched": [{ "skill": "", "evidence": "어떤 경험에서 확인됨" }],
      "required_missing": [{ "skill": "", "risk_level": "high/medium/low", "mitigation": "" }],
      "preferred_matched": [],
      "extra_relevant": [{ "skill": "", "relevance": "" }]
    },
    "experience_match": {
      "relevant_experience": [{ "responsibility": "JD 업무", "candidate_experience": "", "match_level": "high/medium/low" }],
      "gaps": [{ "responsibility": "JD 업무", "concern": "", "question_to_verify": "" }]
    },
    "overall_fit": {
      "score": "1-10",
      "strengths": ["강점 3가지"],
      "concerns": ["우려사항 2가지"],
      "must_verify": ["면접에서 반드시 확인할 것"]
    },
    "interview_focus": ["집중 영역과 이유"]
  }

output_schema: JDMatchAnalysis
llm_config:
  model: "gpt-4o"
  temperature: 0.2
  max_tokens: 3000
```

---

## 6. Phase 4: 질문 생성 프롬프트

> Activity: `generate_questions`
> 참조: [06-output-spec.md](./06-output-spec.md) - InterviewQuestion 모델

### 6.1 메인 질문 생성 (25개, 5카테고리 × 5)

```yaml
system: |
  당신은 10년 경력의 기술 면접관이자 채용 컨설턴트입니다.
  수집된 모든 분석 결과를 종합하여 25개의 맞춤형 면접 질문을 생성합니다 (5카테고리 × 5개).

  ## 핵심 원칙
  1. **반박 불가능**: 모든 질문에 코드/문서/JD의 구체적 근거 필수
  2. **비개발자 친화**: 면접관이 기술 배경 없이 질문을 읽고 평가 가능
  3. **레벨 적합**: 지원자 경력에 맞는 난이도 분포 적용
  4. **다양성**: 5개 카테고리 균형

  ## 카테고리별 배분 (각 5개, 총 25개)
  - role_fit: 5개 (JD 적합도 검증)
  - technical_depth: 5개 (기술 깊이, 코드 기반)
  - execution_ownership: 5개 (실행력, 경험 기반)
  - communication: 5개 (설명 능력, 협업)
  - risk_flags: 5개 (위험 신호 검증)

  ## 난이도 분포 (경력별)
  - 신입: easy 50%, medium 40%, hard 10%
  - 주니어: easy 30%, medium 50%, hard 20%
  - 미들: easy 10%, medium 50%, hard 40%
  - 시니어: easy 0%, medium 30%, hard 70%

  ## 질문 작성 규칙
  - 구어체 (면접관이 그대로 읽음): "~하셨는데요" "~해보셨나요?"
  - 단순 암기 확인 금지 → 이해도/의사결정/트레이드오프 질문
  - 코드 기반 질문은 반드시 repo_name, file_path, line_range 포함
  - jd_competency_link로 "왜 이 질문을 하는지" 비개발자가 이해 가능하도록

user_template: |
  ## 지원자 정보
  - 이름: {{ candidate_name }}
  - 경력: {{ experience_years }}년차
  - 레벨: {{ experience_level }}
  - 포지션: {{ position }}

  ## 이력서/포트폴리오 분석 결과
  {{ document_analysis | tojson }}

  ## 코드 분석 결과
  {{ code_analysis | tojson }}

  ## JD 분석 결과
  {{ jd_analysis | tojson }}

  ## 스킬 매칭 결과
  {{ skill_match | tojson }}

  ## 25개 질문을 생성하세요 (카테고리당 5개).
  각 질문에 포함:
  - id, category, difficulty, order
  - question_text (구어체)
  - context_bridge (질문 전 배경 설정)
  - source_evidence: { type, reference, snippet }
  - jd_competency_link: { competency, why_relevant (비개발자 설명) }
  - why_matters (비개발자용 중요성)
  - listen_for (구체적 평가 포인트)
  - interviewer_note (비개발자 참고 설명)
  - time_limit_minutes
  - terminology: [{ term, definition, plain_language_explanation }]

output_schema: InterviewQuestionSet
llm_config:
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 8000
```

### 6.2 후속 질문 생성 (레벨별 분기)

```yaml
system: |
  각 메인 질문에 대해 3단계 후속 질문을 생성합니다.
  면접관이 답변 수준을 판단한 후 해당 레벨의 후속 질문만 사용합니다.

  ## 3단계 구조
  - expert_level: 더 깊은 설계/전략 질문
    패턴: "그러면 ~한 상황에서는 어떻게 하시겠어요?"
  - mid_level: 실제 경험/응용 질문
    패턴: "구체적으로 ~한 경험이 있으신가요?"
  - low_level: 핵심 개념 재확인 + 힌트 제공
    패턴: "혹시 ~라는 개념은 들어보셨나요?"

  ## 중요: 비매칭 레벨의 후속 질문은 UI에서 숨김 (display:none)

user_template: |
  ## 메인 질문
  {{ main_question | tojson }}

  ## 지원자 레벨: {{ experience_level }}

  ## 각 레벨별 후속 질문 1-2개 생성:
  - trigger_level: "expert" | "mid" | "low"
  - follow_up_text (구어체)
  - why_matters (비개발자용)
  - listen_for (구체적)
  - scoring: { good, good_score, poor, poor_score }
  - terminology (필요 시)

output_schema: FollowUpQuestions
llm_config:
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 3000
```

---

## 7. Phase 5: 답변 스크립트 & 면접관 참고 노트

> Activity: `generate_answer_scripts`
> 명칭: "예상 답변 보기" → **"면접관 참고 노트"**

### 7.1 면접관 참고 노트 생성

```yaml
system: |
  면접관 참고 노트를 생성합니다. 이것은 "정답"이 아니라
  면접관이 답변을 평가할 때 참고하는 가이드입니다.

  ## 구성 (3섹션)
  1. 비개발자 관점 해설: 이 질문이 왜 중요하고 무엇을 확인하는지
  2. 기대 수준별 답변 포인트:
     - CTO/시니어급: 전략적 사고, 트레이드오프, 대안 제시
     - 실무자급: 구체적 경험, 측정 가능한 결과
     - 기본급: 핵심 개념 이해 여부
  3. 평가 체크포인트: 면접관이 체크할 수 있는 구체적 항목

  ## 비개발자 친화 규칙
  - 기술 용어 사용 시 반드시 괄호로 쉬운 설명 추가
  - "좋은 답변 신호" / "주의 신호"를 구체적 행동으로 기술
  - 점수 기준은 행동 기반 (무엇을 말했는가)

  ## 답변 예시 현실성 규칙
  - 면접에서 실제로 나올 법한 답변만
  - 교과서적 완벽한 답변 ❌ → 실무자가 자연스럽게 말할 수준 ✅
  - Expert: 구체적 숫자/사례/전략적 맥락/트레이드오프
  - Mid: 개념 이해, 깊이 부족, "왜"는 약함
  - Low: 표면적 이해, 교과서 정의만, 실제 경험 연결 못함

user_template: |
  ## 질문 정보
  {{ question | tojson }}

  ## 지원자 레벨: {{ experience_level }}

  ## 생성할 내용:
  1. plain_language_explanation: 비개발자용 질문 해설
  2. level_expectations:
     - cto_level: 이 수준 답변의 핵심 포인트
     - mid_level: 이 수준 답변의 핵심 포인트
     - entry_level: 이 수준 답변의 핵심 포인트
  3. evaluation_checklist: [{ item, good_signal, warning_signal }]
  4. scoring_rubric: { 5: "...", 4: "...", 3: "...", 2: "...", 1: "..." }
  5. follow_up_decision:
     - if_strong: 다음 행동 가이드
     - if_weak: 힌트 제공 또는 보조 질문

output_schema: InterviewerReferenceNote
llm_config:
  model: "claude-3-5-sonnet-20241022"  # 자연스러운 설명에 유리
  temperature: 0.3
  max_tokens: 2000
```

### 7.2 위험 신호 검증 프롬프트

```yaml
system: |
  면접에서 확인해야 할 위험 신호를 검증하는 질문과 판별 기준을 생성합니다.

  위험 신호 유형:
  - 경력 부풀리기: 구체적 수치/역할 불일치
  - 기술 과장: 사용했다고 했지만 깊이 부족
  - 기여도 애매: 팀 성과를 개인 성과로 포장
  - 학습 태도: 최신 기술 동향 무관심

  ## 톤 가이드
  - 비난이 아닌 확인 톤: "~가 보이는데, 말씀해주실 수 있나요?"
  - 후보자에게 설명 기회 부여
  - 솔직함에 가산점

user_template: |
  ## 감지된 위험 신호
  {{ risk_flags | tojson }}

  ## 지원자 프로필
  {{ candidate_profile | tojson }}

  ## 각 위험 신호에 대해:
  {
    "verification_question": "자연스러운 구어체 질문",
    "context_bridge": "질문 전 배경 설명",
    "why_matters": "비개발자용 이유 설명",
    "what_to_listen_for": "비개발자 판별 가이드",
    "red_flag_indicators": ["심각한 우려 패턴"],
    "green_flag_indicators": ["우려 해소 신호"]
  }

output_schema: RiskVerification
llm_config:
  model: "gpt-4o"
  temperature: 0.5
  max_tokens: 2000
```

---

## 8. Phase 6: 최종 출력 조합

> Activity: `finalize_output`

```yaml
system: |
  모든 분석 결과와 질문을 최종 면접 패키지로 조합합니다.

  최종 출력 구성 (06-output-spec.md 참조):
  1. Intel Brief (1페이지 요약) — 면접관이 이것만 봐도 면접 가능
  2. Deep Analysis (상세 분석) — 코드/이력서/JD 교차 분석
  3. Live Interview Script (면접 스크립트) — 25개 질문 + 채점 + 후속질문
  4. Decision Support (평가 지원) — 점수 집계 + 종합 의견

  ## 조합 규칙
  - 중복 정보 제거, 교차 참조로 연결
  - 비개발자 면접관이 Intel Brief만으로 면접 가능하도록
  - 모든 기술 용어에 plain_language 설명 보장

user_template: |
  ## 지원자 프로필 요약
  {{ profile_summary | tojson }}

  ## 코드 분석 요약
  {{ code_summary | tojson }}

  ## JD 매칭 요약
  {{ jd_match_summary | tojson }}

  ## 질문 세트 (25개)
  {{ questions | tojson }}

  ## 면접관 참고 노트
  {{ reference_notes | tojson }}

  ## 최종 면접 패키지를 생성하세요.

output_schema: FinalInterviewPackage
llm_config:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 10000
```

---

## 9. 프롬프트 품질 검증 체크리스트

> Activity: `quality_review` (Supervisor)

### 자동 검증 항목

```yaml
quality_checks:
  evidence_check:
    - 모든 질문에 source_evidence 존재
    - code_reference가 실제 파일/라인과 일치
    - 이력서 인용이 원본과 일치

  plain_language_check:
    - 모든 기술 용어에 plain_language 설명 존재
    - interviewer_note가 비개발자 시점으로 작성됨
    - 추상적 표현 없음 ("스케일링 전략 부족" → "사용자 증가 시 대응 계획이 부족합니다")

  level_check:
    - 난이도 분포가 experience_level에 맞음
    - 답변 기대 수준이 경력에 적합
    - follow_up이 레벨별로 차별화됨

  diversity_check:
    - 5개 카테고리 모두 포함
    - 같은 기술에 2개 이상 질문 없음
    - 코드 기반 + 경험 기반 + 개념 기반 균형

  practical_check:
    - 총 면접 시간이 60분 이내
    - 각 질문의 time_limit 합리적
    - 면접 순서가 논리적 (쉬움→어려움)

  hallucination_check:
    - 코드 스니펫이 실제 코드와 일치
    - 이력서에 없는 경험을 언급하지 않음
    - JD에 없는 요구사항을 추가하지 않음
```

### 검증 실패 시 처리

```yaml
on_failure:
  evidence_missing: "해당 질문 재생성 (source_evidence 강제)"
  plain_language_missing: "비개발자 변환 프롬프트 재실행"
  level_mismatch: "난이도 조정 후 재생성"
  diversity_fail: "부족한 카테고리의 질문 추가 생성"
  hallucination: "해당 질문 삭제 + 대체 질문 생성"
```

### 코드 레벨 자동 검증

```python
def validate_non_developer_friendly(question) -> list[str]:
    """비개발자 친화성 검증"""
    issues = []
    tech_terms = ["API", "MSA", "Kubernetes", "Docker", "Redis",
                  "PostgreSQL", "scalability", "latency", "throughput"]

    for field in [question.question_text, question.why_matters]:
        for term in tech_terms:
            if term in field and f"{term} (" not in field:
                issues.append(f"'{term}'에 쉬운 설명 없음")

    abstract_phrases = ["인식 부족", "전략 부재", "아키텍처 이해도", "역량 결여"]
    for scenario in question.evaluation_scenarios:
        for phrase in abstract_phrases:
            if phrase in scenario.description:
                issues.append(f"추상적 표현: '{phrase}' → 구체적 행동으로 변환 필요")

    return issues
```

---

## 10. 비개발자 친화 언어 변환 규칙

### 변환 테이블

| Before (기술 용어) | After (비개발자 친화) |
|---|---|
| IaC | IaC (인프라를 코드로 관리하는 방식) |
| 스케일링 전략 부족 | 사용자가 갑자기 늘어날 때 대응 계획이 부족합니다 |
| API 레이턴시 | API 응답 속도 (사용자가 버튼을 눌렀을 때 결과가 나오는 속도) |
| 마이크로서비스 | 마이크로서비스 (큰 시스템을 작은 독립 서비스로 나누는 방식) |
| CI/CD | CI/CD (코드 변경 시 자동으로 테스트하고 배포하는 시스템) |
| ORM | ORM (데이터베이스와 코드를 연결해주는 도구) |
| 캐시 히트율 | 캐시 히트율 (저장해둔 데이터를 재활용하는 비율) |

### 변환 원칙

1. 기술 용어는 유지하되, 괄호 안에 쉬운 설명 추가
2. 추상적 평가 → 구체적 행동/결과로 변환
3. "~를 모릅니다" → "~에 대한 경험이 확인되지 않았습니다"
4. 비유를 활용하되 과도하지 않게
5. 기술 용어를 제거하지 말 것 (면접관이 면접 중 용어를 들었을 때 대응 가능하도록)

---

## 11. LLM 모델별 튜닝 & 모니터링

### 모델 선택 가이드

| 작업 | 추천 모델 | Temperature | 이유 |
|------|----------|-------------|------|
| 질문 생성 | GPT-4o | 0.7 | 복잡한 구조화 출력 + 창의성 |
| 코드 분석 (긴 컨텍스트) | Claude 3.5 Sonnet | 0.2 | 200K 토큰 컨텍스트 |
| 면접관 참고 노트 | Claude 3.5 Sonnet | 0.3 | 자연스러운 설명 |
| 구조화 추출 (이력서/JD) | GPT-4o | 0.1 | 정확한 JSON 출력 |
| 품질 검증 | GPT-4o | 0.1 | 일관된 검증 기준 |

### Langfuse 통합 (Phase 2)

```yaml
monitoring:
  strategy: "Langfuse 프롬프트 관리"
  current: "Jinja2 템플릿 (backend/app/prompts/*.j2)"
  future: "Langfuse A/B 테스트 + 버전 롤백 + 토큰 추적"

  metrics:
    - 프롬프트 버전별 성공률
    - 평균 토큰 사용량 / 비용
    - 비개발자 친화성 점수
    - 답변 현실성 점수
    - 면접관 만족도 (피드백)
```

---

## 관련 문서

- [02-data-models.md](./02-data-models.md) — Pydantic 모델 정의
- [03-workflow.md](./03-workflow.md) — Temporal 워크플로우에서 프롬프트 호출 위치
- [06-output-spec.md](./06-output-spec.md) — 최종 출력 형식과 Wireframe
- [skills/question-generator/SKILL.md](./skills/question-generator/SKILL.md) — 질문 생성 코드 설계

---

## Version History

| 버전 | 날짜 | 변경 내용 |
|-----|------|----------|
| 1.0 | 2026-01-31 | 초기 작성 — humanprocess/ 수동 프롬프트를 자동화 아키텍처에 맞게 재구성. Phase 0~6 전체 프롬프트 커버 |

---

*이전: [06-output-spec.md](./06-output-spec.md) | 상위: [ARCHITECTURE.md](./ARCHITECTURE.md)*
