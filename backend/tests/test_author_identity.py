"""AuthorIdentityResolver 유닛 테스트 (JIT-35).

테스트 시나리오:
1. name_exact: 완전 일치 → confidence=1.0
2. noreply_email: noreply 이메일 → confidence=0.95
3. email_prefix: 이메일 접두어 → confidence=0.9
4. name_substring: 부분 일치 → confidence=0.7
5. email_domain_match: 동일 커스텀 도메인 → confidence=0.6
6. fork 방어: top_committer_fallback 삭제 확인
7. cross-repo 검증: 2+ 레포 매칭 시 confidence 부스트
8. zero match: 매칭 없음 → matches=[], best_match=None
"""

import pytest

from app.models.author_identity import AuthorIdentityResult, AuthorMatch
from app.services.github_service import GitHubService


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def basic_authors() -> list[dict]:
    """기본 git authors 리스트."""
    return [
        {"name": "sabyun", "email": "sabyun@gmail.com", "commits": 50},
        {"name": "Alice", "email": "alice@company.com", "commits": 30},
        {"name": "Bob", "email": "bob@company.com", "commits": 20},
    ]


@pytest.fixture
def noreply_authors() -> list[dict]:
    """noreply 이메일 포함 authors."""
    return [
        {"name": "DevUser", "email": "12345+sabyun@users.noreply.github.com", "commits": 40},
        {"name": "Other", "email": "other@gmail.com", "commits": 10},
    ]


@pytest.fixture
def fork_authors() -> list[dict]:
    """Fork 레포 시뮬레이션 — 실제 후보자가 아닌 author가 top committer."""
    return [
        {"name": "Ubuntu", "email": "ubuntu@localhost", "commits": 200},
        {"name": "root", "email": "root@localhost", "commits": 100},
        {"name": "bot", "email": "bot@ci.com", "commits": 50},
    ]


# ──────────────────────────────────────────────
# 1. name_exact
# ──────────────────────────────────────────────

class TestNameExact:
    def test_exact_match(self, basic_authors):
        result = GitHubService.resolve_author_by_identity("sabyun", basic_authors)
        assert isinstance(result, AuthorIdentityResult)
        assert result.best_match is not None
        assert result.best_match.confidence == 1.0
        assert result.best_match.method == "name_exact"
        assert result.best_match.name == "sabyun"

    def test_case_insensitive(self, basic_authors):
        result = GitHubService.resolve_author_by_identity("Sabyun", basic_authors)
        assert result.best_match is not None
        assert result.best_match.confidence == 1.0
        assert result.best_match.method == "name_exact"


# ──────────────────────────────────────────────
# 2. noreply_email
# ──────────────────────────────────────────────

class TestNoreplyEmail:
    def test_noreply_match(self, noreply_authors):
        result = GitHubService.resolve_author_by_identity("sabyun", noreply_authors)
        assert result.best_match is not None
        assert result.best_match.confidence == 0.95
        assert result.best_match.method == "noreply_email"
        assert result.best_match.name == "DevUser"


# ──────────────────────────────────────────────
# 3. email_prefix
# ──────────────────────────────────────────────

