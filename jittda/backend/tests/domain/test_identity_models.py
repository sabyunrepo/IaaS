"""
Identity Resolution 도메인 모델 테스트

TDD: 테스트 먼저 작성 후 모델 구현
"""
import pytest
from pydantic import ValidationError

from domain.identity.models import (
    BlameLineAttribution,
    ConfidenceLevel,
    GitAuthor,
    GitHubProfile,
    IdentityCluster,
    MailmapEntry,
    PureContribution,
)


# ---------------------------------------------------------------------------
# ConfidenceLevel
# ---------------------------------------------------------------------------


class TestConfidenceLevel:
    def test_values(self):
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.LOW == "low"

    def test_is_str(self):
        assert isinstance(ConfidenceLevel.HIGH, str)


# ---------------------------------------------------------------------------
# GitAuthor
# ---------------------------------------------------------------------------


class TestGitAuthor:
    def test_creation(self):
        author = GitAuthor(name="Alice", email="alice@example.com")
        assert author.name == "Alice"
        assert author.email == "alice@example.com"

    def test_frozen(self):
        author = GitAuthor(name="Alice", email="alice@example.com")
        with pytest.raises((TypeError, ValidationError)):
            author.name = "Bob"  # type: ignore[misc]

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            GitAuthor(email="alice@example.com")  # type: ignore[call-arg]

    def test_missing_email(self):
        with pytest.raises(ValidationError):
            GitAuthor(name="Alice")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# GitHubProfile
# ---------------------------------------------------------------------------


class TestGitHubProfile:
    def test_creation(self):
        profile = GitHubProfile(
            name="Alice Kim",
            email="alice@example.com",
            login="alicekim",
            database_id="MDQ6VXNlcjEyMzQ1",
        )
        assert profile.name == "Alice Kim"
        assert profile.email == "alice@example.com"
        assert profile.login == "alicekim"
        assert profile.database_id == "MDQ6VXNlcjEyMzQ1"

    def test_frozen(self):
        profile = GitHubProfile(
            name="Alice Kim",
            email="alice@example.com",
            login="alicekim",
            database_id="MDQ6VXNlcjEyMzQ1",
        )
        with pytest.raises((TypeError, ValidationError)):
            profile.login = "bob"  # type: ignore[misc]

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            GitHubProfile(name="Alice Kim", email="alice@example.com")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# MailmapEntry
# ---------------------------------------------------------------------------


