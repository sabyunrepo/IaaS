# Phase 1: Domain Layer

> 원본 설계서: `plan/2026-02-15-v5-final-design.md`
> Linear 티켓: JIT-86 ~ JIT-91, JIT-124

## Linear 티켓 매핑

| 티켓 | 제목 | 참조 섹션 |
|------|------|----------|
| JIT-86 | Identity Resolution 모델 (MailmapEntry, IdentityCluster, BlameLineAttribution, PureContribution) | §7.3 |
| JIT-87 | Mailmap Builder (동적 .mailmap 생성: noreply + Levenshtein + domain) | §7.2 Step 2 |
| JIT-88 | Blame Filter (blame 라인 필터링, identity_cluster 기반) | §7.2 Step 3 |
| JIT-89 | Semantic Pruner 규칙 (AST 노이즈 제거: import, 주석, config, generated) | §7.2 Step 3 Level 2 |
| JIT-90 | Funnel Selection 규칙 (3단계 퍼널: Hard Filter + Relevance Score + Vector) | §8.2, §8.3 |
| JIT-91 | Scoring Calculator (4대 지표 가중 합산, 기존 scoring_formulas.py 재작성) | §11.1, §11.2, §11.3 |
| **JIT-124** | **LinkedIn 프로필 도메인 모델 (경력/스킬/학력/자격증 구조화)** | **§7.4 (신규)** |

---

## §7. Identity Resolution Pipeline

review1.md 2.1에서 지적된 **사용자 식별 및 기여분 추출** 결함을 해결하는 핵심 모듈이다.

### 7.1 문제점 (AS-IS)

- 단순 `git clone` -> `git blame`으로 전체 분석
- 지원자의 여러 이메일(개인/회사/학교), 닉네임 변경, 다른 컴퓨터 커밋 미고려
- 공백 수정, 파일 이동, 리팩토링까지 '기여'로 잡힘 -> 거품 섞인 분석

### 7.2 해결: 3단계 Identity Resolution

#### Step 1: GitHub Node ID 기반 추적

이메일이 바뀌어도 변하지 않는 GitHub 고유 ID(`databaseId`)를 GraphQL로 조회하여 유저를 특정한다.

```python
# infrastructure/github/graphql_client.py
async def get_user_node_id(username: str) -> str:
    """GitHub 고유 ID 조회 -- 이메일 변경에도 불변"""
    query = """
    query($login: String!) {
        user(login: $login) {
            databaseId
            email
            name
            contributionsCollection {
                commitContributionsByRepository {
                    repository { nameWithOwner }
                    contributions { totalCount }
                }
            }
        }
    }
    """
    result = await gql_client.execute(query, {"login": username})
    return str(result["user"]["databaseId"])
```

#### Step 2: 동적 `.mailmap` 생성

레포지토리 내 커밋 히스토리에서 이름/이메일 유사도를 분석하여, 동일인으로 추정되는 커밋을 하나로 묶는 클러스터링을 수행한다.

```python
# domain/identity/mailmap_builder.py
def build_dynamic_mailmap(
    git_authors: list[GitAuthor],
    github_profile: GitHubProfile,
    github_node_id: str,
    threshold: float = 0.75,
) -> list[MailmapEntry]:
    """동적 .mailmap 생성 -- 동일인 이메일 클러스터링"""
    entries = []

    # 1. noreply email 패턴 매칭 (확정적)
    # 예: 12345+username@users.noreply.github.com
    for author in git_authors:
        if "noreply.github.com" in author.email:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="high",
            ))

    # 2. GitHub profile name/email 교차 매칭 (확정적)
    for author in git_authors:
        if author.email == github_profile.email:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="high",
            ))

    # 3. 이름 Levenshtein distance < threshold -> 클러스터링 (휴리스틱)
    for author in git_authors:
        similarity = 1 - (levenshtein(author.name, github_profile.name)
                         / max(len(author.name), len(github_profile.name)))
        if similarity >= threshold:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="medium",
            ))

    # 4. 동일 커스텀 도메인 이메일 -> 후보 추가 (약한 신호)
    profile_domain = github_profile.email.split("@")[-1]
    for author in git_authors:
        if author.email.split("@")[-1] == profile_domain:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="low",
            ))

    return deduplicate(entries)
```

#### Step 3: 3단계 포렌식 쿼리

