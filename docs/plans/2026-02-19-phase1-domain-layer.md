# Phase 1: Domain Layer 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** v5.0 DDD 도메인 레이어 — Identity Resolution, LinkedIn Profile, Funnel Selection, Scoring Calculator, Question Models를 순수 Python + Pydantic v2로 구현한다.

**Architecture:** Domain 레이어는 외부 의존성 0. Pydantic v2 (`model_config = ConfigDict(strict=True)`) 모델 + 순수 비즈니스 로직만 포함. Infrastructure에서 사용할 Port 인터페이스(Protocol)를 정의하되 구현하지 않는다.

**Tech Stack:** Python 3.11, Pydantic v2, python-Levenshtein (mailmap용), pytest

**Linear 티켓:** JIT-236 ~ JIT-242 (7개)

**설계 참조:**
- `plan/v5-design/phase1-domain.md` — Phase 1 상세 설계
- Obsidian vault `domain/` — 각 서브도메인 MOC + 컴포넌트 문서

---

## 의존성 그래프

```
Task 1 (JIT-236) ─┬── Task 3 (JIT-237) ── Task 4 (JIT-238)
                   │
                   └── Task 5 (JIT-239)
Task 2 (JIT-241) ─── 독립
Task 6 (JIT-240) ─── 독립 (RepoMetadata 모델 자체 정의)
Task 7 (JIT-242) ─── Task 1 결과 사용
```

---

## Task 1: Identity Resolution 도메인 모델 [JIT-236]

**Files:**
- Create: `jittda/backend/src/domain/identity/models.py`
- Create: `jittda/backend/src/domain/identity/ports.py`
- Modify: `jittda/backend/src/domain/identity/__init__.py`
- Test: `jittda/backend/tests/domain/test_identity_models.py`

**설계 참조:** Obsidian `domain/identity-resolution/models.md`

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_identity_models.py
"""Identity Resolution 도메인 모델 테스트."""
import pytest
from domain.identity.models import (
    MailmapEntry,
    IdentityCluster,
    BlameLineAttribution,
    PureContribution,
    GitAuthor,
    GitHubProfile,
    ConfidenceLevel,
)


class TestMailmapEntry:
    def test_create_high_confidence(self):
        entry = MailmapEntry(
            canonical="Kim Sabyun",
            canonical_email="sabyun@jittda.com",
            alias_name="sabyun-work",
            alias_email="sabyun@company.com",
            confidence=ConfidenceLevel.HIGH,
        )
        assert entry.canonical == "Kim Sabyun"
        assert entry.confidence == ConfidenceLevel.HIGH

    def test_confidence_levels(self):
        for level in ConfidenceLevel:
            entry = MailmapEntry(
                canonical="Test",
                canonical_email="test@test.com",
                alias_name="Test",
                alias_email="test@alias.com",
                confidence=level,
            )
            assert entry.confidence == level


class TestIdentityCluster:
    def test_create_cluster(self):
        alias = MailmapEntry(
            canonical="Kim Sabyun",
            canonical_email="sabyun@jittda.com",
            alias_name="sabyun-noreply",
            alias_email="12345+sabyun@users.noreply.github.com",
            confidence=ConfidenceLevel.HIGH,
        )
        cluster = IdentityCluster(
            github_node_id="MDQ6VXNlcjEyMzQ1",
            canonical_name="Kim Sabyun",
            canonical_email="sabyun@jittda.com",
            aliases=[alias],
            total_commits=150,
            verified_commits=130,
        )
        assert cluster.github_node_id == "MDQ6VXNlcjEyMzQ1"
        assert len(cluster.aliases) == 1
        assert cluster.verification_ratio == pytest.approx(130 / 150)

    def test_empty_aliases(self):
        cluster = IdentityCluster(
            github_node_id="123",
            canonical_name="Test",
            canonical_email="t@t.com",
            aliases=[],
            total_commits=0,
            verified_commits=0,
        )
        assert cluster.verification_ratio == 0.0


class TestBlameLineAttribution:
    def test_create_blame_line(self):
        line = BlameLineAttribution(
            file_path="src/main.py",
            line_number=42,
            content="def calculate(): ...",
            author_name="Kim Sabyun",
            author_email="sabyun@jittda.com",
            commit_sha="abc123def",
            is_move=False,
            is_copy=False,
            is_whitespace_only=False,
        )
        assert line.is_meaningful_contribution is True

    def test_whitespace_only_not_meaningful(self):
        line = BlameLineAttribution(
            file_path="src/main.py",
            line_number=1,
            content="   ",
            author_name="Test",
            author_email="t@t.com",
            commit_sha="abc",
            is_move=False,
            is_copy=False,
            is_whitespace_only=True,
        )
        assert line.is_meaningful_contribution is False

    def test_move_not_meaningful(self):
        line = BlameLineAttribution(
            file_path="src/main.py",
            line_number=1,
            content="def foo(): ...",
            author_name="Test",
            author_email="t@t.com",
            commit_sha="abc",
            is_move=True,
            is_copy=False,
            is_whitespace_only=False,
        )
        assert line.is_meaningful_contribution is False


class TestPureContribution:
    def test_create_pure_contribution(self):
        pc = PureContribution(
            file_path="src/calculator.py",
            language="python",
            total_lines=200,
            pure_logic_lines=120,
            removed_imports=30,
            removed_comments=25,
            removed_config=15,
            removed_generated=10,
            function_bodies=["def calculate(x, y): ...", "def validate(data): ..."],
        )
        assert pc.purity_ratio == pytest.approx(120 / 200)
        assert pc.noise_lines == 80

    def test_zero_total_lines(self):
        pc = PureContribution(
            file_path="empty.py",
            language="python",
            total_lines=0,
            pure_logic_lines=0,
            removed_imports=0,
            removed_comments=0,
            removed_config=0,
            removed_generated=0,
            function_bodies=[],
        )
        assert pc.purity_ratio == 0.0


class TestGitAuthor:
    def test_create(self):
        author = GitAuthor(name="Kim Sabyun", email="sabyun@jittda.com")
        assert author.name == "Kim Sabyun"


class TestGitHubProfile:
    def test_create(self):
        profile = GitHubProfile(
            name="Kim Sabyun",
            email="sabyun@jittda.com",
            login="sabyun",
            database_id="12345",
        )
        assert profile.login == "sabyun"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && python -m pytest tests/domain/test_identity_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'domain.identity.models'`

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/identity/models.py
"""Identity Resolution 도메인 모델.

Git 커밋 작성자 식별 + 순수 기여분 추출을 위한 모델 정의.
설계 참조: Obsidian domain/identity-resolution/models.md
"""
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GitAuthor(BaseModel):
    """Git 커밋 히스토리에서 추출한 author 정보."""
    model_config = ConfigDict(frozen=True)

    name: str
    email: str


class GitHubProfile(BaseModel):
    """GitHub GraphQL API에서 조회한 프로필 정보."""
    model_config = ConfigDict(frozen=True)

    name: str
    email: str
    login: str
    database_id: str


class MailmapEntry(BaseModel):
    """동적 .mailmap 엔트리 — 동일인의 이메일/이름 매핑."""
    model_config = ConfigDict(frozen=True)

    canonical: str
    canonical_email: str
    alias_name: str
    alias_email: str
    confidence: ConfidenceLevel


class IdentityCluster(BaseModel):
    """동일인으로 확인된 Git author 클러스터."""
    model_config = ConfigDict(strict=True)

    github_node_id: str
    canonical_name: str
    canonical_email: str
    aliases: list[MailmapEntry]
    total_commits: int = Field(ge=0)
    verified_commits: int = Field(ge=0)

    @property
    def verification_ratio(self) -> float:
        if self.total_commits == 0:
            return 0.0
        return self.verified_commits / self.total_commits


class BlameLineAttribution(BaseModel):
    """git blame 결과의 단일 라인 귀속 정보."""
    model_config = ConfigDict(strict=True)

    file_path: str
    line_number: int = Field(ge=1)
    content: str
    author_name: str
    author_email: str
    commit_sha: str
    is_move: bool
    is_copy: bool
    is_whitespace_only: bool

    @property
    def is_meaningful_contribution(self) -> bool:
        return not (self.is_move or self.is_copy or self.is_whitespace_only)


class PureContribution(BaseModel):
    """노이즈 제거 후 순수 코드 기여분."""
    model_config = ConfigDict(strict=True)

    file_path: str
    language: str
    total_lines: int = Field(ge=0)
    pure_logic_lines: int = Field(ge=0)
    removed_imports: int = Field(ge=0)
    removed_comments: int = Field(ge=0)
    removed_config: int = Field(ge=0)
    removed_generated: int = Field(ge=0)
    function_bodies: list[str]

    @property
    def purity_ratio(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.pure_logic_lines / self.total_lines

    @property
    def noise_lines(self) -> int:
        return self.removed_imports + self.removed_comments + self.removed_config + self.removed_generated
```

