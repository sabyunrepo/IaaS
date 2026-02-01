# 02. Data Models

> 시스템에서 사용되는 모든 데이터 모델 정의

---

## 1. 핵심 식별자

### 1.1 Job Identifier
```python
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class JobIdentifier(BaseModel):
    """작업 식별자 - 모든 데이터 격리의 기준"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str                      # 소유자 (API Key → User UUID)
    session_id: str                   # 서버 자동생성
    tenant_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def create(user_id: str, session_id: str, tenant_id: str | None = None) -> "JobIdentifier":
        return JobIdentifier(
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
        )
```

### 1.2 Job Status
```python
from enum import Enum

class JobStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"           # 대기 중
    ENRICHING = "enriching"       # 입력 보강 중 (Phase 0)
    PLANNING = "planning"         # 계획 수립 중
    ANALYZING = "analyzing"       # 분석 중 (Document/Code/JD)
    GENERATING = "generating"     # 질문 생성 중
    REVIEWING = "reviewing"       # 품질 검토 중
    FINALIZING = "finalizing"     # 최종화 중
    COMPLETED = "completed"       # 완료
    FAILED = "failed"            # 실패
    CANCELLED = "cancelled"       # 취소됨
```

---

## 2. 입력 데이터 모델

### 2.1 Input Data
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Literal

class LanguageConfig(BaseModel):
    """언어 설정"""
    output_language: str = Field("ko", description="출력 언어 코드")
    terminology_languages: list[str] = Field(
        default=["ko", "en"],
        description="용어집에 포함할 언어들"
    )

class InputData(BaseModel):
    """면접 스크립트 생성 요청 입력 (유저가 가진 것만 제공)"""

    # 문서 입력
    resume_path: str | None = Field(None, description="이력서 파일 경로 (S3 key)")
    portfolio_path: str | None = Field(None, description="포트폴리오 파일 경로")

    # LinkedIn
    linkedin_url: str | None = Field(
        None,
        description="LinkedIn 프로필 URL (이력서 대체 가능, Proxycurl로 수집)"
    )

    # GitHub
    github_urls: list[HttpUrl] = Field(
        default_factory=list,
        description="분석할 GitHub 레포지토리 URL 목록 (직접 입력 또는 자동 추출)"
    )
    candidate_github_username: str | None = Field(
        None,
        description="후보자 GitHub 사용자명 (자동 추론 가능)"
    )

    # JD
    jd_text: str = Field(..., min_length=50, description="채용공고 텍스트")

    # 옵션
    experience_level: Literal["신입", "주니어", "미들", "시니어"] = Field(
        ...,
        description="후보자 경험 레벨"
    )

    language_config: LanguageConfig = Field(
        default_factory=LanguageConfig,
        description="언어 설정"
    )

    max_questions: int = Field(10, ge=5, le=20, description="생성할 질문 수")
    include_expected_answers: bool = Field(True, description="예상 답변 포함 여부")
    focus_areas: list[str] | None = Field(None, description="집중할 기술 영역")


class LinkedInExperience(BaseModel):
    """LinkedIn 경력 정보"""
    company: str
    title: str
    period: str                    # "Jan 2020 - Present"
    location: str | None
    description: str | None

class LinkedInEducation(BaseModel):
    """LinkedIn 학력 정보"""
    school: str
    degree: str | None
    field_of_study: str | None
    period: str | None             # "2015 - 2019"

class LinkedInCertification(BaseModel):
    """LinkedIn 자격증 정보"""
    name: str
    issuing_organization: str | None
    issue_date: str | None

class LinkedInProfile(BaseModel):
    """Proxycurl API 응답에서 추출한 LinkedIn 프로필"""
    full_name: str                              # ⚠️ PII
    headline: str | None
    summary: str | None
    experiences: list[LinkedInExperience]
    education: list[LinkedInEducation]
    skills: list[str]
    certifications: list[LinkedInCertification]
    github_url: str | None                      # LinkedIn에서 발견된 GitHub URL
    websites: list[str]                         # 기타 링크 (포트폴리오 등)


