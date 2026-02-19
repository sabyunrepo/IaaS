"""
Blame Filter 테스트

TDD: 테스트 먼저 작성 후 구현
filter_blame_lines — IdentityCluster 기반 blame 라인 필터링
aggregate_contributions — 파일 단위 PureContribution 집계
"""
import pytest

from domain.identity.blame_filter import aggregate_contributions, filter_blame_lines
from domain.identity.models import (
    BlameLineAttribution,
    ConfidenceLevel,
    IdentityCluster,
    MailmapEntry,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_cluster(
    canonical_email: str = "alice@example.com",
    alias_emails: list[str] | None = None,
) -> IdentityCluster:
    """IdentityCluster 헬퍼."""
    aliases = []
    for ae in (alias_emails or []):
        aliases.append(
            MailmapEntry(
                canonical="Alice Kim",
                canonical_email=canonical_email,
                alias_name="alice-alias",
                alias_email=ae,
                confidence=ConfidenceLevel.HIGH,
            )
        )
    return IdentityCluster(
        github_node_id="MDQ6VXNlcjEyMzQ1",
        canonical_name="Alice Kim",
        canonical_email=canonical_email,
        aliases=aliases,
    )


def make_line(
    *,
    author_email: str = "alice@example.com",
    file_path: str = "src/foo.py",
    line_number: int = 1,
    content: str = "    return x + y",
    is_move: bool = False,
    is_copy: bool = False,
    is_whitespace_only: bool = False,
) -> BlameLineAttribution:
    """BlameLineAttribution 헬퍼."""
    return BlameLineAttribution(
        file_path=file_path,
        line_number=line_number,
        content=content,
        author_name="Alice Kim",
        author_email=author_email,
        commit_sha="abc1234",
        is_move=is_move,
        is_copy=is_copy,
        is_whitespace_only=is_whitespace_only,
    )


# ---------------------------------------------------------------------------
# filter_blame_lines
# ---------------------------------------------------------------------------


class TestFilterBlameLines:
    def test_keeps_meaningful_line_with_canonical_email(self):
        """canonical_email + is_meaningful_contribution → 포함."""
        cluster = make_cluster(canonical_email="alice@example.com")
        line = make_line(author_email="alice@example.com")
        result = filter_blame_lines([line], cluster)
        assert result == [line]

    def test_filters_move_line(self):
        """is_move=True → 제외 (is_meaningful_contribution is False)."""
        cluster = make_cluster(canonical_email="alice@example.com")
        line = make_line(author_email="alice@example.com", is_move=True)
        result = filter_blame_lines([line], cluster)
        assert result == []

    def test_filters_copy_line(self):
        """is_copy=True → 제외."""
        cluster = make_cluster(canonical_email="alice@example.com")
        line = make_line(author_email="alice@example.com", is_copy=True)
        result = filter_blame_lines([line], cluster)
        assert result == []

    def test_filters_whitespace_line(self):
        """is_whitespace_only=True → 제외."""
        cluster = make_cluster(canonical_email="alice@example.com")
        line = make_line(author_email="alice@example.com", is_whitespace_only=True)
        result = filter_blame_lines([line], cluster)
        assert result == []

    def test_filters_other_author(self):
        """cluster에 속하지 않는 저자 → 제외."""
        cluster = make_cluster(canonical_email="alice@example.com")
        line = make_line(author_email="bob@example.com")
        result = filter_blame_lines([line], cluster)
        assert result == []

    def test_matches_alias_email(self):
        """alias_email로 작성된 라인 → 포함."""
        cluster = make_cluster(
            canonical_email="alice@example.com",
            alias_emails=["alice@old.example.com"],
        )
        line = make_line(author_email="alice@old.example.com")
        result = filter_blame_lines([line], cluster)
        assert result == [line]

    def test_empty_input(self):
        """빈 리스트 입력 → 빈 리스트 반환."""
        cluster = make_cluster()
        result = filter_blame_lines([], cluster)
        assert result == []

    def test_mixed_lines(self):
        """의미 있는 라인만 필터링 — 복합 케이스."""
        cluster = make_cluster(
            canonical_email="alice@example.com",
            alias_emails=["alice@old.example.com"],
        )
        kept_1 = make_line(author_email="alice@example.com", line_number=1)
        kept_2 = make_line(author_email="alice@old.example.com", line_number=2)
        dropped_move = make_line(author_email="alice@example.com", line_number=3, is_move=True)
        dropped_other = make_line(author_email="bob@example.com", line_number=4)
        dropped_ws = make_line(author_email="alice@example.com", line_number=5, is_whitespace_only=True)

        result = filter_blame_lines(
            [kept_1, kept_2, dropped_move, dropped_other, dropped_ws], cluster
        )
        assert result == [kept_1, kept_2]

    def test_multiple_aliases(self):
        """여러 alias 이메일 모두 매칭."""
        cluster = make_cluster(
            canonical_email="alice@example.com",
            alias_emails=["alice@work.com", "alice@personal.com"],
        )
        line_work = make_line(author_email="alice@work.com", line_number=1)
        line_personal = make_line(author_email="alice@personal.com", line_number=2)
        result = filter_blame_lines([line_work, line_personal], cluster)
        assert result == [line_work, line_personal]

    def test_preserves_order(self):
        """라인 순서 보존."""
        cluster = make_cluster(canonical_email="alice@example.com")
        lines = [
            make_line(author_email="alice@example.com", line_number=i)
            for i in range(1, 6)
        ]
        result = filter_blame_lines(lines, cluster)
        assert result == lines
        assert [r.line_number for r in result] == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# aggregate_contributions
# ---------------------------------------------------------------------------


class TestAggregateContributions:
    def test_groups_by_file(self):
        """같은 file_path 라인들 → 하나의 PureContribution."""
        lines = [
            make_line(file_path="src/foo.py", line_number=1),
            make_line(file_path="src/foo.py", line_number=2),
            make_line(file_path="src/foo.py", line_number=3),
        ]
        result = aggregate_contributions(lines, language="Python")
        assert len(result) == 1
        assert result[0].file_path == "src/foo.py"

    def test_multiple_files(self):
        """다른 file_path → 각각의 PureContribution."""
        lines = [
            make_line(file_path="src/foo.py", line_number=1),
            make_line(file_path="src/bar.py", line_number=1),
            make_line(file_path="src/foo.py", line_number=2),
        ]
        result = aggregate_contributions(lines, language="Python")
        file_paths = {c.file_path for c in result}
        assert file_paths == {"src/foo.py", "src/bar.py"}

    def test_total_lines_count(self):
        """total_lines == 해당 파일의 blame 라인 수."""
        lines = [
            make_line(file_path="src/foo.py", line_number=1),
            make_line(file_path="src/foo.py", line_number=2),
            make_line(file_path="src/foo.py", line_number=3),
        ]
        result = aggregate_contributions(lines, language="Python")
        assert result[0].total_lines == 3

    def test_pure_logic_lines_equals_total_before_semantic_pruning(self):
        """시맨틱 프루닝 전: pure_logic_lines == total_lines."""
        lines = [
            make_line(file_path="src/foo.py", line_number=i)
            for i in range(1, 6)
        ]
        result = aggregate_contributions(lines, language="Python")
        assert result[0].pure_logic_lines == result[0].total_lines == 5

    def test_removed_fields_all_zero_before_semantic_pruning(self):
        """시맨틱 프루닝 전: removed_* 모두 0."""
        lines = [make_line(file_path="src/foo.py", line_number=1)]
        result = aggregate_contributions(lines, language="Python")
        c = result[0]
        assert c.removed_imports == 0
        assert c.removed_comments == 0
        assert c.removed_config == 0
        assert c.removed_generated == 0

    def test_language_set_correctly(self):
        """language 파라미터 → PureContribution.language에 반영."""
        lines = [make_line(file_path="src/foo.py", line_number=1)]
        result = aggregate_contributions(lines, language="TypeScript")
        assert result[0].language == "TypeScript"

    def test_function_bodies_empty_before_semantic_pruning(self):
        """시맨틱 프루닝 전: function_bodies는 빈 리스트."""
        lines = [make_line(file_path="src/foo.py", line_number=1)]
        result = aggregate_contributions(lines, language="Python")
        assert result[0].function_bodies == []

    def test_empty_input(self):
        """빈 라인 리스트 → 빈 결과."""
        result = aggregate_contributions([], language="Python")
        assert result == []

    def test_single_line_file(self):
        """단일 라인 파일 → total_lines=1."""
        lines = [make_line(file_path="src/single.py", line_number=1)]
        result = aggregate_contributions(lines, language="Python")
        assert len(result) == 1
        assert result[0].total_lines == 1
        assert result[0].pure_logic_lines == 1

    def test_per_file_line_counts(self):
        """파일별 라인 수 집계 정확성."""
        lines = [
            make_line(file_path="src/foo.py", line_number=1),
            make_line(file_path="src/foo.py", line_number=2),
            make_line(file_path="src/bar.py", line_number=1),
        ]
        result = aggregate_contributions(lines, language="Go")
        by_file = {c.file_path: c for c in result}
        assert by_file["src/foo.py"].total_lines == 2
        assert by_file["src/bar.py"].total_lines == 1
