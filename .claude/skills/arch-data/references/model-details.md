# Data Model Details Reference

50+ Pydantic/DB 모델의 상세 정의.

## Input Layer

### InputData (Raw)
```python
class InputData(BaseModel):
    job_description: str          # JD 텍스트
    experience_level: str         # 경력 수준 (Junior/Mid/Senior/CTO)
    output_language: str          # 출력 언어 (ko/en)
    num_questions: int            # 질문 수 (5-25)
    resume_file: UploadFile | None
    portfolio_file: UploadFile | None
    linkedin_url: str | None
    github_urls: list[str]
```

### EnrichedInput (Phase 0 결과)
```python
class EnrichedInput(InputData):
    discovered_linkedin_url: str | None   # 이력서에서 발견한 LinkedIn
    discovered_github_urls: list[str]     # 이력서에서 발견한 GitHub
    linkedin_profile: LinkedInProfile | None  # Bright Data 수집 결과
    resume_text: str | None               # 추출된 텍스트
    portfolio_text: str | None
```

## Analysis Layer

### CandidateProfile (문서 분석)
```python
class CandidateProfile(BaseModel):
    name: str
    title: str
    summary: str
    experience_years: int
    skills: list[Skill]
    education: list[Education]
    projects: list[Project]
    certifications: list[str]
```

### CodeAnalysis (코드 분석)
```python
class CodeAnalysis(BaseModel):
    repositories: list[RepoAnalysis]
    tech_stack: list[TechStack]
    code_quality_metrics: CodeQualityMetrics
    contribution_patterns: ContributionPattern
    engineering_dna: EngineeringDNA
```

### JDAnalysis (JD 분석)
```python
class JDAnalysis(BaseModel):
    required_skills: list[Skill]
    preferred_skills: list[Skill]
    experience_requirements: ExperienceReq
    role_description: str
    tech_stack: list[str]
```

## Output Layer

### InterviewScript (최종)
```python
class InterviewScript(BaseModel):
    candidate_summary: CandidateSummary
    questions: list[InterviewQuestion]  # 25개
    decision_guide: DecisionGuide
    interviewer_guide: InterviewerGuide
    intel_brief: IntelBrief
    deep_analysis: DeepAnalysis
    decision_support: DecisionSupport
```

## DB Tables

| 테이블 | 컬럼 | 용도 |
|--------|------|------|
| jobs | id(UUID), user_id, status, input_data(JSONB), result(JSONB), created_at | Job 메타데이터 |
| users | id(UUID), email, provider, name, picture | OAuth 사용자 |
| api_keys | id(UUID), user_id, key_hash(SHA-256), name, last_used | API 키 |
| checkpoints | id(UUID), job_id, phase, data(JSONB), created_at | 단계별 체크포인트 |
| vectors | id(UUID), content, embedding(VECTOR(1536)), metadata(JSONB) | pgvector 저장 |

## Enum 정의

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class QuestionCategory(str, Enum):
    ROLE_FIT = "role_fit"
    TECHNICAL = "technical"
    EXECUTION = "execution"
    COMMUNICATION = "communication"
    RISK_FLAGS = "risk_flags"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
```
