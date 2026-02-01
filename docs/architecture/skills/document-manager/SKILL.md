# Document Manager Skill

> 이력서/포트폴리오 분석 에이전트

---

## 역할

이력서(PDF)와 포트폴리오(DOCX/PDF) 문서를 파싱하여 후보자 프로필을 구축합니다.

## 책임

1. **문서 다운로드**: S3에서 업로드된 문서 다운로드
2. **문서 파싱**: PDF/DOCX 텍스트 추출
3. **프로필 추출**: LLM으로 구조화된 정보 추출
4. **벡터 저장**: 추출된 정보를 벡터 스토어에 저장

---

## Activity 정의

### analyze_documents

```python
@activity.defn
async def analyze_documents(job_id: str, input_data: dict) -> dict:
    """
    문서 분석 및 프로필 구축

    Input:
        job_id: 작업 ID
        input_data: {
            resume_path: str | None,      # S3 key
            portfolio_path: str | None,   # S3 key
        }

    Output:
        CandidateProfile: {
            name: str,
            email: str | None,
            phone: str | None,
            experience_years: int,
            skills: list[str],
            education: list[Education],
            work_history: list[WorkExperience],
            projects: list[Project],
            summary: str,
            source_files: list[str],
            confidence_score: float,
        }
    """
```

---

## 문서 파싱 전략

### PDF 파싱

```python
from pypdf import PdfReader
import pdfplumber

async def parse_pdf(file_path: str) -> str:
    """
    PDF 텍스트 추출

    전략:
    1. pypdf로 기본 텍스트 추출 시도
    2. 텍스트가 부족하면 pdfplumber로 재시도 (표 처리)
    3. 이미지 PDF면 OCR 적용 (pytesseract)
    """
    text = ""

    # 1차: pypdf
    reader = PdfReader(file_path)
    for page in reader.pages:
        text += page.extract_text() or ""

    # 텍스트 부족 시 pdfplumber
    if len(text.strip()) < 100:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    # 여전히 부족하면 OCR
    if len(text.strip()) < 100:
        text = await ocr_pdf(file_path)

    return clean_text(text)
```

### DOCX 파싱

```python
from docx import Document

async def parse_docx(file_path: str) -> str:
    """
    DOCX 텍스트 추출

    추출 대상:
    - 본문 텍스트
    - 표 내용
    - 머리글/바닥글
    """
    doc = Document(file_path)

    text_parts = []

    # 본문
    for para in doc.paragraphs:
        text_parts.append(para.text)

    # 표
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text for cell in row.cells)
            text_parts.append(row_text)

    return clean_text("\n".join(text_parts))
```

---

## LLM 프로필 추출

### 프롬프트 템플릿

```yaml
# prompts/document_analysis/profile_extraction.yaml
metadata:
  id: profile_extraction
  version: "1.0"

system_prompt: |
  당신은 이력서와 포트폴리오에서 정보를 추출하는 전문가입니다.

  다음 문서에서 후보자 정보를 추출하세요.
  정보가 명시되지 않은 경우 null로 표시하세요.
  추측하지 말고, 문서에 있는 내용만 추출하세요.

user_prompt_template: |
  ## 문서 내용
  {document_text}

  ## 추출할 정보
  다음 JSON 형식으로 응답하세요:

  ```json
  {
    "name": "이름",
    "email": "이메일 또는 null",
    "phone": "전화번호 또는 null",
    "experience_years": 경력년수(숫자),
    "skills": ["기술1", "기술2", ...],
    "education": [
      {
        "institution": "학교명",
        "degree": "학위",
        "major": "전공 또는 null",
        "graduation_year": 졸업년도 또는 null
      }
    ],
    "work_history": [
      {
        "company": "회사명",
        "position": "직위",
        "period": "기간 (예: 2020.03 - 2023.05)",
        "description": "업무 설명",
        "tech_stack": ["기술1", "기술2"]
      }
    ],
    "projects": [
      {
        "name": "프로젝트명",
        "description": "설명",
        "role": "역할",
        "tech_stack": ["기술1", "기술2"],
        "period": "기간 또는 null",
        "url": "URL 또는 null"
      }
    ]
  }
  ```

output_schema:
  type: object
  required: [name, skills]
```

---

## 프로필 보강 로직

