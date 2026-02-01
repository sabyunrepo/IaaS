# JD Manager Skill

> 채용공고 분석 에이전트

---

## 역할

채용공고(JD)를 분석하여 필수 기술, 우대 사항, 역할 요구사항을 추출합니다.

## 책임

1. **JD 텍스트 파싱**: 채용공고 구조 분석
2. **요구사항 분류**: 필수/우대 기술 분류
3. **기술 용어 추출**: 면접 질문에 활용할 키워드 추출
4. **동적 용어집 생성**: 정의되지 않은 기술 용어 LLM으로 설명 생성
5. **벡터 저장**: 분석 결과를 벡터 스토어에 저장

---

## Activity 정의

### analyze_jd

```python
@activity.defn
async def analyze_jd(job_id: str, jd_text: str, language: str) -> dict:
    """
    채용공고 분석

    Input:
        job_id: 작업 ID
        jd_text: 채용공고 텍스트
        language: 출력 언어 (ko, en, ja, zh, etc.)

    Output:
        JDAnalysis: {
            position: str,
            department: str | None,
            experience_level: str,
            required_skills: list[str],
            preferred_skills: list[str],
            responsibilities: list[str],
            qualifications: list[str],
            tech_keywords: list[str],
            terminology: list[TerminologyEntry],
            summary: str,
        }
    """
```

---

## JD 파싱 전략

### 구조 감지

```python
import re
from dataclasses import dataclass

@dataclass
class JDSection:
    """채용공고 섹션"""
    title: str
    content: str
    section_type: str  # required, preferred, responsibility, qualification, etc.

# 섹션 패턴 (다국어 지원)
SECTION_PATTERNS = {
    "required": [
        r"필수\s*(요건|조건|자격|사항)",
        r"자격\s*요건",
        r"Required\s*(Qualifications|Skills|Requirements)",
        r"Must\s*Have",
        r"必須(条件|スキル)",
        r"必备(条件|技能)",
    ],
    "preferred": [
        r"우대\s*(요건|조건|사항)",
        r"Preferred\s*(Qualifications|Skills)",
        r"Nice\s*to\s*Have",
        r"歓迎(条件|スキル)",
        r"优先(条件|技能)",
    ],
    "responsibility": [
        r"담당\s*업무",
        r"주요\s*업무",
        r"Responsibilities",
        r"What\s*You.*Do",
        r"業務内容",
        r"工作职责",
    ],
    "qualification": [
        r"지원\s*자격",
        r"Qualifications",
        r"応募資格",
        r"任职资格",
    ],
    "tech_stack": [
        r"기술\s*스택",
        r"사용\s*기술",
        r"Tech\s*Stack",
        r"Technologies",
        r"技術スタック",
        r"技术栈",
    ],
}


def detect_sections(jd_text: str) -> list[JDSection]:
    """
    채용공고에서 섹션 감지

    전략:
    1. 정규식 패턴으로 섹션 헤더 찾기
    2. 연속된 불릿 포인트 그룹핑
    3. 빈 줄 기준 분리
    """
    sections = []
    lines = jd_text.split("\n")

    current_section = None
    current_content = []

    for line in lines:
        # 섹션 헤더 감지
        section_type = detect_section_type(line)
        if section_type:
            if current_section:
                sections.append(JDSection(
                    title=current_section,
                    content="\n".join(current_content),
                    section_type=current_type,
                ))
            current_section = line.strip()
            current_type = section_type
            current_content = []
        else:
            current_content.append(line)

    # 마지막 섹션 추가
    if current_section:
        sections.append(JDSection(
            title=current_section,
            content="\n".join(current_content),
            section_type=current_type,
        ))

    return sections
```

---

## LLM 기반 분석

### 프롬프트 템플릿

```yaml
# prompts/jd_analysis/extract_requirements.yaml
metadata:
  id: jd_requirements_extraction
  version: "1.0"

system_prompt: |
  당신은 채용공고를 분석하는 전문가입니다.

  다음 채용공고에서 정보를 추출하세요.
  정보가 명시되지 않은 경우 null로 표시하세요.
  추측하지 말고, 공고에 있는 내용만 추출하세요.

  응답 언어: {language}

user_prompt_template: |
  ## 채용공고
  {jd_text}

  ## 추출할 정보
  다음 JSON 형식으로 응답하세요:

  ```json
  {
    "position": "포지션명",
    "department": "부서명 또는 null",
    "experience_level": "신입/주니어/미들/시니어",
    "required_skills": ["필수 기술1", "필수 기술2", ...],
    "preferred_skills": ["우대 기술1", "우대 기술2", ...],
    "responsibilities": ["담당 업무1", "담당 업무2", ...],
    "qualifications": ["자격 요건1", "자격 요건2", ...],
    "tech_keywords": ["기술 키워드1", "기술 키워드2", ...]
  }
  ```

output_schema:
  type: object
  required: [position, experience_level, required_skills]
```

