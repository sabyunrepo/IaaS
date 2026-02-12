"""PyDriller 다중 author 파라미터 테스트 (JIT-36).

테스트 시나리오:
1. 다중 author: ["sabyun", "변상훈"] → 두 이름의 커밋 모두 수집, 중복 SHA 제거
2. 단일 author: ["sabyun"] → 기존 동작과 동일
3. 빈 리스트: [] → 전체 커밋 수집 (필터 없음)
4. 기여도 정합성: 수집된 커밋 수 == contributions 값
5. code_analysis.py의 다중 author 목록 추출 로직
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.code_analyzer import CodeAnalyzer


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def analyzer():
    return CodeAnalyzer()


class FakeModification:
    def __init__(self, filename="test.py", diff="+ hello", added=5, deleted=2, complexity=3, nloc=10):
        self.filename = filename
        self.diff = diff
        self.added_lines = added
        self.deleted_lines = deleted
        self.complexity = complexity
        self.nloc = nloc
        self.methods = []
        self.source_code = "print('hello')"


class FakeCommit:
    def __init__(self, hash_val, author_name, msg="test commit", modified_files=None):
        self.hash = hash_val
        self.msg = msg
        self.committer_date = MagicMock()
        self.committer_date.isoformat.return_value = "2026-01-15T10:00:00+00:00"
        self.committer_date.strftime.return_value = "2026-01"
        self.author = MagicMock()
        self.author.name = author_name
        self.modified_files = modified_files or [FakeModification()]


# ──────────────────────────────────────────────
# 1. author 파라미터 정규화 테스트
# ──────────────────────────────────────────────

class TestAuthorParameterNormalization:
    """analyze_with_pydriller의 author 파라미터 타입 정규화."""

    @pytest.mark.asyncio
    async def test_str_author_becomes_list(self, analyzer):
        """str → [str] 변환 확인."""
        commits = [
            FakeCommit("abc123def456", "sabyun"),
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author="sabyun",
            )
            # only_authors에 ["sabyun"] 전달 확인
            call_kwargs = mock_repo.call_args
            assert call_kwargs[1]["only_authors"] == ["sabyun"]

    @pytest.mark.asyncio
    async def test_list_author_passed_directly(self, analyzer):
        """list[str] → 그대로 전달."""
        commits = [
            FakeCommit("abc123def456", "sabyun"),
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=["sabyun", "변상훈"],
            )
            call_kwargs = mock_repo.call_args
            assert call_kwargs[1]["only_authors"] == ["sabyun", "변상훈"]

    @pytest.mark.asyncio
    async def test_empty_list_becomes_none(self, analyzer):
        """빈 리스트 → None (전체 커밋 수집)."""
        commits = [
            FakeCommit("abc123def456", "anyone"),
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=[],
            )
            call_kwargs = mock_repo.call_args
            assert call_kwargs[1]["only_authors"] is None

    @pytest.mark.asyncio
    async def test_none_author_stays_none(self, analyzer):
        """None → None (기존 동작 호환)."""
        commits = [
            FakeCommit("abc123def456", "anyone"),
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=None,
            )
            call_kwargs = mock_repo.call_args
            assert call_kwargs[1]["only_authors"] is None


# ──────────────────────────────────────────────
# 2. 중복 SHA 제거
# ──────────────────────────────────────────────

class TestDuplicateSHADedup:
    """다중 author로 동일 커밋이 중복 반환될 때 SHA 기반 중복 제거."""

    @pytest.mark.asyncio
    async def test_duplicate_sha_removed(self, analyzer):
        """같은 SHA 커밋이 2번 나오면 1번만 수집."""
        commits = [
            FakeCommit("abc123def456", "sabyun", msg="first"),
            FakeCommit("abc123def456", "변상훈", msg="first"),  # 동일 SHA
            FakeCommit("def456abc789", "sabyun", msg="second"),
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=["sabyun", "변상훈"],
            )
            assert result["stats"]["total_commits"] == 2

    @pytest.mark.asyncio
    async def test_no_duplicates_no_loss(self, analyzer):
        """중복 없으면 전부 수집."""
        commits = [
            FakeCommit("aaa111bbb222", "sabyun"),
            FakeCommit("bbb222ccc333", "변상훈"),
            FakeCommit("ccc333ddd444", "sabyun"),
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=["sabyun", "변상훈"],
            )
            assert result["stats"]["total_commits"] == 3


# ──────────────────────────────────────────────
# 3. 기여도 정합성
# ──────────────────────────────────────────────

class TestContributionIntegrity:
    """수집된 커밋 수 == stats.total_commits 정합성."""

    @pytest.mark.asyncio
    async def test_commit_count_matches(self, analyzer):
        """commits 리스트 길이와 total_commits 일치."""
        commits = [
            FakeCommit(f"hash{i:010d}pad", "sabyun")
            for i in range(5)
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=["sabyun"],
            )
            assert len(result["commits"]) == result["stats"]["total_commits"]
            assert result["stats"]["total_commits"] == 5

    @pytest.mark.asyncio
    async def test_additions_deletions_summed(self, analyzer):
        """다중 author 커밋의 additions/deletions 합산."""
        mod1 = FakeModification(added=10, deleted=3)
        mod2 = FakeModification(added=20, deleted=5)
        commits = [
            FakeCommit("aaa111bbb222", "sabyun", modified_files=[mod1]),
            FakeCommit("bbb222ccc333", "변상훈", modified_files=[mod2]),
        ]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=["sabyun", "변상훈"],
            )
            assert result["stats"]["total_additions"] == 30
            assert result["stats"]["total_deletions"] == 8


# ──────────────────────────────────────────────
# 4. 단일 author 하위 호환성
# ──────────────────────────────────────────────

class TestSingleAuthorCompat:
    """기존 단일 author 동작 호환성."""

    @pytest.mark.asyncio
    async def test_single_str_unchanged_behavior(self, analyzer):
        """기존 str author 전달 시 동일 결과."""
        commits = [FakeCommit("abc123def456", "sabyun")]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author="sabyun",
            )
            assert result["stats"]["total_commits"] == 1
            assert len(result["commits"]) == 1


# ──────────────────────────────────────────────
# 5. code_analysis.py 다중 author 추출 로직
# ──────────────────────────────────────────────

class TestMultiAuthorExtraction:
    """identity_result.matches에서 다중 author name 추출."""

    def test_extract_identity_linked_authors(self):
        """commit_pattern_analysis 제외한 identity-linked name만 수집."""
        from app.models.author_identity import AuthorIdentityResult, AuthorMatch

        matches = [
            AuthorMatch(name="sabyun", email="s@g.com", commits=50,
                        confidence=1.0, method="name_exact"),
            AuthorMatch(name="DevUser", email="12345+sabyun@users.noreply.github.com",
                        commits=40, confidence=0.95, method="noreply_email"),
            AuthorMatch(name="major-contrib", email="m@g.com", commits=80,
                        confidence=0.5, method="commit_pattern_analysis"),
        ]
        result = AuthorIdentityResult(
            matches=matches,
            best_match=matches[0],
        )

        # JIT-36 로직 재현: commit_pattern_analysis 제외
        candidate_author_names = list(dict.fromkeys(
            m.name for m in result.matches
            if m.method != "commit_pattern_analysis"
        ))
        assert candidate_author_names == ["sabyun", "DevUser"]
        assert "major-contrib" not in candidate_author_names

    def test_empty_matches_returns_empty(self):
        """매칭 없으면 빈 리스트."""
        from app.models.author_identity import AuthorIdentityResult

        result = AuthorIdentityResult()
        candidate_author_names = list(dict.fromkeys(
            m.name for m in result.matches
            if m.method != "commit_pattern_analysis"
        ))
        assert candidate_author_names == []

    def test_dedup_preserves_order(self):
        """동일 name 중복 제거, 순서 유지."""
        from app.models.author_identity import AuthorIdentityResult, AuthorMatch

        matches = [
            AuthorMatch(name="sabyun", email="s@g.com", commits=50,
                        confidence=1.0, method="name_exact"),
            AuthorMatch(name="sabyun", email="sabyun@company.com", commits=30,
                        confidence=0.9, method="email_prefix"),
            AuthorMatch(name="DevUser", email="12345+sabyun@users.noreply.github.com",
                        commits=40, confidence=0.95, method="noreply_email"),
        ]
        result = AuthorIdentityResult(matches=matches, best_match=matches[0])

        candidate_author_names = list(dict.fromkeys(
            m.name for m in result.matches
            if m.method != "commit_pattern_analysis"
        ))
        assert candidate_author_names == ["sabyun", "DevUser"]


# ──────────────────────────────────────────────
# 6. Falsy 값 필터링
# ──────────────────────────────────────────────

class TestFalsyFiltering:
    """author 리스트에서 falsy 값 제거."""

    @pytest.mark.asyncio
    async def test_empty_string_filtered(self, analyzer):
        """빈 문자열은 author 리스트에서 제거."""
        commits = [FakeCommit("abc123def456", "sabyun")]

        with patch("pydriller.Repository") as mock_repo:
            mock_repo.return_value.traverse_commits.return_value = commits
            result = await analyzer.analyze_with_pydriller(
                repo_url="https://github.com/test/repo",
                job_id="test-job",
                author=["sabyun", "", None],
            )
            call_kwargs = mock_repo.call_args
            assert call_kwargs[1]["only_authors"] == ["sabyun"]
