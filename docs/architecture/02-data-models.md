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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def create(user_id: str) -> "JobIdentifier":
        return JobIdentifier(user_id=user_id)
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

## 1.5 인증 모델

### 이중 인증 구조
- **프론트엔드 (React SPA)**: FastAPI OAuth 엔드포인트 → JWT 발급 → Authorization 헤더
- **프로그래밍 API**: API Key (SHA-256 해시) → 직접 호출

```python
class User(BaseModel):
    """사용자 (OAuth 로그인 시 자동 생성)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str | None = None
    image: str | None = None          # OAuth 프로필 이미지
    plan: Literal["free", "pro", "enterprise"] = "free"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OAuthAccount(BaseModel):
    """OAuth 연결 계정"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    provider: str                      # "google" | "github"
    provider_account_id: str           # OAuth provider의 고유 ID
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: int | None = None      # Unix timestamp
    token_type: str | None = None
    scope: str | None = None

class APIKey(BaseModel):
    """API Key (프로그래밍 접근용, 원본은 생성 시 1회만 반환)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key_prefix: str             # "vnt_xxxx" (식별용)
    name: str | None = None
    is_active: bool = True
    last_used_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### OAuth 로그인 시퀀스

> React SPA → FastAPI가 OAuth를 직접 처리 → JWT 발급 → React가 메모리에 저장

```
[React SPA] → "Google로 로그인" 클릭
    │
    ▼
[FastAPI GET /api/v1/auth/login/google]
    → authorization_url 생성 → 302 Redirect
    │
    ▼
[Google OAuth 동의 화면]
    → 사용자 동의 → code 발급
    │
    ▼
[FastAPI GET /api/v1/auth/callback/google?code=xxx]
    │
    ├─ 1. code → access_token 교환 (Google API)
    ├─ 2. access_token → 사용자 정보 조회 (email, name, image)
    ├─ 3. users upsert + oauth_accounts upsert (트랜잭션)
    └─ 4. 자체 JWT 발급 (HS256, user_id + plan 포함)
    │
    ▼
[302 Redirect → React SPA /auth/callback?token=<jwt>]
    │
    ▼