class TestMailmapEntry:
    def _make(self, confidence: ConfidenceLevel = ConfidenceLevel.HIGH) -> MailmapEntry:
        return MailmapEntry(
            canonical="Alice Kim",
            canonical_email="alice@example.com",
            alias_name="alice",
            alias_email="alice@old.example.com",
            confidence=confidence,
        )

    def test_creation_high(self):
        entry = self._make(ConfidenceLevel.HIGH)
        assert entry.canonical == "Alice Kim"
        assert entry.confidence == ConfidenceLevel.HIGH

    def test_creation_medium(self):
        entry = self._make(ConfidenceLevel.MEDIUM)
        assert entry.confidence == ConfidenceLevel.MEDIUM

    def test_creation_low(self):
        entry = self._make(ConfidenceLevel.LOW)
        assert entry.confidence == ConfidenceLevel.LOW

    def test_frozen(self):
        entry = self._make()
        with pytest.raises((TypeError, ValidationError)):
            entry.canonical = "Bob"  # type: ignore[misc]

    def test_invalid_confidence(self):
        with pytest.raises(ValidationError):
            MailmapEntry(
                canonical="Alice Kim",
                canonical_email="alice@example.com",
                alias_name="alice",
                alias_email="alice@old.example.com",
                confidence="ultra",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# IdentityCluster
# ---------------------------------------------------------------------------


class TestIdentityCluster:
    def _make_alias(self) -> MailmapEntry:
        return MailmapEntry(
            canonical="Alice Kim",
            canonical_email="alice@example.com",
            alias_name="alice",
            alias_email="alice@old.example.com",
            confidence=ConfidenceLevel.HIGH,
        )

    def test_creation_with_aliases(self):
        alias = self._make_alias()
        cluster = IdentityCluster(
            github_node_id="MDQ6VXNlcjEyMzQ1",
            canonical_name="Alice Kim",
            canonical_email="alice@example.com",
            aliases=[alias],
            total_commits=100,
            verified_commits=80,
        )
        assert cluster.canonical_name == "Alice Kim"
        assert len(cluster.aliases) == 1
        assert cluster.total_commits == 100
        assert cluster.verified_commits == 80

    def test_empty_aliases(self):
        cluster = IdentityCluster(
            github_node_id="MDQ6VXNlcjEyMzQ1",
            canonical_name="Alice Kim",
            canonical_email="alice@example.com",
            aliases=[],
            total_commits=50,
            verified_commits=50,
        )
        assert cluster.aliases == []

    def test_verification_ratio_normal(self):
        cluster = IdentityCluster(
            github_node_id="MDQ6VXNlcjEyMzQ1",
            canonical_name="Alice Kim",
            canonical_email="alice@example.com",
            aliases=[],
            total_commits=100,
            verified_commits=75,
        )
        assert cluster.verification_ratio == pytest.approx(0.75)

    def test_verification_ratio_zero_total(self):
        cluster = IdentityCluster(
            github_node_id="MDQ6VXNlcjEyMzQ1",
            canonical_name="Alice Kim",
            canonical_email="alice@example.com",
            aliases=[],
            total_commits=0,
            verified_commits=0,
        )
        assert cluster.verification_ratio == 0.0

    def test_verification_ratio_full(self):
        cluster = IdentityCluster(
            github_node_id="MDQ6VXNlcjEyMzQ1",
            canonical_name="Alice Kim",
            canonical_email="alice@example.com",
            aliases=[],
            total_commits=10,
            verified_commits=10,
        )
        assert cluster.verification_ratio == pytest.approx(1.0)

    def test_negative_commits_rejected(self):
        with pytest.raises(ValidationError):
            IdentityCluster(
                github_node_id="MDQ6VXNlcjEyMzQ1",
                canonical_name="Alice Kim",
                canonical_email="alice@example.com",
                aliases=[],
                total_commits=-1,
                verified_commits=0,
            )

    def test_negative_verified_rejected(self):
        with pytest.raises(ValidationError):
            IdentityCluster(
                github_node_id="MDQ6VXNlcjEyMzQ1",
                canonical_name="Alice Kim",
                canonical_email="alice@example.com",
                aliases=[],
                total_commits=10,
                verified_commits=-5,
            )

    def test_default_commits(self):
        cluster = IdentityCluster(
            github_node_id="MDQ6VXNlcjEyMzQ1",
            canonical_name="Alice Kim",
            canonical_email="alice@example.com",
            aliases=[],
        )
        assert cluster.total_commits == 0
        assert cluster.verified_commits == 0


# ---------------------------------------------------------------------------
# BlameLineAttribution
# ---------------------------------------------------------------------------


class TestBlameLineAttribution:
    def _make(
        self,
        *,
        is_move: bool = False,
        is_copy: bool = False,
        is_whitespace_only: bool = False,
    ) -> BlameLineAttribution:
        return BlameLineAttribution(
            file_path="src/foo.py",
            line_number=42,
            content="    return x + y",
            author_name="Alice",
            author_email="alice@example.com",
            commit_sha="abc1234",
            is_move=is_move,
            is_copy=is_copy,
            is_whitespace_only=is_whitespace_only,
        )

    def test_creation(self):
        attr = self._make()
        assert attr.file_path == "src/foo.py"
        assert attr.line_number == 42
        assert attr.commit_sha == "abc1234"

    def test_meaningful_when_pure(self):
        attr = self._make(is_move=False, is_copy=False, is_whitespace_only=False)
        assert attr.is_meaningful_contribution is True

    def test_not_meaningful_when_move(self):
        attr = self._make(is_move=True)
        assert attr.is_meaningful_contribution is False

    def test_not_meaningful_when_copy(self):
        attr = self._make(is_copy=True)
        assert attr.is_meaningful_contribution is False

    def test_not_meaningful_when_whitespace(self):
        attr = self._make(is_whitespace_only=True)
        assert attr.is_meaningful_contribution is False

    def test_not_meaningful_when_all_flags(self):
        attr = self._make(is_move=True, is_copy=True, is_whitespace_only=True)
        assert attr.is_meaningful_contribution is False

    def test_line_number_ge1(self):
        # line_number=0 must be rejected (ge=1 constraint)
        with pytest.raises(ValidationError):
            BlameLineAttribution(
                file_path="src/foo.py",
                line_number=0,
                content="x",
                author_name="Alice",
                author_email="alice@example.com",
                commit_sha="abc1234",
                is_move=False,
                is_copy=False,
                is_whitespace_only=False,
            )

    def test_line_number_negative_rejected(self):
        # Negative line_number must also be rejected
        with pytest.raises(ValidationError):
            BlameLineAttribution(
                file_path="src/foo.py",
                line_number=-1,
                content="x",
                author_name="Alice",
                author_email="alice@example.com",
                commit_sha="abc1234",
                is_move=False,
                is_copy=False,
                is_whitespace_only=False,
            )

    def test_line_number_valid(self):
        attr = BlameLineAttribution(
            file_path="src/foo.py",
            line_number=1,
            content="x",
            author_name="Alice",
            author_email="alice@example.com",
            commit_sha="abc1234",
            is_move=False,
            is_copy=False,
            is_whitespace_only=False,
        )
        assert attr.line_number == 1


# ---------------------------------------------------------------------------
# PureContribution
# ---------------------------------------------------------------------------


class TestPureContribution:
    def _make(
        self,
        *,
        total_lines: int = 100,
        pure_logic_lines: int = 60,
        removed_imports: int = 10,
        removed_comments: int = 15,
        removed_config: int = 8,
        removed_generated: int = 7,
        function_bodies: list[str] | None = None,
    ) -> PureContribution:
        bodies = (
            ["def foo(): pass", "def bar(): return 1"]
            if function_bodies is None
            else function_bodies
        )
        return PureContribution(
            file_path="src/service.py",
            language="Python",
            total_lines=total_lines,
            pure_logic_lines=pure_logic_lines,
            removed_imports=removed_imports,
            removed_comments=removed_comments,
            removed_config=removed_config,
            removed_generated=removed_generated,
            function_bodies=bodies,
        )

    def test_creation(self):
        contrib = self._make()
        assert contrib.file_path == "src/service.py"
        assert contrib.language == "Python"
        assert contrib.total_lines == 100

    def test_purity_ratio(self):
        contrib = self._make(total_lines=100, pure_logic_lines=60)
        assert contrib.purity_ratio == pytest.approx(0.6)

    def test_purity_ratio_zero_total(self):
        contrib = self._make(total_lines=0, pure_logic_lines=0)
        assert contrib.purity_ratio == 0.0

    def test_purity_ratio_full(self):
        contrib = self._make(total_lines=50, pure_logic_lines=50)
        assert contrib.purity_ratio == pytest.approx(1.0)

    def test_noise_lines(self):
        contrib = self._make(
            removed_imports=10,
            removed_comments=15,
            removed_config=8,
            removed_generated=7,
        )
        assert contrib.noise_lines == 40  # 10 + 15 + 8 + 7

    def test_noise_lines_all_zero(self):
        contrib = self._make(
            removed_imports=0,
            removed_comments=0,
            removed_config=0,
            removed_generated=0,
        )
        assert contrib.noise_lines == 0

    def test_negative_total_lines_rejected(self):
        with pytest.raises(ValidationError):
            self._make(total_lines=-1)

    def test_negative_pure_logic_rejected(self):
        with pytest.raises(ValidationError):
            self._make(pure_logic_lines=-1)

    def test_negative_removed_fields_rejected(self):
        with pytest.raises(ValidationError):
            self._make(removed_imports=-1)

    def test_empty_function_bodies(self):
        contrib = self._make(function_bodies=[])
        assert contrib.function_bodies == []

    def test_function_bodies_stored(self):
        bodies = ["def foo(): pass", "def bar(): return 1"]
        contrib = self._make(function_bodies=bodies)
        assert contrib.function_bodies == bodies