```python
# jittda/backend/src/domain/identity/ports.py
"""Identity Resolution Port 인터페이스.

Infrastructure 레이어에서 구현할 어댑터 계약.
"""
from typing import Protocol

from domain.identity.models import GitAuthor, GitHubProfile


class GitAuthorReader(Protocol):
    """Git 저장소에서 author 목록을 읽는 포트."""
    async def list_authors(self, repo_path: str) -> list[GitAuthor]: ...


class GitHubProfileFetcher(Protocol):
    """GitHub API에서 프로필을 조회하는 포트."""
    async def fetch_profile(self, username: str) -> GitHubProfile: ...
    async def get_node_id(self, username: str) -> str: ...
```

```python
# jittda/backend/src/domain/identity/__init__.py
"""Identity Resolution 도메인."""
from domain.identity.models import (
    BlameLineAttribution,
    ConfidenceLevel,
    GitAuthor,
    GitHubProfile,
    IdentityCluster,
    MailmapEntry,
    PureContribution,
)

__all__ = [
    "BlameLineAttribution",
    "ConfidenceLevel",
    "GitAuthor",
    "GitHubProfile",
    "IdentityCluster",
    "MailmapEntry",
    "PureContribution",
]
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_identity_models.py -v`
Expected: ALL PASS (13 tests)

**Step 5: Commit**

```bash
but branch new feat/JIT-236-identity-models
but commit -m "feat: Identity Resolution 도메인 모델 구현 [JIT-236]" feat/JIT-236-identity-models
```

---

## Task 2: LinkedIn 프로필 도메인 모델 [JIT-241]

**Files:**
- Create: `jittda/backend/src/domain/identity/linkedin_models.py`
- Create: `jittda/backend/src/domain/identity/linkedin_normalizer.py`
- Modify: `jittda/backend/src/domain/identity/__init__.py`
- Test: `jittda/backend/tests/domain/test_linkedin_models.py`

**설계 참조:** Obsidian `domain/linkedin-profile/profile-model.md`, `plan/v5-design/phase1-domain.md` §7.4

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_linkedin_models.py
"""LinkedIn 프로필 도메인 모델 테스트."""
import pytest
from domain.identity.linkedin_models import (
    LinkedInCertification,
    LinkedInEducation,
    LinkedInExperience,
    LinkedInProfile,
    LinkedInSkill,
)
from domain.identity.linkedin_normalizer import normalize_linkedin_profile


class TestLinkedInExperience:
    def test_create(self):
        exp = LinkedInExperience(
            company="Jittda",
            title="Backend Engineer",
            duration_months=24,
            start_date="2024-02",
            end_date=None,
            is_current=True,
        )
        assert exp.company == "Jittda"
        assert exp.is_current is True

    def test_duration_months_non_negative(self):
        with pytest.raises(Exception):
            LinkedInExperience(
                company="X", title="Y", duration_months=-1,
            )


class TestLinkedInProfile:
    def test_full_profile(self):
        profile = LinkedInProfile(
            name="Kim Sabyun",
            headline="Senior Backend Engineer at Jittda",
            location="Seoul, Korea",
            summary="Experienced engineer",
            profile_url="https://linkedin.com/in/sabyun",
            experiences=[
                LinkedInExperience(
                    company="Jittda", title="Senior BE", duration_months=24,
                    is_current=True,
                ),
                LinkedInExperience(
                    company="Previous", title="BE", duration_months=18,
                ),
            ],
            skills=[
                LinkedInSkill(name="Python", endorsement_count=50),
                LinkedInSkill(name="FastAPI", endorsement_count=30),
            ],
            educations=[
                LinkedInEducation(school="Seoul Univ", degree="학사", field_of_study="CS"),
            ],
            certifications=[
                LinkedInCertification(name="AWS SAA", issuer="Amazon"),
            ],
        )
        assert profile.total_experience_months == 42
        assert profile.current_company == "Jittda"
        assert len(profile.skills) == 2

    def test_empty_profile(self):
        profile = LinkedInProfile(
            name="Empty",
            profile_url="https://linkedin.com/in/empty",
        )
        assert profile.total_experience_months == 0
        assert profile.current_company is None
        assert profile.experiences == []

    def test_no_current_company(self):
        profile = LinkedInProfile(
            name="Past",
            profile_url="https://linkedin.com/in/past",
            experiences=[
                LinkedInExperience(
                    company="OldCo", title="Dev", duration_months=12,
                    is_current=False, end_date="2023-12",
                ),
            ],
        )
        assert profile.current_company is None


class TestNormalizeLinkedInProfile:
    def test_normalize_full_data(self):
        raw = {
            "name": "Kim Sabyun",
            "headline": "Engineer",
            "url": "https://linkedin.com/in/sabyun",
            "location": "Seoul",
            "summary": "Summary text",
            "experiences": [
                {
                    "company": "Jittda",
                    "title": "Backend Engineer",
                    "start": "2024-02",
                    "end": None,
                    "description": "Building AI tools",
                    "location": "Seoul",
                },
            ],
            "educations": [
                {"school": "Seoul Univ", "degree": "학사", "field_of_study": "CS"},
            ],
            "skills": [
                {"name": "Python", "endorsement_count": 50},
            ],
            "certifications": [
                {"name": "AWS", "issuer": "Amazon", "issue_date": "2024-01"},
            ],
        }
        profile = normalize_linkedin_profile(raw)
        assert profile.name == "Kim Sabyun"
        assert len(profile.experiences) == 1
        assert profile.experiences[0].is_current is True
        assert profile.experiences[0].duration_months > 0

    def test_normalize_minimal_data(self):
        raw = {"name": "Min", "url": "https://linkedin.com/in/min"}
        profile = normalize_linkedin_profile(raw)
        assert profile.name == "Min"
        assert profile.experiences == []

    def test_normalize_duration_calculation(self):
        raw = {
            "name": "Test",
            "url": "https://linkedin.com/in/test",
            "experiences": [
                {"company": "A", "title": "Dev", "start": "2024-01", "end": "2025-01"},
            ],
        }
        profile = normalize_linkedin_profile(raw)
        assert profile.experiences[0].duration_months == 12
        assert profile.experiences[0].is_current is False
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_linkedin_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/identity/linkedin_models.py
"""LinkedIn 프로필 도메인 모델.

BrightData에서 수집한 LinkedIn 데이터의 구조화 모델.
설계 참조: Obsidian domain/linkedin-profile/profile-model.md
"""
from pydantic import BaseModel, ConfigDict, Field