```python
async def enrich_profile(raw_profile: dict, document_text: str) -> dict:
    """
    추출된 프로필 보강

    1. 경력 년수 계산 (명시 안 된 경우)
    2. 기술 스택 정규화
    3. 신뢰도 점수 계산
    4. 요약 생성
    """
    profile = raw_profile.copy()

    # 경력 년수 계산
    if not profile.get("experience_years"):
        profile["experience_years"] = calculate_experience_years(
            profile.get("work_history", [])
        )

    # 기술 스택 정규화 (대소문자, 동의어 통일)
    profile["skills"] = normalize_skills(profile.get("skills", []))

    # 신뢰도 점수 (추출된 필드 수 기반)
    profile["confidence_score"] = calculate_confidence(profile)

    # 요약 생성 (LLM)
    profile["summary"] = await generate_summary(profile)

    return profile


def normalize_skills(skills: list[str]) -> list[str]:
    """
    기술 스택 정규화

    매핑 예시:
    - "python", "Python", "PYTHON" -> "Python"
    - "react.js", "ReactJS", "React" -> "React"
    - "postgres", "PostgreSQL", "psql" -> "PostgreSQL"
    """
    SKILL_MAPPING = {
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "react": "React",
        "react.js": "React",
        "reactjs": "React",
        "vue": "Vue.js",
        "vue.js": "Vue.js",
        "angular": "Angular",
        "node": "Node.js",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "spring": "Spring",
        "spring boot": "Spring Boot",
    }

    normalized = []
    seen = set()

    for skill in skills:
        key = skill.lower().strip()
        mapped = SKILL_MAPPING.get(key, skill)

        if mapped.lower() not in seen:
            normalized.append(mapped)
            seen.add(mapped.lower())

    return normalized
```

---

## 벡터 저장

```python
async def store_profile_vectors(job_id: str, profile: dict) -> None:
    """
    프로필 정보를 벡터 스토어에 저장

    저장 대상:
    1. 전체 프로필 요약
    2. 각 경력 항목
    3. 각 프로젝트 항목
    """
    vector_store = get_vector_store(job_id)

    # 프로필 요약
    await vector_store.upsert(
        id=f"profile_summary",
        content=profile["summary"],
        metadata={
            "type": "profile_summary",
            "name": profile["name"],
            "skills": profile["skills"],
        }
    )

    # 경력 항목
    for i, work in enumerate(profile.get("work_history", [])):
        content = f"{work['company']} - {work['position']}: {work['description']}"
        await vector_store.upsert(
            id=f"work_{i}",
            content=content,
            metadata={
                "type": "work_experience",
                "company": work["company"],
                "tech_stack": work.get("tech_stack", []),
            }
        )

    # 프로젝트 항목
    for i, project in enumerate(profile.get("projects", [])):
        content = f"{project['name']}: {project['description']} (역할: {project['role']})"
        await vector_store.upsert(
            id=f"project_{i}",
            content=content,
            metadata={
                "type": "project",
                "name": project["name"],
                "tech_stack": project.get("tech_stack", []),
            }
        )
```

---

## 출력 예시

```json
{
  "name": "김개발",
  "email": "dev@example.com",
  "phone": "010-1234-5678",
  "experience_years": 5,
  "skills": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Redis",
    "Docker",
    "AWS"
  ],
  "education": [
    {
      "institution": "서울대학교",
      "degree": "학사",
      "major": "컴퓨터공학",
      "graduation_year": 2019
    }
  ],
  "work_history": [
    {
      "company": "테크스타트업",
      "position": "백엔드 개발자",
      "period": "2021.03 - 현재",
      "description": "결제 시스템 개발 및 API 설계",
      "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
    }
  ],
  "projects": [
    {
      "name": "실시간 알림 시스템",
      "description": "WebSocket 기반 실시간 알림 서비스 구축",
      "role": "메인 개발자",
      "tech_stack": ["Python", "Redis", "WebSocket"],
      "period": "2022.06 - 2022.12",
      "url": null
    }
  ],
  "summary": "5년차 백엔드 개발자로, Python/FastAPI 기반 API 개발과 결제 시스템 구축 경험이 풍부합니다.",
  "source_files": ["resume.pdf"],
  "confidence_score": 0.92
}
```

---

## 관련 파일

- `backend/app/workflows/activities/document_analysis.py`
- `backend/app/services/document_parser.py`
- `backend/app/prompts/document_analysis/`

---

## 의존성

- **외부 서비스**: S3 (파일 다운로드), LLM (프로필 추출)
- **내부 서비스**: Vector Store (저장)
- **라이브러리**: pypdf, pdfplumber, python-docx, pytesseract