```
Level 1 (Git Internal):
  git blame -w -M -C -C --line-porcelain
  -> 공백(-w), 파일 이동(-M), 코드 복사(-C) 제외한 순수 로직 작성분만 추출

Level 2 (Semantic Pruning):
  Tree-sitter AST 파싱 ->
  import 구문, 주석, Config 설정, 자동 생성 코드(Generated Code) 제거 ->
  함수/클래스 본문만 보존

Level 3 (Authenticity Check):
  Vibector(WPM) + CLAVE(스타일로메트리) + Datasketch(표절) 교차 검증
```

### 7.3 Domain 모델

```python
# domain/identity/models.py
from pydantic import BaseModel

class MailmapEntry(BaseModel):
    canonical: str             # 정규 이름
    canonical_email: str       # 정규 이메일
    alias_name: str            # 별칭 이름
    alias_email: str           # 별칭 이메일
    confidence: str            # "high" | "medium" | "low"

class IdentityCluster(BaseModel):
    github_node_id: str
    canonical_name: str
    canonical_email: str
    aliases: list[MailmapEntry]
    total_commits: int
    verified_commits: int

class BlameLineAttribution(BaseModel):
    file_path: str
    line_number: int
    content: str
    author_name: str
    author_email: str
    commit_sha: str
    is_move: bool              # -M 감지
    is_copy: bool              # -C 감지
    is_whitespace_only: bool   # -w 감지

class PureContribution(BaseModel):
    file_path: str
    language: str
    total_lines: int           # 전체 blame 라인
    pure_logic_lines: int      # 노이즈 제거 후 순수 로직
    removed_imports: int
    removed_comments: int
    removed_config: int
    removed_generated: int
    function_bodies: list[str] # 보존된 함수/클래스 본문
```

---

## §7.4 LinkedIn 프로필 도메인 모델 (JIT-124)

LinkedIn 프로필 데이터를 구조화하는 순수 도메인 모델이다. BrightData API 호출은 Infrastructure 레이어(JIT-125)에서 담당하며, 여기서는 **파싱된 데이터의 구조화**만 책임진다.

### 모델 정의

```python
# domain/identity/linkedin_models.py
from pydantic import BaseModel, Field, ConfigDict

class LinkedInExperience(BaseModel):
    model_config = ConfigDict(strict=True)

    company: str
    title: str
    duration_months: int = Field(ge=0)
    start_date: str | None = None       # "YYYY-MM" 형식
    end_date: str | None = None         # None = 현재 재직
    description: str = ""
    location: str | None = None
    is_current: bool = False

class LinkedInEducation(BaseModel):
    model_config = ConfigDict(strict=True)

    school: str
    degree: str | None = None           # "학사", "석사" 등
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None

class LinkedInSkill(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    endorsement_count: int = Field(ge=0, default=0)

class LinkedInCertification(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    issuer: str
    issue_date: str | None = None       # "YYYY-MM"
    credential_url: str | None = None

class LinkedInProfile(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    headline: str | None = None          # "Senior Backend Engineer at ..."
    location: str | None = None
    summary: str = ""
    profile_url: str

    experiences: list[LinkedInExperience] = []
    educations: list[LinkedInEducation] = []
    skills: list[LinkedInSkill] = []
    certifications: list[LinkedInCertification] = []

    @property
    def total_experience_months(self) -> int:
        return sum(e.duration_months for e in self.experiences)

    @property
    def current_company(self) -> str | None:
        current = [e for e in self.experiences if e.is_current]
        return current[0].company if current else None
```

### 프로필 정규화 함수

```python
# domain/identity/linkedin_normalizer.py
def normalize_linkedin_profile(raw_data: dict) -> LinkedInProfile:
    """BrightData에서 수집한 raw JSON/HTML → 구조화 모델 변환"""
    experiences = [
        LinkedInExperience(
            company=exp.get("company", ""),
            title=exp.get("title", ""),
            duration_months=_calc_duration(exp.get("start"), exp.get("end")),
            start_date=exp.get("start"),
            end_date=exp.get("end"),
            description=exp.get("description", ""),
            is_current=exp.get("end") is None,
        )
        for exp in raw_data.get("experiences", [])
    ]
    # ... educations, skills, certifications 동일 패턴
    return LinkedInProfile(
        name=raw_data["name"],
        headline=raw_data.get("headline"),
        profile_url=raw_data["url"],
        experiences=experiences,
        # ...
    )
```

### 테스트 케이스