---

## 동적 용어집 생성

```python
from dataclasses import dataclass

@dataclass
class TerminologyEntry:
    """용어집 항목"""
    term: str
    definition: str
    category: str  # framework, database, concept, pattern, etc.
    difficulty: str  # basic, intermediate, advanced
    related_terms: list[str]

# 사전 정의된 용어집 (기본)
PREDEFINED_TERMINOLOGY = {
    "FastAPI": {
        "definition": "Python 기반 고성능 비동기 웹 프레임워크",
        "category": "framework",
        "difficulty": "intermediate",
    },
    "Docker": {
        "definition": "컨테이너 기반 애플리케이션 패키징 및 배포 플랫폼",
        "category": "devops",
        "difficulty": "basic",
    },
    # ... 기타 용어
}


async def generate_terminology(
    tech_keywords: list[str],
    llm_client,
    language: str,
) -> list[TerminologyEntry]:
    """
    기술 키워드에 대한 용어집 생성

    전략:
    1. 사전 정의된 용어가 있으면 사용
    2. 없으면 LLM으로 동적 생성
    3. 면접관이 이해할 수 있는 수준으로 설명
    """
    terminology = []
    unknown_terms = []

    for term in tech_keywords:
        normalized = normalize_term(term)

        if normalized in PREDEFINED_TERMINOLOGY:
            # 사전 정의 사용
            entry = PREDEFINED_TERMINOLOGY[normalized]
            terminology.append(TerminologyEntry(
                term=term,
                definition=entry["definition"],
                category=entry["category"],
                difficulty=entry["difficulty"],
                related_terms=[],
            ))
        else:
            unknown_terms.append(term)

    # 알려지지 않은 용어는 LLM으로 생성
    if unknown_terms:
        generated = await llm_client.generate_terminology(
            terms=unknown_terms,
            language=language,
            context="기술 면접을 위한 용어 설명",
        )
        terminology.extend(generated)

    return terminology


def normalize_term(term: str) -> str:
    """용어 정규화"""
    TERM_MAPPING = {
        "fastapi": "FastAPI",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "react": "React",
        "reactjs": "React",
        "vue": "Vue.js",
        "vuejs": "Vue.js",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "ci/cd": "CI/CD",
        "cicd": "CI/CD",
        "graphql": "GraphQL",
        "rest": "REST API",
        "restful": "REST API",
        "websocket": "WebSocket",
        "grpc": "gRPC",
    }

    return TERM_MAPPING.get(term.lower(), term)
```

### LLM 용어 생성 프롬프트

```yaml
# prompts/jd_analysis/generate_terminology.yaml
metadata:
  id: terminology_generation
  version: "1.0"

system_prompt: |
  당신은 기술 용어를 면접관이 이해할 수 있도록 설명하는 전문가입니다.

  다음 기술 용어들에 대해 설명을 생성하세요:
  - 비개발자 면접관도 이해할 수 있는 수준
  - 핵심 개념만 간결하게 (2-3문장)
  - 실무에서 어떻게 사용되는지 포함

  응답 언어: {language}

user_prompt_template: |
  ## 설명할 용어
  {terms}

  ## 응답 형식
  ```json
  [
    {
      "term": "용어명",
      "definition": "간결한 설명",
      "category": "분류 (framework/database/concept/pattern/devops/language)",
      "difficulty": "난이도 (basic/intermediate/advanced)",
      "related_terms": ["관련 용어1", "관련 용어2"]
    }
  ]
  ```
```

---

## 기술 스택 분류

```python
TECH_CATEGORIES = {
    "language": [
        "Python", "JavaScript", "TypeScript", "Java", "Go",
        "Rust", "C++", "C#", "Ruby", "PHP", "Kotlin", "Swift"
    ],
    "frontend": [
        "React", "Vue.js", "Angular", "Svelte", "Next.js",
        "Nuxt.js", "HTML", "CSS", "Sass", "Tailwind"
    ],
    "backend": [
        "FastAPI", "Django", "Flask", "Spring", "Express",
        "NestJS", "Rails", "Laravel", "ASP.NET"
    ],
    "database": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "SQLite"
    ],
    "devops": [
        "Docker", "Kubernetes", "AWS", "GCP", "Azure",
        "Terraform", "Ansible", "Jenkins", "GitHub Actions"
    ],
    "concept": [
        "REST API", "GraphQL", "Microservices", "CI/CD",
        "TDD", "DDD", "Event Sourcing", "CQRS"
    ],
}


def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    """기술 스택 분류"""
    categorized = {cat: [] for cat in TECH_CATEGORIES}
    categorized["other"] = []

    for skill in skills:
        found = False
        for category, tech_list in TECH_CATEGORIES.items():
            if any(skill.lower() == t.lower() for t in tech_list):
                categorized[category].append(skill)
                found = True
                break

        if not found:
            categorized["other"].append(skill)

    # 빈 카테고리 제거
    return {k: v for k, v in categorized.items() if v}
```