class EnrichedInput(BaseModel):
    """Phase 0 Smart Input Extraction 결과
    유저의 raw input에서 교차 추출하여 빈 필드를 자동으로 채운 결과.
    이후 모든 Phase는 이 모델을 입력으로 사용.
    """
    # 원본 입력 보존
    raw_input: InputData

    # 교차 추출으로 보강된 필드
    github_urls: list[HttpUrl]               # 모든 소스에서 수집된 GitHub URLs (중복 제거)
    candidate_github_username: str | None     # GitHub URL에서 자동 추론
    linkedin_profile: LinkedInProfile | None  # Proxycurl 수집 결과

    # 추출 소스 추적
    extraction_sources: dict[str, list[str]]
    # 예: {"github_urls": ["resume", "portfolio", "linkedin"], "linkedin_url": ["resume"]}

    # 사용 가능한 분석 목록 (Planning에서 참조)
    available_analyses: list[str]
    # 예: ["document_analysis", "code_analysis", "jd_analysis", "linkedin_analysis"]
```

### 2.2 Job Request (API)
```python
class CreateJobRequest(BaseModel):
    """Job 생성 API 요청"""
    input_data: InputData
    callback_url: str | None = Field(None, description="완료 시 호출할 웹훅 URL")
    priority: Literal["low", "normal", "high"] = "normal"

class CreateJobResponse(BaseModel):
    """Job 생성 API 응답"""
    job_id: str
    status: JobStatus
    estimated_time_seconds: int
    created_at: datetime
```

---

## 3. 분석 결과 모델

### 3.1 Candidate Profile (문서 분석 결과)
```python
class Education(BaseModel):
    """학력 정보"""
    institution: str
    degree: str
    major: str | None
    graduation_year: int | None

class WorkExperience(BaseModel):
    """경력 정보"""
    company: str
    position: str
    period: str  # "2020.03 - 2023.05"
    description: str
    tech_stack: list[str]

class Project(BaseModel):
    """프로젝트 정보"""
    name: str
    description: str
    role: str
    tech_stack: list[str]
    period: str | None
    url: str | None

class CandidateProfile(BaseModel):
    """후보자 프로필 (문서 분석 결과)"""
    name: str              # ⚠️ PII
    email: str | None      # ⚠️ PII
    phone: str | None      # ⚠️ PII

    experience_years: int
    skills: list[str]

    education: list[Education]
    work_history: list[WorkExperience]
    projects: list[Project]

    summary: str  # LLM이 생성한 요약

    # 메타데이터
    source_files: list[str]  # 분석한 파일 목록
    confidence_score: float  # 추출 신뢰도
```

### 3.2 Code Analysis (코드 분석 결과)
```python
class CodePattern(BaseModel):
    """탐지된 코드 패턴"""
    pattern_type: str  # "design_pattern", "anti_pattern", "idiom"
    name: str          # "Singleton", "Factory", "Context Manager"
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    explanation: str

class ComplexityMetrics(BaseModel):
    """복잡도 지표"""
    total_lines: int
    code_lines: int
    comment_lines: int
    avg_function_length: float
    max_function_length: int
    cyclomatic_complexity_avg: float

class QualityIssue(BaseModel):
    """품질 이슈"""
    severity: Literal["info", "warning", "error"]
    category: str  # "security", "performance", "maintainability"
    message: str
    file_path: str
    line: int | None

class NotableImplementation(BaseModel):
    """주목할 만한 구현"""
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    why_notable: str  # 왜 주목할 만한지
    question_potential: float  # 질문 생성 가능성 점수 (0-1)

class CandidateContribution(BaseModel):
    """후보자 기여도 정보 (PyDriller 추출)"""
    total_commits: int            # 후보자가 작성한 커밋 수
    total_additions: int          # 추가한 라인 수
    total_deletions: int          # 삭제한 라인 수
    avg_complexity: float         # 후보자 코드 평균 cyclomatic complexity
    files_modified: int           # 수정한 파일 수
    analysis_period_years: int    # 분석 기간 (기본 3년)
    primary_file_types: list[str] # 주로 수정한 파일 타입 [".py", ".sql"]