[React SPA]
    ├─ URL에서 JWT 추출 → 메모리 저장
    └─ 이후 모든 API 호출: Authorization: Bearer <jwt>
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
    cover_letter_path: str | None = Field(None, description="자기소개서/커버레터 파일 경로")

    # LinkedIn
    linkedin_url: str | None = Field(
        None,
        description="LinkedIn 프로필 URL (이력서 대체 가능, Bright Data로 수집)"
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
    experience_level: Literal["신입", "주니어", "미들", "시니어", "CTO/VP"] = Field(
        ...,
        description="후보자 경험 레벨"
    )

    language_config: LanguageConfig = Field(
        default_factory=LanguageConfig,
        description="언어 설정"
    )

    max_questions: int = Field(25, ge=5, le=25, description="생성할 질문 수 (기본 25, 카테고리별 5개)")
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
    """Bright Data API 응답에서 추출한 LinkedIn 프로필"""
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
    linkedin_profile: LinkedInProfile | None  # Bright Data 수집 결과

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
    analysis_period_years: int    # 분석 기간 (GITHUB_ANALYSIS_YEARS 환경변수, 기본 1년)
    primary_file_types: list[str] # 주로 수정한 파일 타입 [".py", ".sql"]


# ── GitHub 종합 분석 모델 (4-Channel) ──

class CommitDiff(BaseModel):
    """커밋 diff 정보 (토큰 효율적)"""
    commit_hash: str              # 커밋 해시 (8자)
    message: str                  # 커밋 메시지
    date: datetime
    file_path: str
    diff: str                     # diff만 추출 (source_code 대신)
    additions: int
    deletions: int
    complexity: int | None        # cyclomatic complexity


class OSSContribution(BaseModel):
    """오픈소스 PR 기여 (Channel B)"""
    repo_full_name: str           # "owner/repo" (외부 레포)
    pr_number: int
    pr_title: str
    pr_description: str | None
    pr_url: str                   # GitHub permalink
    files_changed: int
    additions: int
    deletions: int
    merged_at: datetime
    review_comments_count: int    # 받은 리뷰 코멘트 수
    labels: list[str]             # PR 라벨 (bugfix, feature 등)


class IssueParticipation(BaseModel):
    """이슈 참여 정보 (Channel C)"""
    repo_full_name: str
    issue_number: int
    issue_title: str
    issue_url: str
    role: Literal["author", "commenter"]  # 작성자 vs 코멘터
    state: Literal["open", "closed"]
    labels: list[str]
    body_summary: str | None      # 이슈 본문 요약 (300자)
    comment_count: int            # 참여한 코멘트 수
    created_at: datetime


class CodeReviewActivity(BaseModel):
    """코드 리뷰 활동 (Channel D)"""
    repo_full_name: str
    pr_number: int
    pr_title: str
    pr_url: str
    review_state: Literal["APPROVED", "CHANGES_REQUESTED", "COMMENTED"]
    review_body: str | None       # 리뷰 본문 (500자)
    submitted_at: datetime
    comments_count: int           # 인라인 코멘트 수


class ComprehensiveGitHubProfile(BaseModel):
    """GitHub 종합 분석 프로필 (4-Channel 통합)"""
    username: str
    analysis_period_years: int    # GITHUB_ANALYSIS_YEARS 환경변수

    # Channel A: 본인 레포 (diff 기반)
    own_repos: list["RepositoryAnalysis"]

    # Channel B: 오픈소스 PR 기여
    oss_contributions: list[OSSContribution]

    # Channel C: 이슈 참여
    issue_participations: list[IssueParticipation]

    # Channel D: 코드 리뷰 활동
    code_reviews: list[CodeReviewActivity]

    # 통계 요약
    stats: "GitHubStats"


class GitHubStats(BaseModel):
    """GitHub 활동 통계 요약"""
    # Channel A
    own_repos_count: int
    own_commits_count: int
    own_additions: int
    own_deletions: int

    # Channel B
    oss_prs_merged: int
    oss_repos_contributed: int

    # Channel C
    issues_authored: int
    issues_commented: int

    # Channel D
    reviews_given: int
    reviews_approved: int
    reviews_changes_requested: int

    # 토큰 사용량 추정
    estimated_tokens: int

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

    # 후보자 기여도 (PyDriller - diff 기반)
    candidate_contribution: CandidateContribution

    # diff 기반 코드 추출 (토큰 효율적)
    commit_diffs: list[CommitDiff]  # source_code 대신 diff만 저장

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
    """기술 용어 설명 (비개발자 친화)"""
    term: str                       # "Strangler Fig Pattern"
    definition: str                 # 전문 정의
    plain_language_explanation: str  # 비개발자용 쉬운 설명
    # 예: "오래된 시스템을 한번에 바꾸지 않고, 새 시스템을 옆에 만들면서 조금씩 옮겨가는 방법"
    context: str                    # 이 질문에서 왜 이 용어가 등장하는지
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
    """예상 답변 (확장)"""
    core_answer: str                    # 불릿 포인트 핵심 답변
    example_script: str                 # 자연스러운 답변 예시

    # 핵심 키워드
    answer_keywords: list[AnswerKeyword]

    # 레벨별 기대치
    depth_expectations: dict[str, str]  # {"신입": "...", "시니어": "..."}

    # 코드 증거
    code_evidence: list[CodeEvidence]
    key_points: list[str]
```

### 4.3 Question Category & Supporting Models
```python
from enum import Enum

class QuestionCategory(str, Enum):
    """질문 카테고리"""
    ROLE_FIT = "role_fit"
    TECHNICAL_DEPTH = "technical_depth"
    EXECUTION_OWNERSHIP = "execution_ownership"
    COMMUNICATION = "communication"
    RISK_FLAGS = "risk_flags"

class AnswerKeyword(BaseModel):
    """답변에서 기대되는 핵심 키워드"""
    keyword: str                    # "Strangler Fig Pattern"
    importance: Literal["must", "good_to_have"]  # 필수 vs 언급하면 가산
    explanation: str                # 왜 이 키워드가 중요한지

class FollowUpScoring(BaseModel):
    """꼬리질문 채점 (2단계 간소화)"""
    good: str                       # 좋은 답변 시나리오
    good_score: int                 # +5 ~ +10
    poor: str                       # 부족한 답변 시나리오
    poor_score: int                 # 0 ~ -5

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

class JDCompetencyMapping(BaseModel):
    """채용공고 역량 매핑"""
    competency: str                 # "MSA 아키텍처 설계 경험"
    jd_original_text: str           # 채용공고 원문 발췌
    why_important: str              # 왜 이 역량이 이 직무에 중요한지 (쉬운 말로)
    related_questions: list[str]    # 관련 질문 ID 리스트 ["q2", "q3", "q7"]
    assessment_weight: float        # 이 역량의 중요도 (0.0 ~ 1.0)
```

### 4.4 Interview Question (면접 질문)
```python
class InterviewerNote(BaseModel):
    """면접관 노트 (비기술 면접관용 가이드)"""
    business_interpretation: str    # 이 질문이 비즈니스적으로 무엇을 확인하는지
    daily_analogy: str              # 일상 비유로 설명
    level_expectations: dict[str, str] | None = None  # 직급별 기대 수준

class EvaluationScenarioLevel(BaseModel):
    """평가 시나리오 레벨"""
    description: str                # 이 수준의 답변 시나리오 설명
    indicators: list[str]           # 이 수준을 나타내는 구체적 지표
    score: int                      # 점수 (expert: 15-25, mid: 8-12, low: -10~5)

class EvaluationScenario(BaseModel):
    """평가 시나리오 (3단계 채점)"""
    expert: EvaluationScenarioLevel  # 🟢 우수한 답변
    mid: EvaluationScenarioLevel     # 🟡 보통 답변
    low: EvaluationScenarioLevel     # 🔴 미흡한 답변

class CodeReference(BaseModel):
    """코드 참조 정보 (확장)"""
    repo_name: str                  # "username/project-name"
    file_path: str                  # "src/services/auth.py"
    line_range: str                 # "L45-L67"
    permalink: str                  # GitHub permalink URL
    snippet: str                    # 코드 스니펫
    explanation: str                # 이 코드가 왜 중요한지
    plain_language_summary: str     # 비개발자용 설명

class InterviewQuestion(BaseModel):
    """면접 질문 (확장된 최종 모델)"""
    id: str                                 # q1, q2, ...
    sequence: int                           # 순서
    category: QuestionCategory              # role_fit | technical_depth | ...
    topic: str                              # 질문 주제
    difficulty: Difficulty                   # Easy | Medium | Hard

    # 질문 본체
    question_text: str
    context_bridge: str                     # 상황 설정 (면접관이 읽어줄 맥락)
    alternative_phrasings: list[str]        # 대체 표현

    # 면접관 가이드
    why_matters: str                        # 이 질문이 중요한 이유
    listen_for: str                         # 답변에서 들어야 할 것

    # 코드 참조 (확장)
    code_reference: CodeReference | None

    # 채점 루브릭 (3단계)
    evaluation_scenarios: EvaluationScenario

    # 꼬리질문 (답변 수준별 분기)
    follow_ups: list[FollowUpQuestion]

    # 예상 답변 (키워드 포함)
    expected_answer: ExpectedAnswer

    # 용어집
    terminology: list[TerminologyEntry]

    # 메타데이터
    language: str                           # 생성된 언어 코드 ("ko", "en" 등)
    estimated_time_minutes: int
    skills_assessed: list[str]

    # 면접관 노트 (비기술 면접관용)
    interviewer_note: InterviewerNote | None

    # 질문 생성 근거
    generation_rationale: str               # 왜 이 질문이 선택되었는지

    # JD 역량 연결
    jd_competency_link: str                 # 채용공고의 어떤 역량 요구사항과 연결되는지
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

    # 의사결정 가이드 (Decision Tab 데이터)
    decision_guide: dict[str, Any]  # 채용 추천, JD 매칭, 위험 신호 요약 등

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
    temporal_workflow_id: str       # "interview-{job_id}"
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
-- ============================================
-- 인증 테이블
-- ============================================

-- 사용자 테이블 (OAuth 로그인 시 자동 생성)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    image VARCHAR(2048),                -- OAuth 프로필 이미지 URL
    plan VARCHAR(50) NOT NULL DEFAULT 'free',  -- free, pro, enterprise
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OAuth 연결 계정 (NextAuth.js accounts 테이블)
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,             -- "google" | "github"
    provider_account_id VARCHAR(255) NOT NULL,  -- OAuth provider 고유 ID
    access_token TEXT,
    refresh_token TEXT,
    expires_at BIGINT,                          -- Unix timestamp
    token_type VARCHAR(50),
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_account_id)
);