- `test_linkedin_profile_creation` — 전체 필드 모델 생성
- `test_total_experience_months` — 경력 월수 합산
- `test_current_company` — 현재 재직 회사 추출
- `test_empty_profile` — 경력/스킬 없는 프로필
- `test_normalize_raw_data` — raw dict → LinkedInProfile 변환

---

## §8. JD 기반 Funnel Selection

review1.md 2.2에서 지적된 **모든 레포 분석 = 토큰 낭비** 문제를 해결한다.

### 8.1 문제점 (AS-IS)

- 백엔드 지원자의 3년 전 React 토이 프로젝트, 알고리즘 문제 풀이 레포까지 심층 분석
- LLM 토큰 + 분석 시간 낭비
- "질문은 JD 기반"이라는 원칙과 모순

### 8.2 해결: 3단계 Funnel Architecture

```
전체 레포 목록 (GraphQL 수집)
        |
        v Stage 1: Hard Filter
[Fork, 크기, 최근 push 날짜, 유저 기여도 필터]
        |
        v Stage 2: Relevance Scoring
[JD tech_stack + requirements 기반 LLM 스코어링]
        |
        v Stage 3: Vector Similarity
[JD 텍스트 <-> README/Description 벡터 유사도]
        |
        v 상위 3-5개 프로젝트만 심층 분석
```

### 8.3 Domain 규칙

```python
# domain/matching/funnel_rules.py

class FunnelConfig(BaseModel):
    min_push_days: int = 365     # 최근 1년 내 push
    min_stars: int = 0
    max_repos: int = 20          # GraphQL 수집 상한
    top_k: int = 5               # 최종 선별 개수
    org_contribution_threshold: float = 0.10  # Org 레포 기여도 최소 10%
    vector_similarity_min: float = 0.60       # 벡터 유사도 최소

def stage1_hard_filter(
    repos: list[RepoMetadata],
    jd_languages: list[str],
    config: FunnelConfig,
) -> list[RepoMetadata]:
    """Stage 1: 메타데이터 기반 하드 필터"""
    filtered = []
    for repo in repos:
        # Fork 제외
        if repo.is_fork:
            continue
        # 최근 push 날짜 확인
        if repo.days_since_push > config.min_push_days:
            continue
        # Org 레포: 기여도 임계치 확인
        if repo.is_org_repo and repo.user_contribution_ratio < config.org_contribution_threshold:
            continue
        # 언어 교집합 확인 (JD에서 요구하는 언어가 레포에 있는지)
        if jd_languages and not set(repo.languages).intersection(set(jd_languages)):
            continue
        filtered.append(repo)
    return filtered

def stage2_relevance_score(
    repos: list[RepoMetadata],
    jd_requirements: list[str],
    jd_tech_stack: list[str],
) -> list[tuple[RepoMetadata, float]]:
    """Stage 2: JD 기반 적합성 스코어링"""
    scored = []
    for repo in repos:
        score = 0.0
        # tech_stack 매칭 (LLM 분석 결과 활용)
        matched_techs = set(repo.detected_tech_stack).intersection(set(jd_tech_stack))
        score += len(matched_techs) * 0.3
        # 최근 활동 가산
        if repo.days_since_push < 90:
            score += 0.2
        # 코드 규모 가산 (너무 작은 레포 감점)
        if repo.total_loc > 500:
            score += 0.1
        scored.append((repo, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)

def stage3_should_include(
    similarity: float,
    config: FunnelConfig,
) -> bool:
    """Stage 3: 벡터 유사도 임계값 판정"""
    return similarity >= config.vector_similarity_min
```

---

## §11. 4대 핵심 지표 체계

### 11.1 점수 산출 공식

```
최종 점수 = 0.30 x 논리력 + 0.30 x 전문성 + 0.20 x 안정성 + 0.20 x 진정성
```

### 11.2 각 지표 세부 구성

| 주지표 | 세부 지표 | 산출 도구 | 내부 가중치 | Worker |
|--------|----------|----------|------------|--------|
| **논리력 (30%)** | | | | |
| | 순환 복잡도 (CC) | Radon/Lizard | 40% | W7 |
| | 할스테드 난이도 (D) | Radon | 30% | W7 |
| | 인지적 복잡도 | SonarQube | 30% | W8 |
| **전문성 (30%)** | | | | |
| | API 활용 깊이 | AST 분석 | 35% | W10 |
| | 디자인 패턴 사용 | AST 패턴 감지 | 25% | W11 |
| | SOLID 준수율 | 아키텍처 분석 | 20% | W11 |
| | 기술스택 다양성 | 스킬 추출 | 20% | W9 |
| **안정성 (20%)** | | | | |
| | 기술 부채 비율 | SonarQube | 35% | W8 |
| | 코드 스멜 밀도 | SonarQube | 25% | W8 |
| | 리워크 비율 (Churn) | PyDriller | 20% | W7 |
| | 보안 취약점 밀도 | SonarQube + Bandit | 20% | W8 |
| **진정성 (20%)** | | | | |
| | 인간 타이핑 속도 (WPM) | Vibector | 30% | W3 |
| | 순수 기여도 | Blame + AST Pruning | 30% | W2 |
| | 표절/복사 비율 | Datasketch (LSH) | 20% | W5 |
| | 스타일 일관성 | CLAVE | 20% | W4 |