class ASTFunction(BaseModel):
    """AST 추출 함수 정보"""
    name: str
    params: list[str]
    return_type: str | None
    decorators: list[str]
    complexity: int | None

class ASTClass(BaseModel):
    """AST 추출 클래스 정보"""
    name: str
    bases: list[str]
    methods: list[str]
    attributes: list[str]

class ASTPattern(BaseModel):
    """AST 탐지 디자인 패턴"""
    pattern_type: str    # "Singleton", "Factory", "Observer" 등
    name: str
    evidence: str        # 패턴 근거 코드 위치

class ASTAnalysis(BaseModel):
    """AST 구조 분석 결과 (Phase 3)
    MVP 지원: Python (ast 빌트인), JS/TS (tree-sitter)
    미지원 언어: fallback → Phase 2 메트릭만 사용
    """
    functions: list[ASTFunction]
    classes: list[ASTClass]
    patterns: list[ASTPattern]
    imports: list[dict]          # [{module, alias, is_third_party}]
    parser_used: str             # "ast" | "tree-sitter" | "fallback"

class RepositoryAnalysis(BaseModel):
    """단일 레포지토리 분석 결과"""
    repo_url: str
    repo_name: str

    # 기본 정보
    language: str              # primary language (PyGithub)
    language_ratio: float      # 해당 언어 비율 (0.0~1.0)
    total_files: int
    analyzed_files: int

    # 후보자 기여도 (PyDriller)
    candidate_contribution: CandidateContribution

    # AST 구조 분석 (Phase 3)
    ast_analysis: ASTAnalysis | None  # 미지원 언어 시 None

    # 분석 결과
    tech_stack: list[str]
    patterns: list[CodePattern]
    complexity: ComplexityMetrics
    quality_issues: list[QualityIssue]
    notable_implementations: list[NotableImplementation]

    # 메타데이터
    last_commit_date: datetime | None
    contributors_count: int
    jd_match_score: float      # JD 기술스택 매칭 점수 (0.0~1.0)

class CodeAnalysis(BaseModel):
    """전체 코드 분석 결과"""
    repositories: list[RepositoryAnalysis]

    # 집계 데이터
    combined_tech_stack: list[str]
    total_patterns: int
    total_notable_implementations: int

    # 질문 생성용 요약
    top_question_candidates: list[NotableImplementation]
```

### 3.3 JD Analysis (채용공고 분석 결과)
```python
class Requirement(BaseModel):
    """요구사항"""
    category: Literal["필수", "우대"]
    skill: str
    detail: str | None
    experience_years: int | None

class SkillMatch(BaseModel):
    """스킬 매칭 결과"""
    required_skill: str
    candidate_skill: str | None
    match_type: Literal["exact", "similar", "partial", "none"]
    evidence: str | None  # 코드나 문서에서 찾은 증거
    confidence: float

class JDAnalysis(BaseModel):
    """채용공고 분석 결과"""
    # 추출된 정보
    job_title: str
    company_name: str | None

    # 요구사항
    requirements: list[Requirement]
    responsibilities: list[str]

    # 회사 문화/특징
    company_culture: list[str]

    # 스킬 매칭 (후보자 프로필과 비교)
    skill_matches: list[SkillMatch]
    overall_match_score: float

    # 갭 분석
    gaps: list[str]  # 후보자에게 부족한 부분
    strengths: list[str]  # 후보자의 강점
```

---

## 4. 질문 데이터 모델

### 4.1 Terminology (용어 설명)
```python
class TerminologyEntry(BaseModel):
    """용어집 항목 (다국어 + LLM 동적 생성)"""
    term: str  # 원본 기술 용어 (영문)
    category: str  # database, framework, pattern, etc.

    # 다국어 지원
    translations: dict[str, str]  # {"ko": "레디스", "en": "Redis"}
    synonyms: dict[str, list[str]]  # {"ko": ["인메모리 캐시", "메모리 DB"]}
    pronunciation: dict[str, str] | None  # {"ko": "레디스"}
    simple_explanation: dict[str, str]  # 비개발자용 설명

    # 메타데이터
    llm_generated: bool = False  # LLM이 동적으로 생성했는지
    confidence: float = 1.0  # LLM 생성 시 신뢰도