class TestEmailPrefix:
    def test_email_prefix_match(self):
        authors = [
            {"name": "John Doe", "email": "sabyun@company.com", "commits": 25},
            {"name": "Jane", "email": "jane@gmail.com", "commits": 15},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is not None
        assert result.best_match.confidence == 0.9
        assert result.best_match.method == "email_prefix"

    def test_email_with_plus_tag(self):
        authors = [
            {"name": "TagUser", "email": "notifications+sabyun@company.com", "commits": 10},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is not None
        assert result.best_match.confidence == 0.9
        assert result.best_match.method == "email_prefix"


# ──────────────────────────────────────────────
# 4. name_substring
# ──────────────────────────────────────────────

class TestNameSubstring:
    def test_username_in_author_name(self):
        authors = [
            {"name": "sabyunrepo-dev", "email": "x@y.com", "commits": 20},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is not None
        assert result.best_match.confidence == 0.7
        assert result.best_match.method == "name_substring"

    def test_author_name_in_username(self):
        authors = [
            {"name": "sab", "email": "x@y.com", "commits": 20},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is not None
        assert result.best_match.confidence == 0.7
        assert result.best_match.method == "name_substring"

    def test_short_name_skipped(self):
        """2자 이하 username은 substring 매칭 스킵."""
        authors = [
            {"name": "ab-something", "email": "x@y.com", "commits": 20},
        ]
        result = GitHubService.resolve_author_by_identity("ab", authors)
        # substring 매칭 안 됨 (len < 3)
        assert result.best_match is None or result.best_match.method != "name_substring"


# ──────────────────────────────────────────────
# 5. email_domain_match
# ──────────────────────────────────────────────

class TestEmailDomainMatch:
    def test_custom_domain_match(self):
        authors = [
            {"name": "TeamMember1", "email": "dev1@mycompany.io", "commits": 30},
            {"name": "TeamMember2", "email": "dev2@mycompany.io", "commits": 20},
        ]
        result = GitHubService.resolve_author_by_identity("unknown-user", authors)
        assert result.best_match is not None
        assert result.best_match.confidence == 0.6
        assert result.best_match.method == "email_domain_match"

    def test_public_domain_skipped(self):
        """gmail 등 공개 도메인은 email_domain_match 안 함."""
        authors = [
            {"name": "Person1", "email": "a@gmail.com", "commits": 30},
            {"name": "Person2", "email": "b@gmail.com", "commits": 20},
        ]
        result = GitHubService.resolve_author_by_identity("unknown-user", authors)
        # gmail은 공개 도메인이므로 email_domain_match 안 됨
        matched_methods = [m.method for m in result.matches]
        assert "email_domain_match" not in matched_methods


# ──────────────────────────────────────────────
# 6. Fork 레포 방어 (top_committer_fallback 삭제)
# ──────────────────────────────────────────────

class TestForkDefense:
    def test_no_top_committer_fallback(self, fork_authors):
        """Fork 레포에서 top_committer_fallback이 발동하지 않아야 함."""
        result = GitHubService.resolve_author_by_identity("sabyun", fork_authors)
        # Ubuntu/root/bot 중 어느 것도 sabyun과 매칭 안 됨
        for m in result.matches:
            assert m.method != "top_committer_fallback"

    def test_sesami_rag_case(self):
        """sesami_rag 레포: Ubuntu가 top committer지만 매칭 안 됨."""
        authors = [
            {"name": "Ubuntu", "email": "ubuntu@ip.internal", "commits": 500},
            {"name": "dependabot[bot]", "email": "bot@github.com", "commits": 50},
        ]
        result = GitHubService.resolve_author_by_identity("actual-candidate", authors)
        assert result.best_match is None or result.best_match.name != "Ubuntu"

    def test_deepagent_case(self):
        """deepagent 레포: alsksssass가 top committer지만 매칭 안 됨."""
        authors = [
            {"name": "alsksssass", "email": "als@naver.com", "commits": 300},
            {"name": "GitHub Actions", "email": "actions@github.com", "commits": 20},
        ]
        result = GitHubService.resolve_author_by_identity("real-user", authors)
        assert result.best_match is None or result.best_match.name != "alsksssass"


# ──────────────────────────────────────────────
# 7. Cross-repo 검증
# ──────────────────────────────────────────────

class TestCrossRepoVerification:
    def test_multi_repo_boost(self):
        """3개 레포 중 2개에서 매칭 → confidence 부스트."""
        repo_a = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun", "email": "s@g.com", "commits": 30}],
            repo_name="repo-a",
        )
        repo_b = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun", "email": "s@g.com", "commits": 20}],
            repo_name="repo-b",
        )
        repo_c = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "unknown", "email": "x@y.com", "commits": 10}],
            repo_name="repo-c",
        )

        merged = GitHubService.verify_cross_repo({
            "repo-a": repo_a,
            "repo-b": repo_b,
            "repo-c": repo_c,
        })

        assert merged.cross_repo_verified is True
        assert merged.best_match is not None
        assert merged.best_match.name == "sabyun"
        # 1.0 * 1.3 = 1.3 → cap 1.0
        assert merged.best_match.confidence == 1.0
        assert merged.best_match.commits == 50  # 30 + 20
        assert len(merged.best_match.repos_matched) == 2

    def test_single_repo_penalty(self):
        """1개 레포에서만 매칭 + 다른 레포 존재 → confidence 패널티."""
        repo_a = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun-dev", "email": "x@y.com", "commits": 10}],
            repo_name="repo-a",
        )
        repo_b = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "unrelated", "email": "u@u.com", "commits": 100}],
            repo_name="repo-b",
        )

        merged = GitHubService.verify_cross_repo({
            "repo-a": repo_a,
            "repo-b": repo_b,
        })

        assert merged.cross_repo_verified is False
        # sabyun-dev: confidence 0.7 * 0.5 = 0.35
        sabyun_match = next(
            (m for m in merged.matches if m.name == "sabyun-dev"), None
        )
        assert sabyun_match is not None
        assert sabyun_match.confidence == 0.35

    def test_empty_results(self):
        merged = GitHubService.verify_cross_repo({})
        assert merged.matches == []
        assert merged.best_match is None
        assert merged.cross_repo_verified is False