---

## 벡터 저장

```python
async def store_jd_vectors(job_id: str, analysis: dict) -> None:
    """
    JD 분석 결과를 벡터 스토어에 저장
    """
    vector_store = get_vector_store(job_id)

    # JD 요약
    await vector_store.upsert(
        id="jd_summary",
        content=analysis["summary"],
        metadata={
            "type": "jd_summary",
            "position": analysis["position"],
            "experience_level": analysis["experience_level"],
        }
    )

    # 필수 기술
    for i, skill in enumerate(analysis.get("required_skills", [])):
        await vector_store.upsert(
            id=f"required_skill_{i}",
            content=f"필수 기술: {skill}",
            metadata={
                "type": "required_skill",
                "skill": skill,
                "priority": "high",
            }
        )

    # 우대 기술
    for i, skill in enumerate(analysis.get("preferred_skills", [])):
        await vector_store.upsert(
            id=f"preferred_skill_{i}",
            content=f"우대 기술: {skill}",
            metadata={
                "type": "preferred_skill",
                "skill": skill,
                "priority": "medium",
            }
        )

    # 담당 업무
    for i, resp in enumerate(analysis.get("responsibilities", [])):
        await vector_store.upsert(
            id=f"responsibility_{i}",
            content=resp,
            metadata={
                "type": "responsibility",
                "index": i,
            }
        )

    # 용어집
    for entry in analysis.get("terminology", []):
        await vector_store.upsert(
            id=f"term_{entry.term}",
            content=f"{entry.term}: {entry.definition}",
            metadata={
                "type": "terminology",
                "term": entry.term,
                "category": entry.category,
                "difficulty": entry.difficulty,
            }
        )
```

---

## 출력 예시

```json
{
  "position": "백엔드 개발자",
  "department": "플랫폼팀",
  "experience_level": "미들",
  "required_skills": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Docker"
  ],
  "preferred_skills": [
    "Kubernetes",
    "Redis",
    "AWS",
    "GraphQL"
  ],
  "responsibilities": [
    "REST API 설계 및 개발",
    "데이터베이스 스키마 설계",
    "CI/CD 파이프라인 구축",
    "코드 리뷰 및 기술 문서 작성"
  ],
  "qualifications": [
    "컴퓨터공학 관련 전공",
    "3년 이상의 백엔드 개발 경험",
    "대용량 트래픽 처리 경험"
  ],
  "tech_keywords": [
    "Python", "FastAPI", "PostgreSQL", "Docker",
    "Kubernetes", "Redis", "AWS", "REST API", "CI/CD"
  ],
  "terminology": [
    {
      "term": "FastAPI",
      "definition": "Python 기반 고성능 비동기 웹 프레임워크로, 자동 API 문서화와 타입 검증을 제공합니다.",
      "category": "framework",
      "difficulty": "intermediate",
      "related_terms": ["Pydantic", "Starlette", "ASGI"]
    },
    {
      "term": "CI/CD",
      "definition": "지속적 통합(CI)과 지속적 배포(CD)를 의미하며, 코드 변경사항을 자동으로 테스트하고 배포하는 프로세스입니다.",
      "category": "concept",
      "difficulty": "basic",
      "related_terms": ["GitHub Actions", "Jenkins", "DevOps"]
    }
  ],
  "summary": "플랫폼팀의 백엔드 개발자로, Python/FastAPI 기반 REST API 개발과 Docker/Kubernetes 환경에서의 서비스 운영을 담당합니다. 3년 이상의 경력과 대용량 트래픽 처리 경험이 필요합니다."
}
```

---

## 관련 파일

- `backend/app/workflows/activities/jd_analysis.py`
- `backend/app/services/jd_parser.py`
- `backend/app/prompts/jd_analysis/`
- `backend/app/data/terminology.json`

---

## 의존성

- **외부 서비스**: LLM (분석 및 용어 생성)
- **내부 서비스**: Vector Store (저장)
- **라이브러리**: re (정규식)