```

### 4.2 Expected Answer (예상 답변)
```python
class CodeEvidence(BaseModel):
    """코드 증거"""
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    explanation: str

class ExpectedAnswer(BaseModel):
    """예상 답변 스크립트"""
    # 핵심 답변 포인트
    core_answer: str  # 불릿 포인트 형식

    # 실제 대화체 예시
    example_script: str  # 자연스러운 답변 예시

    # 코드 증거
    code_evidence: list[CodeEvidence]

    # 핵심 키워드
    key_points: list[str]

    # 레벨별 기대치
    depth_expectations: dict[str, str]  # {"신입": "...", "시니어": "..."}
```

### 4.3 Interview Question (면접 질문)
```python
class EvaluationScenario(BaseModel):
    """평가 시나리오"""
    excellent: str  # 우수한 답변 시나리오
    good: str       # 양호한 답변 시나리오
    poor: str       # 미흡한 답변 시나리오

class CodeReference(BaseModel):
    """코드 참조"""
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    explanation: str | None

class InterviewQuestion(BaseModel):
    """면접 질문 (최종 출력 단위)"""
    id: str  # q1, q2, ...
    sequence: int  # 순서
    topic: str  # 질문 주제

    # 주 언어 질문 (생성 시 output_language만 생성)
    question_text: str
    alternative_phrasings: list[str]  # 대체 표현

    # 코드 참조
    code_reference: CodeReference | None

    # 평가 기준
    evaluation_scenarios: EvaluationScenario

    # 꼬리질문
    follow_ups: list[str]

    # 예상 답변
    expected_answer: ExpectedAnswer

    # 다국어: 요청 시 on-demand 번역 (저장 X, API 호출로 동적 생성)
    language: str  # 생성된 언어 코드 ("ko", "en" 등)

    # 용어집
    terminology: list[TerminologyEntry]

    # 메타데이터
    difficulty: Literal["basic", "intermediate", "advanced"]
    estimated_time_minutes: int
    skills_assessed: list[str]
```

---

## 5. 최종 출력 모델

### 5.1 Interview Script (최종 출력)
```python
class CandidateSummary(BaseModel):
    """후보자 요약"""
    name: str
    experience_level: str
    experience_years: int
    key_skills: list[str]
    jd_match_score: float
    strengths: list[str]
    areas_to_probe: list[str]  # 면접에서 확인할 부분

class InterviewerGuide(BaseModel):
    """면접관 가이드"""
    total_duration_minutes: int
    question_order_rationale: str  # 질문 순서 이유
    tips: list[str]  # 면접 진행 팁
    warning_signs: list[str]  # 주의해야 할 신호

class InterviewScript(BaseModel):
    """최종 면접 스크립트"""
    # 메타데이터
    job_id: str
    generated_at: datetime
    output_language: str

    # 후보자 정보
    candidate_summary: CandidateSummary

    # 질문 목록
    questions: list[InterviewQuestion]

    # 면접관 가이드
    interviewer_guide: InterviewerGuide

    # 용어 총집합 (전체 질문의 용어 취합)
    full_glossary: list[TerminologyEntry]

    # 통계
    metadata: dict[str, Any]  # 생성 통계, 토큰 사용량 등
```

---

## 6. 내부 상태 모델

### 6.1 Workflow State (Temporal 상태)
```python
class AnalysisPhaseResult(BaseModel):
    """분석 단계 결과"""
    document_analysis: CandidateProfile | None
    code_analysis: CodeAnalysis | None
    jd_analysis: JDAnalysis | None

class QuestionGenerationState(BaseModel):
    """질문 생성 상태"""
    selected_topics: list[dict]
    generated_questions: list[InterviewQuestion]
    review_feedback: dict | None
    revision_count: int