# ──────────────────────────────────────────────
# 8. Zero match
# ──────────────────────────────────────────────

class TestZeroMatch:
    def test_no_match(self):
        authors = [
            {"name": "completely-different", "email": "cd@random.org", "commits": 50},
            {"name": "another-person", "email": "ap@other.net", "commits": 30},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        # email_domain_match로 매칭될 수 있으므로 공개 도메인 사용
        authors_public = [
            {"name": "completely-different", "email": "cd@gmail.com", "commits": 5},
            {"name": "another-person", "email": "ap@yahoo.com", "commits": 3},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors_public)
        assert result.matches == []
        assert result.best_match is None

    def test_empty_inputs(self):
        result = GitHubService.resolve_author_by_identity("", [])
        assert result.matches == []
        assert result.best_match is None

    def test_none_username(self):
        result = GitHubService.resolve_author_by_identity(
            None,
            [{"name": "x", "email": "x@x.com", "commits": 1}],
        )
        assert result.matches == []
        assert result.best_match is None


# ──────────────────────────────────────────────
# 엣지 케이스
# ──────────────────────────────────────────────

class TestEdgeCases:
    def test_multiple_methods_single_author(self):
        """한 author가 name_exact + email_prefix 둘 다 매칭 → 중복 제거."""
        authors = [
            {"name": "sabyun", "email": "sabyun@company.com", "commits": 40},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        # name_exact로 먼저 매칭 → email_prefix에서 중복 제거
        assert result.best_match.confidence == 1.0
        assert result.best_match.method == "name_exact"
        # 동일 author가 중복으로 들어가지 않아야 함
        name_count = sum(1 for m in result.matches if m.name == "sabyun")
        assert name_count == 1

    def test_commit_pattern_analysis(self):
        """커밋 50% 이상 + 10+ 커밋 author가 commit_pattern_analysis로 매칭."""
        authors = [
            {"name": "major-contributor", "email": "mc@gmail.com", "commits": 80},
            {"name": "minor1", "email": "m1@gmail.com", "commits": 10},
            {"name": "minor2", "email": "m2@gmail.com", "commits": 10},
        ]
        result = GitHubService.resolve_author_by_identity("unknown-user", authors)
        pattern_matches = [m for m in result.matches if m.method == "commit_pattern_analysis"]
        assert len(pattern_matches) == 1
        assert pattern_matches[0].name == "major-contributor"
        assert pattern_matches[0].confidence == 0.5

    def test_repo_name_tracking(self):
        """repo_name이 matches에 올바르게 전파되는지 확인."""
        authors = [{"name": "sabyun", "email": "s@g.com", "commits": 10}]
        result = GitHubService.resolve_author_by_identity(
            "sabyun", authors, repo_name="my-project"
        )
        assert result.best_match.repos_matched == ["my-project"]