class LinkedInExperience(BaseModel):
    model_config = ConfigDict(strict=True)

    company: str
    title: str
    duration_months: int = Field(ge=0)
    start_date: str | None = None
    end_date: str | None = None
    description: str = ""
    location: str | None = None
    is_current: bool = False


class LinkedInEducation(BaseModel):
    model_config = ConfigDict(strict=True)

    school: str
    degree: str | None = None
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
    issue_date: str | None = None
    credential_url: str | None = None


class LinkedInProfile(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    headline: str | None = None
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

```python
# jittda/backend/src/domain/identity/linkedin_normalizer.py
"""LinkedIn 프로필 정규화.

BrightData raw JSON → LinkedInProfile 구조화 변환.
"""
from datetime import date

from domain.identity.linkedin_models import (
    LinkedInCertification,
    LinkedInEducation,
    LinkedInExperience,
    LinkedInProfile,
    LinkedInSkill,
)


def _calc_duration(start: str | None, end: str | None) -> int:
    """YYYY-MM 형식의 시작/종료일로 개월 수 계산."""
    if not start:
        return 0
    try:
        s_year, s_month = map(int, start.split("-"))
        if end:
            e_year, e_month = map(int, end.split("-"))
        else:
            today = date.today()
            e_year, e_month = today.year, today.month
        return max(0, (e_year - s_year) * 12 + (e_month - s_month))
    except (ValueError, AttributeError):
        return 0


def normalize_linkedin_profile(raw_data: dict) -> LinkedInProfile:
    """BrightData raw JSON → LinkedInProfile 변환."""
    experiences = [
        LinkedInExperience(
            company=exp.get("company", ""),
            title=exp.get("title", ""),
            duration_months=_calc_duration(exp.get("start"), exp.get("end")),
            start_date=exp.get("start"),
            end_date=exp.get("end"),
            description=exp.get("description", ""),
            location=exp.get("location"),
            is_current=exp.get("end") is None and exp.get("start") is not None,
        )
        for exp in raw_data.get("experiences", [])
    ]

    educations = [
        LinkedInEducation(
            school=edu.get("school", ""),
            degree=edu.get("degree"),
            field_of_study=edu.get("field_of_study"),
            start_year=edu.get("start_year"),
            end_year=edu.get("end_year"),
        )
        for edu in raw_data.get("educations", [])
    ]

    skills = [
        LinkedInSkill(
            name=sk.get("name", ""),
            endorsement_count=sk.get("endorsement_count", 0),
        )
        for sk in raw_data.get("skills", [])
    ]

    certifications = [
        LinkedInCertification(
            name=cert.get("name", ""),
            issuer=cert.get("issuer", ""),
            issue_date=cert.get("issue_date"),
            credential_url=cert.get("credential_url"),
        )
        for cert in raw_data.get("certifications", [])
    ]

    return LinkedInProfile(
        name=raw_data["name"],
        headline=raw_data.get("headline"),
        location=raw_data.get("location"),
        summary=raw_data.get("summary", ""),
        profile_url=raw_data["url"],
        experiences=experiences,
        educations=educations,
        skills=skills,
        certifications=certifications,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_linkedin_models.py -v`
Expected: ALL PASS (8 tests)

**Step 5: Commit**

```bash
but commit -m "feat: LinkedIn 프로필 도메인 모델 + 정규화 함수 [JIT-241]" feat/JIT-236-identity-models
```

---

## Task 3: Mailmap Builder [JIT-237]

**Files:**
- Create: `jittda/backend/src/domain/identity/mailmap_builder.py`
- Test: `jittda/backend/tests/domain/test_mailmap_builder.py`

**설계 참조:** Obsidian `domain/identity-resolution/dynamic-mailmap.md`, `plan/v5-design/phase1-domain.md` §7.2 Step 2

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_mailmap_builder.py
"""Mailmap Builder 테스트 — 동적 .mailmap 생성."""
import pytest
from domain.identity.mailmap_builder import build_dynamic_mailmap, deduplicate_entries
from domain.identity.models import (
    ConfidenceLevel,
    GitAuthor,
    GitHubProfile,
    MailmapEntry,
)


@pytest.fixture
def github_profile():
    return GitHubProfile(
        name="Kim Sabyun",
        email="sabyun@jittda.com",
        login="sabyun",
        database_id="12345",
    )


class TestBuildDynamicMailmap:
    def test_noreply_email_detected(self, github_profile):
        authors = [
            GitAuthor(name="sabyun", email="12345+sabyun@users.noreply.github.com"),
        ]
        entries = build_dynamic_mailmap(authors, github_profile, "12345")
        assert len(entries) >= 1
        noreply = [e for e in entries if "noreply" in e.alias_email]
        assert noreply[0].confidence == ConfidenceLevel.HIGH

    def test_profile_email_match(self, github_profile):
        authors = [
            GitAuthor(name="Kim S", email="sabyun@jittda.com"),
        ]
        entries = build_dynamic_mailmap(authors, github_profile, "12345")
        high_entries = [e for e in entries if e.confidence == ConfidenceLevel.HIGH]
        assert len(high_entries) >= 1

    def test_levenshtein_similarity(self, github_profile):
        authors = [
            GitAuthor(name="Kim Sabyun-dev", email="sabyun.dev@gmail.com"),
        ]
        entries = build_dynamic_mailmap(authors, github_profile, "12345", threshold=0.6)
        medium_entries = [e for e in entries if e.confidence == ConfidenceLevel.MEDIUM]
        assert len(medium_entries) >= 1

    def test_domain_match(self, github_profile):
        authors = [
            GitAuthor(name="unknown", email="other@jittda.com"),
        ]
        entries = build_dynamic_mailmap(authors, github_profile, "12345")
        low_entries = [e for e in entries if e.confidence == ConfidenceLevel.LOW]
        assert len(low_entries) >= 1

    def test_no_match_returns_empty(self, github_profile):
        authors = [
            GitAuthor(name="Completely Different Person", email="stranger@other.org"),
        ]
        entries = build_dynamic_mailmap(authors, github_profile, "12345")
        assert len(entries) == 0

    def test_deduplication(self, github_profile):
        """동일한 alias_email이 여러 규칙에 매칭되면 confidence 높은 쪽만 유지."""
        authors = [
            GitAuthor(name="Kim Sabyun", email="sabyun@jittda.com"),
        ]
        # profile email match (HIGH) + domain match (LOW) 모두 매칭
        entries = build_dynamic_mailmap(authors, github_profile, "12345")
        emails = [e.alias_email for e in entries]
        assert emails.count("sabyun@jittda.com") == 1
        assert entries[0].confidence == ConfidenceLevel.HIGH


class TestDeduplicateEntries:
    def test_keeps_highest_confidence(self):
        entries = [
            MailmapEntry(
                canonical="A", canonical_email="a@a.com",
                alias_name="B", alias_email="b@b.com",
                confidence=ConfidenceLevel.LOW,
            ),
            MailmapEntry(
                canonical="A", canonical_email="a@a.com",
                alias_name="B", alias_email="b@b.com",
                confidence=ConfidenceLevel.HIGH,
            ),
        ]
        result = deduplicate_entries(entries)
        assert len(result) == 1
        assert result[0].confidence == ConfidenceLevel.HIGH
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_mailmap_builder.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/identity/mailmap_builder.py
"""동적 .mailmap 생성.

Git 커밋 히스토리에서 동일인의 이메일/이름을 클러스터링한다.
4가지 매칭 규칙: noreply 패턴, 프로필 이메일, Levenshtein, 도메인.
설계 참조: Obsidian domain/identity-resolution/dynamic-mailmap.md
"""
from Levenshtein import ratio as levenshtein_ratio

from domain.identity.models import (
    ConfidenceLevel,
    GitAuthor,
    GitHubProfile,
    MailmapEntry,
)

_CONFIDENCE_PRIORITY = {
    ConfidenceLevel.HIGH: 0,
    ConfidenceLevel.MEDIUM: 1,
    ConfidenceLevel.LOW: 2,
}


def build_dynamic_mailmap(
    git_authors: list[GitAuthor],
    github_profile: GitHubProfile,
    github_node_id: str,
    threshold: float = 0.75,
) -> list[MailmapEntry]:
    """동적 .mailmap 생성 — 동일인 이메일 클러스터링."""
    entries: list[MailmapEntry] = []

    for author in git_authors:
        # Rule 1: noreply email 패턴 (확정적)
        if "noreply.github.com" in author.email:
            entries.append(_make_entry(github_profile, author, ConfidenceLevel.HIGH))
            continue

        # Rule 2: GitHub profile email 교차 (확정적)
        if author.email == github_profile.email:
            entries.append(_make_entry(github_profile, author, ConfidenceLevel.HIGH))
            continue

        # Rule 3: 이름 Levenshtein 유사도 (휴리스틱)
        similarity = levenshtein_ratio(author.name, github_profile.name)
        if similarity >= threshold:
            entries.append(_make_entry(github_profile, author, ConfidenceLevel.MEDIUM))
            continue

        # Rule 4: 동일 도메인 이메일 (약한 신호)
        profile_domain = github_profile.email.split("@")[-1]
        author_domain = author.email.split("@")[-1]
        if (
            profile_domain == author_domain
            and profile_domain not in ("gmail.com", "hotmail.com", "yahoo.com", "outlook.com")
        ):
            entries.append(_make_entry(github_profile, author, ConfidenceLevel.LOW))

    return deduplicate_entries(entries)


def deduplicate_entries(entries: list[MailmapEntry]) -> list[MailmapEntry]:
    """동일 alias_email 중복 제거 — confidence 높은 쪽만 유지."""
    best: dict[str, MailmapEntry] = {}
    for entry in entries:
        key = entry.alias_email
        if key not in best or _CONFIDENCE_PRIORITY[entry.confidence] < _CONFIDENCE_PRIORITY[best[key].confidence]:
            best[key] = entry
    return list(best.values())


def _make_entry(profile: GitHubProfile, author: GitAuthor, confidence: ConfidenceLevel) -> MailmapEntry:
    return MailmapEntry(
        canonical=profile.name,
        canonical_email=profile.email,
        alias_name=author.name,
        alias_email=author.email,
        confidence=confidence,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_mailmap_builder.py -v`
Expected: ALL PASS (7 tests)

**Step 5: Commit**

```bash
but commit -m "feat: Mailmap Builder — 동적 .mailmap 생성 [JIT-237]" feat/JIT-236-identity-models
```

---

## Task 4: Blame Filter [JIT-238]

**Files:**
- Create: `jittda/backend/src/domain/identity/blame_filter.py`
- Test: `jittda/backend/tests/domain/test_blame_filter.py`

**설계 참조:** Obsidian `domain/identity-resolution/blame-forensics.md`

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_blame_filter.py
"""Blame Filter 테스트 — blame 라인 필터링."""
import pytest
from domain.identity.blame_filter import filter_blame_lines, aggregate_contributions
from domain.identity.models import BlameLineAttribution, IdentityCluster, MailmapEntry, ConfidenceLevel


@pytest.fixture
def cluster():
    return IdentityCluster(
        github_node_id="12345",
        canonical_name="Kim Sabyun",
        canonical_email="sabyun@jittda.com",
        aliases=[
            MailmapEntry(
                canonical="Kim Sabyun",
                canonical_email="sabyun@jittda.com",
                alias_name="sabyun-noreply",
                alias_email="12345+sabyun@users.noreply.github.com",
                confidence=ConfidenceLevel.HIGH,
            ),
        ],
        total_commits=100,
        verified_commits=90,
    )


def _make_line(email: str, move: bool = False, copy: bool = False, ws: bool = False) -> BlameLineAttribution:
    return BlameLineAttribution(
        file_path="src/main.py",
        line_number=1,
        content="def foo(): ...",
        author_name="Test",
        author_email=email,
        commit_sha="abc",
        is_move=move,
        is_copy=copy,
        is_whitespace_only=ws,
    )


class TestFilterBlameLines:
    def test_keeps_meaningful_own_lines(self, cluster):
        lines = [_make_line("sabyun@jittda.com")]
        result = filter_blame_lines(lines, cluster)
        assert len(result) == 1

    def test_filters_move_lines(self, cluster):
        lines = [_make_line("sabyun@jittda.com", move=True)]
        result = filter_blame_lines(lines, cluster)
        assert len(result) == 0

    def test_filters_copy_lines(self, cluster):
        lines = [_make_line("sabyun@jittda.com", copy=True)]
        result = filter_blame_lines(lines, cluster)
        assert len(result) == 0

    def test_filters_whitespace_lines(self, cluster):
        lines = [_make_line("sabyun@jittda.com", ws=True)]
        result = filter_blame_lines(lines, cluster)
        assert len(result) == 0

    def test_filters_other_authors(self, cluster):
        lines = [_make_line("stranger@other.com")]
        result = filter_blame_lines(lines, cluster)
        assert len(result) == 0

    def test_matches_alias_email(self, cluster):
        lines = [_make_line("12345+sabyun@users.noreply.github.com")]
        result = filter_blame_lines(lines, cluster)
        assert len(result) == 1


class TestAggregateContributions:
    def test_aggregate_by_file(self, cluster):
        lines = [
            BlameLineAttribution(
                file_path="src/a.py", line_number=i, content=f"line {i}",
                author_name="Kim", author_email="sabyun@jittda.com",
                commit_sha="abc", is_move=False, is_copy=False, is_whitespace_only=False,
            )
            for i in range(1, 11)
        ]
        contributions = aggregate_contributions(lines, "python")
        assert len(contributions) == 1
        assert contributions[0].file_path == "src/a.py"
        assert contributions[0].total_lines == 10
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_blame_filter.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/identity/blame_filter.py
"""Blame 라인 필터링.

IdentityCluster 기반으로 blame 결과에서 대상 사용자의
순수 코드 기여 라인만 추출한다.
설계 참조: Obsidian domain/identity-resolution/blame-forensics.md
"""
from collections import defaultdict

from domain.identity.models import (
    BlameLineAttribution,
    IdentityCluster,
    PureContribution,
)


def filter_blame_lines(
    lines: list[BlameLineAttribution],
    cluster: IdentityCluster,
) -> list[BlameLineAttribution]:
    """blame 라인에서 대상 사용자의 의미 있는 기여만 필터링."""
    known_emails = {cluster.canonical_email}
    for alias in cluster.aliases:
        known_emails.add(alias.alias_email)

    return [
        line for line in lines
        if line.author_email in known_emails and line.is_meaningful_contribution
    ]


def aggregate_contributions(
    lines: list[BlameLineAttribution],
    language: str,
) -> list[PureContribution]:
    """필터링된 blame 라인을 파일별로 집계."""
    by_file: dict[str, list[BlameLineAttribution]] = defaultdict(list)
    for line in lines:
        by_file[line.file_path].append(line)

    return [
        PureContribution(
            file_path=file_path,
            language=language,
            total_lines=len(file_lines),
            pure_logic_lines=len(file_lines),  # Semantic Pruner 적용 전
            removed_imports=0,
            removed_comments=0,
            removed_config=0,
            removed_generated=0,
            function_bodies=[line.content for line in file_lines],
        )
        for file_path, file_lines in by_file.items()
    ]
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_blame_filter.py -v`
Expected: ALL PASS (7 tests)

**Step 5: Commit**

```bash
but commit -m "feat: Blame Filter — blame 라인 필터링 [JIT-238]" feat/JIT-236-identity-models
```

---

## Task 5: Semantic Pruner 규칙 [JIT-239]

**Files:**
- Create: `jittda/backend/src/domain/identity/semantic_pruner.py`
- Test: `jittda/backend/tests/domain/test_semantic_pruner.py`

**설계 참조:** Obsidian `domain/identity-resolution/blame-forensics.md` Level 2

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_semantic_pruner.py
"""Semantic Pruner 테스트 — AST 노이즈 제거 규칙."""
import pytest
from domain.identity.semantic_pruner import (
    PruningCategory,
    classify_line,
    prune_contribution,
)
from domain.identity.models import PureContribution


class TestClassifyLine:
    @pytest.mark.parametrize("line,expected", [
        ("import os", PruningCategory.IMPORT),
        ("from pathlib import Path", PruningCategory.IMPORT),
        ("from . import utils", PruningCategory.IMPORT),
        ("# This is a comment", PruningCategory.COMMENT),
        ("// javascript comment", PruningCategory.COMMENT),
        ("/* block comment */", PruningCategory.COMMENT),
        ('"""docstring"""', PruningCategory.COMMENT),
        ("DEBUG = True", PruningCategory.CONFIG),
        ("DATABASE_URL = 'postgres://...'", PruningCategory.CONFIG),
        ("LOG_LEVEL = 'INFO'", PruningCategory.CONFIG),
        ("# Generated by protobuf", PruningCategory.GENERATED),
        ("# auto-generated", PruningCategory.GENERATED),
        ("# DO NOT EDIT", PruningCategory.GENERATED),
        ("def calculate(x, y):", PruningCategory.LOGIC),
        ("    return x + y", PruningCategory.LOGIC),
        ("class UserService:", PruningCategory.LOGIC),
    ])
    def test_classification(self, line, expected):
        assert classify_line(line) == expected


class TestPruneContribution:
    def test_prune_mixed_content(self):
        lines = [
            "import os",
            "from typing import List",
            "# helper function",
            "DATABASE_URL = 'postgres://...'",
            "def calculate(x, y):",
            "    return x + y",
            "class Validator:",
            "    def validate(self, data):",
            "        return len(data) > 0",
        ]
        result = prune_contribution(
            file_path="src/calc.py",
            language="python",
            lines=lines,
        )
        assert result.total_lines == 9
        assert result.removed_imports == 2
        assert result.removed_comments == 1
        assert result.removed_config == 1
        assert result.pure_logic_lines == 5
        assert result.purity_ratio == pytest.approx(5 / 9)

    def test_all_logic(self):
        lines = ["def foo():", "    return 42"]
        result = prune_contribution("f.py", "python", lines)
        assert result.pure_logic_lines == 2
        assert result.purity_ratio == 1.0

    def test_empty_file(self):
        result = prune_contribution("empty.py", "python", [])
        assert result.total_lines == 0
        assert result.purity_ratio == 0.0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_semantic_pruner.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/identity/semantic_pruner.py
"""Semantic Pruner — AST 노이즈 제거 규칙.

코드 라인을 카테고리별로 분류하여 import, 주석, 설정, 자동생성 코드를 제거하고
순수 로직 라인만 보존한다. 실제 AST 파싱은 Infrastructure (Tree-sitter)에서 수행하며,
여기서는 규칙 기반 분류 로직만 정의한다.
설계 참조: Obsidian domain/identity-resolution/blame-forensics.md Level 2
"""
import re
from enum import StrEnum

from domain.identity.models import PureContribution


class PruningCategory(StrEnum):
    IMPORT = "import"
    COMMENT = "comment"
    CONFIG = "config"
    GENERATED = "generated"
    LOGIC = "logic"


_IMPORT_PATTERNS = re.compile(
    r"^\s*(import\s|from\s.*\simport\s)"
)

_COMMENT_PATTERNS = re.compile(
    r'^\s*(#|//|/\*|\*/|\*\s|"""|\'\'\')'
)

_CONFIG_PATTERNS = re.compile(
    r"^\s*[A-Z][A-Z_0-9]*\s*=\s*"
)

_GENERATED_PATTERNS = re.compile(
    r"(?i)(generated|auto-generated|do not edit|autogenerated|this file is generated)"
)


def classify_line(line: str) -> PruningCategory:
    """코드 라인을 카테고리로 분류."""
    stripped = line.strip()
    if not stripped:
        return PruningCategory.LOGIC

    # 자동 생성 코드 (주석 내 키워드)
    if _GENERATED_PATTERNS.search(stripped):
        return PruningCategory.GENERATED

    # import 구문
    if _IMPORT_PATTERNS.match(stripped):
        return PruningCategory.IMPORT

    # 주석
    if _COMMENT_PATTERNS.match(stripped):
        return PruningCategory.COMMENT

    # 설정 상수 (ALL_CAPS = value)
    if _CONFIG_PATTERNS.match(stripped):
        return PruningCategory.CONFIG

    return PruningCategory.LOGIC


def prune_contribution(
    file_path: str,
    language: str,
    lines: list[str],
) -> PureContribution:
    """코드 라인 목록에서 노이즈를 제거하고 PureContribution 생성."""
    counts = {cat: 0 for cat in PruningCategory}
    logic_lines: list[str] = []

    for line in lines:
        category = classify_line(line)
        counts[category] += 1
        if category == PruningCategory.LOGIC:
            logic_lines.append(line)

    return PureContribution(
        file_path=file_path,
        language=language,
        total_lines=len(lines),
        pure_logic_lines=counts[PruningCategory.LOGIC],
        removed_imports=counts[PruningCategory.IMPORT],
        removed_comments=counts[PruningCategory.COMMENT],
        removed_config=counts[PruningCategory.CONFIG],
        removed_generated=counts[PruningCategory.GENERATED],
        function_bodies=logic_lines,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_semantic_pruner.py -v`
Expected: ALL PASS (19 tests — 16 parametrized + 3 prune tests)

**Step 5: Commit**

```bash
but commit -m "feat: Semantic Pruner — AST 노이즈 제거 규칙 [JIT-239]" feat/JIT-236-identity-models
```

---

## Task 6: Funnel Selection 규칙 [JIT-240]

**Files:**
- Create: `jittda/backend/src/domain/matching/models.py`
- Create: `jittda/backend/src/domain/matching/funnel_rules.py`
- Modify: `jittda/backend/src/domain/matching/__init__.py`
- Test: `jittda/backend/tests/domain/test_funnel_rules.py`

**설계 참조:** Obsidian `domain/funnel-selection/`, `plan/v5-design/phase1-domain.md` §8

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_funnel_rules.py
"""Funnel Selection 규칙 테스트 — 3단계 퍼널."""
import pytest
from domain.matching.models import FunnelConfig, RepoMetadata
from domain.matching.funnel_rules import (
    stage1_hard_filter,
    stage2_relevance_score,
    stage3_should_include,
)


def _make_repo(**overrides) -> RepoMetadata:
    defaults = dict(
        name="test-repo",
        owner="sabyun",
        url="https://github.com/sabyun/test-repo",
        is_fork=False,
        is_org_repo=False,
        days_since_push=30,
        languages=["Python"],
        total_loc=1000,
        detected_tech_stack=["FastAPI", "PostgreSQL"],
        user_contribution_ratio=1.0,
        description="Test repository",
    )
    defaults.update(overrides)
    return RepoMetadata(**defaults)


class TestStage1HardFilter:
    def test_removes_forks(self):
        repos = [_make_repo(is_fork=True)]
        result = stage1_hard_filter(repos, ["Python"], FunnelConfig())
        assert len(result) == 0

    def test_removes_old_repos(self):
        repos = [_make_repo(days_since_push=400)]
        result = stage1_hard_filter(repos, ["Python"], FunnelConfig())
        assert len(result) == 0

    def test_removes_low_org_contribution(self):
        repos = [_make_repo(is_org_repo=True, user_contribution_ratio=0.05)]
        result = stage1_hard_filter(repos, ["Python"], FunnelConfig())
        assert len(result) == 0

    def test_removes_language_mismatch(self):
        repos = [_make_repo(languages=["JavaScript"])]
        result = stage1_hard_filter(repos, ["Python", "Go"], FunnelConfig())
        assert len(result) == 0

    def test_keeps_matching_repo(self):
        repos = [_make_repo()]
        result = stage1_hard_filter(repos, ["Python"], FunnelConfig())
        assert len(result) == 1

    def test_empty_jd_languages_skips_check(self):
        repos = [_make_repo(languages=["Rust"])]
        result = stage1_hard_filter(repos, [], FunnelConfig())
        assert len(result) == 1

    def test_org_repo_above_threshold_kept(self):
        repos = [_make_repo(is_org_repo=True, user_contribution_ratio=0.15)]
        result = stage1_hard_filter(repos, ["Python"], FunnelConfig())
        assert len(result) == 1


class TestStage2RelevanceScore:
    def test_tech_stack_matching(self):
        repos = [_make_repo(detected_tech_stack=["FastAPI", "PostgreSQL"])]
        scored = stage2_relevance_score(repos, [], ["FastAPI", "PostgreSQL"])
        assert scored[0][1] > 0

    def test_recent_activity_bonus(self):
        recent = _make_repo(days_since_push=10, detected_tech_stack=[])
        old = _make_repo(days_since_push=200, detected_tech_stack=[])
        scored = stage2_relevance_score([recent, old], [], [])
        assert scored[0][1] > scored[1][1]

    def test_sorted_descending(self):
        repos = [
            _make_repo(name="low", detected_tech_stack=[], days_since_push=200, total_loc=100),
            _make_repo(name="high", detected_tech_stack=["FastAPI", "React"], days_since_push=10),
        ]
        scored = stage2_relevance_score(repos, [], ["FastAPI", "React"])
        assert scored[0][0].name == "high"


class TestStage3ShouldInclude:
    def test_above_threshold(self):
        assert stage3_should_include(0.75, FunnelConfig()) is True

    def test_below_threshold(self):
        assert stage3_should_include(0.50, FunnelConfig()) is False

    def test_exact_threshold(self):
        assert stage3_should_include(0.60, FunnelConfig()) is True
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_funnel_rules.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/matching/models.py
"""Funnel Selection 도메인 모델.

JD 기반 레포지토리 퍼널 선별을 위한 모델.
설계 참조: Obsidian domain/funnel-selection/MOC.md
"""
from pydantic import BaseModel, ConfigDict, Field


class RepoMetadata(BaseModel):
    """GitHub 레포지토리 메타데이터."""
    model_config = ConfigDict(strict=True)

    name: str
    owner: str
    url: str
    is_fork: bool
    is_org_repo: bool = False
    days_since_push: int = Field(ge=0)
    languages: list[str] = []
    total_loc: int = Field(ge=0, default=0)
    detected_tech_stack: list[str] = []
    user_contribution_ratio: float = Field(ge=0.0, le=1.0, default=1.0)
    description: str = ""


class FunnelConfig(BaseModel):
    """Funnel Selection 설정."""
    model_config = ConfigDict(strict=True)

    min_push_days: int = 365
    min_stars: int = 0
    max_repos: int = 20
    top_k: int = 5
    org_contribution_threshold: float = 0.10
    vector_similarity_min: float = 0.60
```

```python
# jittda/backend/src/domain/matching/funnel_rules.py
"""Funnel Selection 규칙 — 3단계 퍼널.

전체 레포에서 JD에 가장 적합한 상위 3-5개를 선별한다.
Stage 1: Hard Filter (메타데이터)
Stage 2: Relevance Scoring (기술 스택 매칭)
Stage 3: Vector Similarity (벡터 유사도 임계값)
설계 참조: Obsidian domain/funnel-selection/
"""
from domain.matching.models import FunnelConfig, RepoMetadata


def stage1_hard_filter(
    repos: list[RepoMetadata],
    jd_languages: list[str],
    config: FunnelConfig,
) -> list[RepoMetadata]:
    """Stage 1: 메타데이터 기반 하드 필터."""
    filtered = []
    jd_lang_set = set(jd_languages)

    for repo in repos:
        if repo.is_fork:
            continue
        if repo.days_since_push > config.min_push_days:
            continue
        if repo.is_org_repo and repo.user_contribution_ratio < config.org_contribution_threshold:
            continue
        if jd_lang_set and not set(repo.languages).intersection(jd_lang_set):
            continue
        filtered.append(repo)

    return filtered


def stage2_relevance_score(
    repos: list[RepoMetadata],
    jd_requirements: list[str],
    jd_tech_stack: list[str],
) -> list[tuple[RepoMetadata, float]]:
    """Stage 2: JD 기반 적합성 스코어링."""
    jd_stack_set = set(jd_tech_stack)
    scored = []

    for repo in repos:
        score = 0.0
        matched_techs = set(repo.detected_tech_stack).intersection(jd_stack_set)
        score += len(matched_techs) * 0.3
        if repo.days_since_push < 90:
            score += 0.2
        if repo.total_loc > 500:
            score += 0.1
        scored.append((repo, score))

    return sorted(scored, key=lambda x: x[1], reverse=True)


def stage3_should_include(
    similarity: float,
    config: FunnelConfig,
) -> bool:
    """Stage 3: 벡터 유사도 임계값 판정."""
    return similarity >= config.vector_similarity_min
```

```python
# jittda/backend/src/domain/matching/__init__.py
"""Funnel Selection 도메인."""
from domain.matching.funnel_rules import (
    stage1_hard_filter,
    stage2_relevance_score,
    stage3_should_include,
)
from domain.matching.models import FunnelConfig, RepoMetadata

__all__ = [
    "FunnelConfig",
    "RepoMetadata",
    "stage1_hard_filter",
    "stage2_relevance_score",
    "stage3_should_include",
]
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_funnel_rules.py -v`
Expected: ALL PASS (10 tests)

**Step 5: Commit**

```bash
but commit -m "feat: Funnel Selection — 3단계 퍼널 규칙 [JIT-240]" feat/JIT-236-identity-models
```

---

## Task 7: Scoring Calculator [JIT-242]

**Files:**
- Create: `jittda/backend/src/domain/scoring/models.py`
- Create: `jittda/backend/src/domain/scoring/calculator.py`
- Create: `jittda/backend/src/domain/scoring/confidence.py`
- Modify: `jittda/backend/src/domain/scoring/__init__.py`
- Test: `jittda/backend/tests/domain/test_scoring.py`

**설계 참조:** Obsidian `domain/scoring-system/`, `plan/v5-design/phase1-domain.md` §11

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_scoring.py
"""Scoring Calculator 테스트 — 4대 지표 가중 합산."""
import pytest
from domain.scoring.models import (
    MetricScore,
    CandidateScore,
    MetricType,
    ScoreConfidence,
)
from domain.scoring.calculator import calculate_weighted_score
from domain.scoring.confidence import determine_confidence


class TestMetricScore:
    def test_create_valid(self):
        score = MetricScore(
            metric_type=MetricType.LOGIC,
            raw_score=75.0,
            normalized_score=75.0,
            sub_scores={"cyclomatic": 80.0, "halstead": 70.0, "cognitive": 75.0},
            evidence_count=5,
        )
        assert score.normalized_score == 75.0

    def test_score_clamped_0_100(self):
        with pytest.raises(Exception):
            MetricScore(
                metric_type=MetricType.LOGIC,
                raw_score=150.0,
                normalized_score=150.0,
                sub_scores={},
                evidence_count=0,
            )


class TestCalculateWeightedScore:
    def test_default_weights(self):
        scores = {
            MetricType.LOGIC: MetricScore(
                metric_type=MetricType.LOGIC, raw_score=80, normalized_score=80,
                sub_scores={}, evidence_count=5,
            ),
            MetricType.MASTERY: MetricScore(
                metric_type=MetricType.MASTERY, raw_score=70, normalized_score=70,
                sub_scores={}, evidence_count=5,
            ),
            MetricType.STABILITY: MetricScore(
                metric_type=MetricType.STABILITY, raw_score=60, normalized_score=60,
                sub_scores={}, evidence_count=3,
            ),
            MetricType.AUTHENTICITY: MetricScore(
                metric_type=MetricType.AUTHENTICITY, raw_score=90, normalized_score=90,
                sub_scores={}, evidence_count=4,
            ),
        }
        result = calculate_weighted_score(scores)
        expected = 0.30 * 80 + 0.30 * 70 + 0.20 * 60 + 0.20 * 90
        assert result.weighted_total == pytest.approx(expected)

    def test_all_zeros(self):
        scores = {
            mt: MetricScore(
                metric_type=mt, raw_score=0, normalized_score=0,
                sub_scores={}, evidence_count=0,
            )
            for mt in MetricType
        }
        result = calculate_weighted_score(scores)
        assert result.weighted_total == 0.0

    def test_all_perfect(self):
        scores = {
            mt: MetricScore(
                metric_type=mt, raw_score=100, normalized_score=100,
                sub_scores={}, evidence_count=10,
            )
            for mt in MetricType
        }
        result = calculate_weighted_score(scores)
        assert result.weighted_total == pytest.approx(100.0)

    def test_missing_metric_raises(self):
        scores = {
            MetricType.LOGIC: MetricScore(
                metric_type=MetricType.LOGIC, raw_score=80, normalized_score=80,
                sub_scores={}, evidence_count=5,
            ),
        }
        with pytest.raises(ValueError, match="4개 지표 모두 필요"):
            calculate_weighted_score(scores)


class TestDetermineConfidence:
    def test_high_confidence(self):
        assert determine_confidence(data_source_count=3, public_repo_count=5) == ScoreConfidence.HIGH

    def test_medium_confidence(self):
        assert determine_confidence(data_source_count=2, public_repo_count=3) == ScoreConfidence.MEDIUM

    def test_low_confidence(self):
        assert determine_confidence(data_source_count=1, public_repo_count=1) == ScoreConfidence.LOW

    def test_low_repos_even_with_many_sources(self):
        assert determine_confidence(data_source_count=5, public_repo_count=0) == ScoreConfidence.LOW
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_scoring.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/scoring/models.py
"""Scoring 도메인 모델.

4대 핵심 지표 (Logic, Mastery, Stability, Authenticity) 점수 모델.
설계 참조: Obsidian domain/scoring-system/
"""
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MetricType(StrEnum):
    LOGIC = "logic"
    MASTERY = "mastery"
    STABILITY = "stability"
    AUTHENTICITY = "authenticity"


class ScoreConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MetricScore(BaseModel):
    """개별 지표 점수."""
    model_config = ConfigDict(strict=True)

    metric_type: MetricType
    raw_score: float = Field(ge=0, le=100)
    normalized_score: float = Field(ge=0, le=100)
    sub_scores: dict[str, float]
    evidence_count: int = Field(ge=0)


class CandidateScore(BaseModel):
    """후보자 종합 점수."""
    model_config = ConfigDict(strict=True)

    logic: MetricScore
    mastery: MetricScore
    stability: MetricScore
    authenticity: MetricScore
    weighted_total: float = Field(ge=0, le=100)
    confidence: ScoreConfidence
```

```python
# jittda/backend/src/domain/scoring/calculator.py
"""4대 지표 가중 합산 계산기.

최종 점수 = 0.30 × 논리력 + 0.30 × 전문성 + 0.20 × 안정성 + 0.20 × 진정성
설계 참조: Obsidian domain/scoring-system/four-metrics.md
"""
from domain.scoring.confidence import determine_confidence
from domain.scoring.models import CandidateScore, MetricScore, MetricType, ScoreConfidence

WEIGHTS: dict[MetricType, float] = {
    MetricType.LOGIC: 0.30,
    MetricType.MASTERY: 0.30,
    MetricType.STABILITY: 0.20,
    MetricType.AUTHENTICITY: 0.20,
}


def calculate_weighted_score(
    scores: dict[MetricType, MetricScore],
) -> CandidateScore:
    """4대 지표를 가중 합산하여 CandidateScore 생성."""
    if set(scores.keys()) != set(MetricType):
        raise ValueError("4개 지표 모두 필요합니다.")

    weighted_total = sum(
        scores[mt].normalized_score * WEIGHTS[mt]
        for mt in MetricType
    )

    total_evidence = sum(s.evidence_count for s in scores.values())
    confidence = determine_confidence(
        data_source_count=len([s for s in scores.values() if s.evidence_count > 0]),
        public_repo_count=total_evidence,
    )

    return CandidateScore(
        logic=scores[MetricType.LOGIC],
        mastery=scores[MetricType.MASTERY],
        stability=scores[MetricType.STABILITY],
        authenticity=scores[MetricType.AUTHENTICITY],
        weighted_total=round(weighted_total, 2),
        confidence=confidence,
    )
```

```python
# jittda/backend/src/domain/scoring/confidence.py
"""신뢰도 판정.

데이터 소스 수 × 공개 레포 수 2차원 매트릭스.
설계 참조: Obsidian domain/scoring-system/confidence-levels.md
"""
from domain.scoring.models import ScoreConfidence


def determine_confidence(
    data_source_count: int,
    public_repo_count: int,
) -> ScoreConfidence:
    """2차원 매트릭스 기반 신뢰도 판정."""
    if data_source_count >= 3 and public_repo_count >= 5:
        return ScoreConfidence.HIGH
    if data_source_count >= 2 and public_repo_count >= 2:
        return ScoreConfidence.MEDIUM
    return ScoreConfidence.LOW
```

```python
# jittda/backend/src/domain/scoring/__init__.py
"""Scoring 도메인."""
from domain.scoring.calculator import calculate_weighted_score
from domain.scoring.models import (
    CandidateScore,
    MetricScore,
    MetricType,
    ScoreConfidence,
)

__all__ = [
    "CandidateScore",
    "MetricScore",
    "MetricType",
    "ScoreConfidence",
    "calculate_weighted_score",
]
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_scoring.py -v`
Expected: ALL PASS (8 tests)

**Step 5: Commit**

```bash
but commit -m "feat: Scoring Calculator — 4대 지표 가중 합산 [JIT-242]" feat/JIT-236-identity-models
```

---

## Task 8: Question + Analysis 도메인 모델 (보너스)

**Files:**
- Create: `jittda/backend/src/domain/question/models.py`
- Create: `jittda/backend/src/domain/analysis/models.py`
- Modify: `jittda/backend/src/domain/question/__init__.py`
- Modify: `jittda/backend/src/domain/analysis/__init__.py`
- Test: `jittda/backend/tests/domain/test_question_models.py`
- Test: `jittda/backend/tests/domain/test_analysis_models.py`

**설계 참조:** `plan/v5-design/phase1-domain.md` §12.1

> 이 Task는 Phase 4에서 사용할 모델을 미리 정의한다. 구현이 간단하므로 Phase 1에서 함께 처리.

**Step 1: Write the failing test**

```python
# jittda/backend/tests/domain/test_question_models.py
"""Question 도메인 모델 테스트."""
from domain.question.models import InterviewQuestion, QuestionStrategy, QuestionCategory


class TestInterviewQuestion:
    def test_create(self):
        q = InterviewQuestion(
            question_id="Q001",
            category=QuestionCategory.TECHNICAL_DEPTH,
            strategy=QuestionStrategy.NEGATIVE_SELECTION,
            difficulty="medium",
            question_text="이 코드에서 async/await를 사용하지 않은 이유를 설명해주세요.",
            intent="비동기 프로그래밍 이해도를 확인합니다.",
            code_reference="src/main.py:42",
            expected_answer_guide="I/O 바운드가 아닌 CPU 바운드 작업이므로 동기 처리가 적합합니다.",
            red_flags=["async를 모른다고 답변"],
            follow_up_triggers=["비동기가 필요한 경우를 물어볼 수 있습니다"],
            terminology=[{"term": "async/await", "explanation": "비동기 실행 키워드"}],
        )
        assert q.category == QuestionCategory.TECHNICAL_DEPTH
        assert q.strategy == QuestionStrategy.NEGATIVE_SELECTION
```

```python
# jittda/backend/tests/domain/test_analysis_models.py
"""Analysis 도메인 모델 테스트."""
from domain.analysis.models import ComplexityMetrics, AuthenticityScore, SkillAssessment


class TestComplexityMetrics:
    def test_create(self):
        m = ComplexityMetrics(
            cyclomatic_complexity=5.2,
            halstead_difficulty=12.0,
            halstead_volume=300.0,
            maintainability_index=72.0,
            cognitive_complexity=8.0,
        )
        assert m.cyclomatic_complexity == 5.2

class TestAuthenticityScore:
    def test_create(self):
        s = AuthenticityScore(
            human_typing_ratio=0.85,
            originality_ratio=0.90,
            ai_code_suspicion=0.10,
            plagiarism_ratio=0.05,
            style_consistency=0.92,
        )
        assert s.originality_ratio == 0.90

class TestSkillAssessment:
    def test_create(self):
        sa = SkillAssessment(
            skill_name="Python",
            proficiency="advanced",
            evidence_count=15,
            evidence_sources=["github:repo1", "linkedin"],
            confidence="high",
        )
        assert sa.proficiency == "advanced"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_question_models.py tests/domain/test_analysis_models.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# jittda/backend/src/domain/question/models.py
"""면접 질문 도메인 모델.

Instructor로 LLM이 직접 생성하는 구조화된 면접 질문.
설계 참조: plan/v5-design/phase1-domain.md §12.1
"""
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QuestionCategory(StrEnum):
    TECHNICAL_DEPTH = "technical_depth"
    EXECUTION_OWNERSHIP = "execution_ownership"
    COMMUNICATION = "communication"
    ROLE_FIT = "role_fit"
    RISK_FLAGS = "risk_flags"


class QuestionStrategy(StrEnum):
    NEGATIVE_SELECTION = "negative_selection"
    INTENTIONAL_COMPLEXITY = "intentional_complexity"
    CODE_EVOLUTION = "code_evolution"


class InterviewQuestion(BaseModel):
    """구조화된 면접 질문."""
    model_config = ConfigDict(strict=True)

    question_id: str
    category: QuestionCategory
    strategy: QuestionStrategy
    difficulty: str  # easy | medium | hard
    question_text: str = Field(min_length=10, max_length=500)
    intent: str
    code_reference: str | None = None
    expected_answer_guide: str
    red_flags: list[str]
    follow_up_triggers: list[str]
    terminology: list[dict]
```

```python
# jittda/backend/src/domain/analysis/models.py
"""Analysis 도메인 모델 — 코드 분석 결과 구조.

설계 참조: plan/v5-design/phase1-domain.md §12.1
"""
from pydantic import BaseModel, ConfigDict, Field


class ComplexityMetrics(BaseModel):
    model_config = ConfigDict(strict=True)

    cyclomatic_complexity: float = Field(ge=0)
    halstead_difficulty: float = Field(ge=0)
    halstead_volume: float = Field(ge=0)
    maintainability_index: float = Field(ge=0, le=100)
    cognitive_complexity: float = Field(ge=0)


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
    evidence_sources: list[str]
    confidence: str  # high | medium | low
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/test_question_models.py tests/domain/test_analysis_models.py -v`
Expected: ALL PASS (4 tests)

**Step 5: Commit**

```bash
but commit -m "feat: Question + Analysis 도메인 모델 [JIT-236]" feat/JIT-236-identity-models
```

---

## Task 9: 전체 통합 테스트 + PR

**Step 1: 전체 도메인 테스트 실행**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && PYTHONPATH=src python -m pytest tests/domain/ -v --tb=short`
Expected: ALL PASS (약 70+ tests)

**Step 2: 린트**

Run: `cd /Users/sabyun/goinfre/IaaS/jittda/backend && pip install ruff && ruff check src/domain/`
Expected: No errors

**Step 3: 최종 커밋 + 푸시**

```bash
but push feat/JIT-236-identity-models
```

**Step 4: PR 생성**

```bash
but pr new feat/JIT-236-identity-models -m "feat: Phase 1 — Domain Layer 전체 구현 [JIT-236~242]

## Summary
- Identity Resolution 모델 (MailmapEntry, IdentityCluster, BlameLineAttribution, PureContribution)
- LinkedIn 프로필 모델 + 정규화 함수
- Mailmap Builder — 4가지 규칙 기반 동적 .mailmap 생성
- Blame Filter — identity cluster 기반 blame 라인 필터링
- Semantic Pruner — import/주석/config/generated 코드 제거 규칙
- Funnel Selection — 3단계 퍼널 (Hard Filter → Relevance Score → Vector)
- Scoring Calculator — 4대 지표 가중 합산 (Logic 30% + Mastery 30% + Stability 20% + Authenticity 20%)
- Question + Analysis 도메인 모델

## Test
- 전체 도메인 테스트 70+ 통과
- ruff lint 통과"
```

**Step 5: Linear 티켓 업데이트**

```bash
source .claude/skills/linear-ops/linear-api.sh
for ticket in JIT-236 JIT-237 JIT-238 JIT-239 JIT-240 JIT-241 JIT-242; do
  linear_update_status "$ticket" "done"
done
```