class WorkflowState(BaseModel):
    """전체 워크플로우 상태"""
    # 식별자
    job: JobIdentifier
    input_data: InputData

    # Phase 0: Input Enrichment
    enriched_input: EnrichedInput | None

    # Phase 1: Planning
    execution_plan: dict | None
    estimated_workload: dict | None

    # Phase 2: Analysis
    analysis_result: AnalysisPhaseResult

    # Phase 3: Question Generation
    question_state: QuestionGenerationState

    # Phase 4: Finalization
    final_output: InterviewScript | None

    # 메타
    current_phase: str
    errors: list[dict]
    checkpoints: list[str]
    started_at: datetime
    completed_at: datetime | None
```

---

## 7. 체크포인트 및 캐시 모델

### 7.1 Pipeline Step 정의
```python
"""
backend/app/models/checkpoint.py
체크포인트 관련 타입 정의
"""
from typing import Literal, TypeAlias
from pydantic import BaseModel
from datetime import datetime

# 파이프라인 단계 (실행 순서)
PipelineStep: TypeAlias = Literal[
    "enrich_input",
    "plan",
    "document_analysis",
    "code_analysis",
    "jd_analysis",
    "aggregate_analysis",
    "select_topics",
    "craft_questions",
    "review_quality",
    "finalize",
]

PIPELINE_STEPS: list[PipelineStep] = [
    "enrich_input", "plan", "document_analysis", "code_analysis",
    "jd_analysis", "aggregate_analysis", "select_topics",
    "craft_questions", "review_quality", "finalize",
]


class CheckpointMeta(BaseModel):
    """체크포인트 메타정보"""
    job_id: str
    step: PipelineStep
    status: Literal["completed", "failed", "partial"]
    saved_at: datetime
    size_bytes: int
    storage: Literal["redis", "s3", "both"]


class CheckpointStatus(BaseModel):
    """Job 체크포인트 전체 상태"""
    job_id: str
    steps: list[dict]  # [{"name": step, "status": "completed"|"pending"}]
    completed_steps: list[PipelineStep]
    resume_point: PipelineStep | None
    total_steps: int
    completed_count: int


class RetryRequest(BaseModel):
    """재시작 요청"""
    from_step: PipelineStep | None = None  # None이면 자동 감지
    force_rerun: bool = False  # True면 캐시 무시하고 재실행


class RetryResponse(BaseModel):
    """재시작 응답"""
    job_id: str
    status: str  # "retrying"
    resume_from: PipelineStep
    skipped_steps: list[PipelineStep]
    cached_steps: list[PipelineStep]
```

### 7.2 LLM 캐시 모델
```python
class LLMCacheEntry(BaseModel):
    """LLM 캐시 항목 (모니터링/디버깅용)"""
    model: str
    prompt_hash: str
    content: str
    usage: dict  # {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    cached_at: datetime
    ttl_seconds: int
    hit_count: int = 0

class LLMCacheStats(BaseModel):
    """LLM 캐시 통계"""
    total_hits: int
    total_misses: int
    hit_rate: float  # 0.0 ~ 1.0
    estimated_cost_saved: float  # 캐시로 절약한 예상 비용 ($)
    total_tokens_saved: int
```

---

## 8. 데이터베이스 스키마

### 8.1 PostgreSQL Tables

```sql
-- 작업 테이블
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',

    -- 입력 데이터 (JSONB)
    input_data JSONB NOT NULL,

    -- 결과 (JSONB)
    analysis_result JSONB,
    final_output JSONB,

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_jobs_user ON jobs (user_id);
CREATE INDEX idx_jobs_session ON jobs (session_id);
CREATE INDEX idx_jobs_tenant ON jobs (tenant_id);
CREATE INDEX idx_jobs_status ON jobs (status);

-- 코드 분석 결과 (벡터 검색용)
CREATE TABLE code_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,

    -- 원본 데이터
    file_path VARCHAR(500) NOT NULL,
    code_snippet TEXT NOT NULL,
    snippet_type VARCHAR(50),  -- function, class, pattern

    -- 벡터
    embedding vector(%EMBEDDING_DIM%),  -- settings.EMBEDDING_DIMENSION (default 1536, ada-002)

    -- 메타데이터
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

);