### 11.3 점수 산출 수학적 모델

```python
# domain/scoring/calculator.py

# 논리력: 복잡도가 낮을수록 고득점
Score_logic = 1 / (1 + a * M_avg + b * D_avg) * 100

# 전문성: API 활용 깊이 가중치 합산
Score_mastery = Sum(Count_API * Weight_Level)

# 안정성: 부채와 Churn이 낮을수록 고득점
Score_stability = max(0, 100 - (tech_debt_ratio * 40 + churn_ratio * 30 + smell_density * 30))

# 진정성: 순수 기여 비율
Index_authenticity = (LoC_total - LoC_AI - LoC_copy) / LoC_total * 100
```

### 11.4 신뢰도 표시 체계

| 신뢰도 | 조건 | 표시 |
|--------|------|------|
| 높음 (Green) | 데이터 소스 3개 이상 + 공개 레포 5개 이상 | 초록색 |
| 중간 (Yellow) | 데이터 소스 2개 + 공개 레포 2-4개 | 노란색 |
| 낮음 (Red) | 데이터 소스 1개 또는 공개 레포 1개 이하 | 빨간색 |

---

## §12.1 Pydantic 모델 (구조화 출력)

> **extra.md 반영:** Pydantic v2에서는 `class Config` 대신 `model_config = ConfigDict(strict=True)`를 사용한다.

```python
# domain/analysis/models.py
from pydantic import BaseModel, Field, ConfigDict

class ComplexityMetrics(BaseModel):
    model_config = ConfigDict(strict=True)  # Pydantic v2

    cyclomatic_complexity: float = Field(ge=0, description="McCabe 순환 복잡도 평균")
    halstead_difficulty: float = Field(ge=0, description="Halstead 난이도")
    halstead_volume: float = Field(ge=0, description="Halstead 볼륨")
    maintainability_index: float = Field(ge=0, le=100, description="유지보수 지수")
    cognitive_complexity: float = Field(ge=0, description="인지적 복잡도")

class AuthenticityScore(BaseModel):
    model_config = ConfigDict(strict=True)

    human_typing_ratio: float = Field(ge=0, le=1)
    originality_ratio: float = Field(ge=0, le=1)
    ai_code_suspicion: float = Field(ge=0, le=1)
    plagiarism_ratio: float = Field(ge=0, le=1)
    style_consistency: float = Field(ge=0, le=1)

class SkillAssessment(BaseModel):
    model_config = ConfigDict(strict=True)

    skill_name: str
    proficiency: str  # beginner | intermediate | advanced | expert
    evidence_count: int = Field(ge=0)
    evidence_sources: list[str]  # ["github:repo1", "linkedin", "resume"]
    confidence: str  # "high" | "medium" | "low"
```

### 면접 질문 모델

```python
# domain/question/models.py
class InterviewQuestion(BaseModel):
    """Instructor로 LLM이 직접 생성하는 구조화된 면접 질문"""
    model_config = ConfigDict(strict=True)  # Pydantic v2

    question_id: str
    category: str      # technical_depth | execution_ownership | communication | role_fit | risk_flags
    strategy: str      # negative_selection | intentional_complexity | evolution
    difficulty: str    # easy | medium | hard
    question_text: str = Field(min_length=20, max_length=500)
    intent: str = Field(description="이 질문의 의도 (비개발자용)")
    code_reference: str | None = Field(description="관련 코드 파일:라인")
    expected_answer_guide: str = Field(description="비개발자도 이해 가능한 예상 답변 가이드")
    red_flags: list[str] = Field(description="주의해야 할 답변 패턴")
    follow_up_triggers: list[str] = Field(description="파생 질문 트리거 조건")
    terminology: list[dict] = Field(description="질문에 포함된 전문 용어 설명")
```