CREATE INDEX idx_oauth_provider ON oauth_accounts(provider, provider_account_id);
CREATE INDEX idx_oauth_user ON oauth_accounts(user_id);

-- API Key 테이블 (프로그래밍 접근용)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA-256 해시 (원본 저장 금지)
    key_prefix VARCHAR(10) NOT NULL,        -- "vnt_xxxx" (식별용 접두사)
    name VARCHAR(255),                       -- 사용자가 지정한 키 이름
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- ============================================
-- 작업 테이블
-- ============================================

-- 작업 테이블 (간소화: Temporal이 SOT, PostgreSQL은 최종 결과만)
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    temporal_workflow_id VARCHAR(255) UNIQUE,  -- "interview-{job_id}" (Temporal 조회용)
    status VARCHAR(50) NOT NULL DEFAULT 'pending',

    -- 입력 데이터 (JSONB)
    input_data JSONB NOT NULL,

    -- 최종 결과만 저장 (중간 분석 결과는 Temporal이 관리)
    final_output JSONB,

    -- 웹훅 (완료 시 호출)
    callback_url VARCHAR(2048),

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_temporal ON jobs(temporal_workflow_id);
```

> **제거된 테이블:**
> - `code_embeddings`: 파이프라인에서 사용되지 않음. 코드 분석 결과는 Temporal Activity 내에서 in-memory 처리 후 LLM 컨텍스트로 전달되며, 별도 벡터 DB 저장이 필요할 경우 Phase 2에서 재설계.
> - `training_examples`: Langfuse Datasets가 프롬프트 관리 + 데이터셋 + 품질 평가를 통합 제공하므로 별도 테이블 불필요.
>
> **제거된 컬럼:**
> - `session_id`, `tenant_id`: MVP에서 불필요한 멀티테넌시. 필요 시 users 테이블에 organization 추가로 대체.
> - `analysis_result`: 중간 분석 결과는 Temporal이 관리. PostgreSQL에는 최종 결과(`final_output`)만 저장.

### 8.2 Redis Keys

> **설계 원칙**: Temporal이 워크플로우 상태의 SOT (Single Source of Truth).
> Redis는 LLM 캐싱과 Rate Limiting 전용. 상태/진행률 조회는 Temporal Query API 사용.

```
# LLM 결과 캐시 (LiteLLM Redis 캐싱)
llm_cache:{model}:{prompt_hash} -> JSON (TTL 24h)