CREATE INDEX idx_code_job ON code_embeddings (job_id);

-- 벡터 검색 인덱스
CREATE INDEX idx_code_embedding_vector
ON code_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 학습 데이터 수집용
-- ⚠️ Phase 2: Langfuse Datasets로 마이그레이션 예정
--   Langfuse가 프롬프트 관리 + 데이터셋 관리 + 품질 평가를 통합 제공
--   이 테이블은 MVP에서 raw 로그 백업용으로 유지
CREATE TABLE training_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),

    -- LLM 입출력
    agent_type VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,

    -- 품질 레이블
    quality VARCHAR(50) DEFAULT 'unlabeled',
    quality_score FLOAT,
    human_feedback TEXT,

    -- 메타데이터
    model_used VARCHAR(100),
    prompt_tokens INT,
    completion_tokens INT,
    latency_ms INT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 8.2 Redis Keys

```
# Job 상태 캐시
job:{job_id}:status -> JSON (JobStatus)
job:{job_id}:progress -> JSON (진행률 정보)
job:{job_id}:input -> JSON (원본 입력, 재시작용, TTL 7d)

# 분석 결과 캐시 (처리 중)
job:{job_id}:document_analysis -> JSON
job:{job_id}:code_analysis -> JSON
job:{job_id}:jd_analysis -> JSON

# 체크포인트 (단계별 스냅샷)
checkpoint:{job_id}:{step_name} -> JSON (TTL 7d)
checkpoint:{job_id}:_meta -> Hash { step: "completed" } (TTL 7d)

# LLM 결과 캐시
llm_cache:{model}:{prompt_hash} -> JSON (TTL 24h)

# 세션별 최근 작업
session:{session_id}:recent_jobs -> List[job_id] (최근 10개)

# Rate Limiting
ratelimit:github:{token_hash} -> Counter (분당 API 호출)
ratelimit:llm:{api_key_hash} -> Counter (분당 토큰)
```

---

## 9. 파일 저장 구조 (S3)

```
s3://vantict-data/
├── uploads/
│   └── {job_id}/
│       ├── resume.pdf
│       └── portfolio.docx
│
├── analysis/
│   └── {job_id}/
│       ├── document_analysis.json
│       ├── code_analysis.json
│       └── jd_analysis.json
│
├── repos/
│   └── {job_id}/
│       └── {repo_name}/
│           └── (클론된 코드, 분석 후 삭제)
│
├── outputs/
│   └── {job_id}/
│       ├── interview_script.json
│       ├── interview_script_ko.pdf
│       └── interview_script_en.pdf
│
└── training/
    ├── raw/
    │   └── {job_id}/
    │       └── {example_id}.json
    └── exports/
        └── {format}/
            └── {timestamp}.jsonl
```

---

## 10. 타입 정의 모음 (Python)

### types.py
```python
"""
backend/app/models/types.py
공통 타입 정의
"""
from typing import Literal, TypeAlias

# 지원 언어
SupportedLanguage: TypeAlias = Literal[
    "ko", "en", "ja", "zh-CN", "zh-TW",
    "es", "de", "fr", "pt", "vi", "th", "id"
]

# 경험 레벨
ExperienceLevel: TypeAlias = Literal["신입", "주니어", "미들", "시니어"]

# 질문 난이도
Difficulty: TypeAlias = Literal["basic", "intermediate", "advanced"]

# 요구사항 구분
RequirementCategory: TypeAlias = Literal["필수", "우대"]

# 코드 패턴 유형
PatternType: TypeAlias = Literal["design_pattern", "anti_pattern", "idiom"]

# 이슈 심각도
Severity: TypeAlias = Literal["info", "warning", "error"]

# 스킬 매칭 유형
MatchType: TypeAlias = Literal["exact", "similar", "partial", "none"]

# 학습 데이터 품질
DataQuality: TypeAlias = Literal["unlabeled", "auto", "verified", "gold"]
```

---

*이전: [01-overview.md](./01-overview.md) | 다음: [03-workflow.md](./03-workflow.md)*