# Rate Limiting
ratelimit:api:{user_id} -> Counter (분당 API 호출, TTL 60s)
ratelimit:github:{token_hash} -> Counter (분당 API 호출, TTL 60s)
ratelimit:llm:{api_key_hash} -> Counter (분당 토큰, TTL 60s)
```

> **제거된 키:**
> - `job:{job_id}:status`, `job:{job_id}:progress`: Temporal Query API (`get_progress`)로 대체. 삼중 저장소 문제 해소.
> - `job:{job_id}:input`, `job:{job_id}:*_analysis`: Temporal이 Activity 결과를 Event History에 보관.
> - `checkpoint:{job_id}:*`: Temporal 내장 복구(Event History replay)로 대체. 수동 재시작은 Temporal Signal로 구현.
> - `session:{session_id}:recent_jobs`: session_id 개념 제거됨.

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
└── outputs/
    └── {job_id}/
        ├── interview_script.json
        ├── interview_script_ko.pdf
        └── interview_script_en.pdf
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

# GitHub 분석 관련 환경변수 (config.py에서 정의)
# GITHUB_ANALYSIS_YEARS: int = 1  # 분석 기간 (기본 1년, 최대 3년 권장)
# GITHUB_TOKEN: str              # GitHub API 토큰 (5000 req/hour)

# 경험 레벨
ExperienceLevel: TypeAlias = Literal["신입", "주니어", "미들", "시니어", "CTO/VP"]

# 질문 난이도
Difficulty: TypeAlias = Literal["Easy", "Medium", "Hard"]

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
