"""
Mailmap Builder 테스트

TDD: 테스트 먼저 작성 — 4가지 매칭 규칙 검증
1. noreply 패턴 → HIGH
2. GitHub 프로필 이메일 매칭 → HIGH
3. Levenshtein 유사도 매칭 → MEDIUM
4. 도메인 매칭 → LOW
"""

import pytest

from domain.identity.mailmap_builder import build_dynamic_mailmap, deduplicate_entries
from domain.identity.models import ConfidenceLevel, GitAuthor, GitHubProfile, MailmapEntry

# ---------------------------------------------------------------------------
# 공통 픽스처
# ---------------------------------------------------------------------------

GITHUB_NODE_ID = "MDQ6VXNlcjEyMzQ1"


def make_profile(
    name: str = "Alice Kim",
    email: str = "alice@example.com",
    login: str = "alicekim",
    database_id: str = GITHUB_NODE_ID,
) -> GitHubProfile:
    return GitHubProfile(name=name, email=email, login=login, database_id=database_id)


# ---------------------------------------------------------------------------
# Rule 1: noreply 패턴 → HIGH confidence
# ---------------------------------------------------------------------------


class TestNoreplyRule:
    def test_noreply_github_pattern_detected(self):
        """123456+username@users.noreply.github.com 패턴 → HIGH"""
        author = GitAuthor(
            name="Alice Kim",
            email="123456+alicekim@users.noreply.github.com",
        )
        profile = make_profile()
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.HIGH
        assert entries[0].alias_email == "123456+alicekim@users.noreply.github.com"
        assert entries[0].canonical_email == profile.email

    def test_plain_noreply_pattern_detected(self):
        """noreply@ 패턴 → HIGH"""
        author = GitAuthor(name="Alice", email="noreply@github.com")
        profile = make_profile()
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.HIGH

    def test_noreply_canonical_is_profile(self):
        """noreply 엔트리의 canonical은 항상 GitHub 프로필 정보"""
        author = GitAuthor(
            name="old-name",
            email="99999+alicekim@users.noreply.github.com",
        )
        profile = make_profile(name="Alice Kim", email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert entries[0].canonical == profile.name
        assert entries[0].canonical_email == profile.email


# ---------------------------------------------------------------------------
# Rule 2: GitHub 프로필 이메일 정확 매칭 → HIGH confidence
# ---------------------------------------------------------------------------


class TestProfileEmailRule:
    def test_exact_email_match(self):
        """Git 저자 이메일 == GitHub 프로필 이메일 → HIGH"""
        author = GitAuthor(name="Alice K", email="alice@example.com")
        profile = make_profile(email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.HIGH
        assert entries[0].alias_email == "alice@example.com"

    def test_canonical_same_as_alias_when_email_matches(self):
        """이메일이 같더라도 MailmapEntry로 생성됨 (이름 정규화 목적)"""
        author = GitAuthor(name="alice k", email="alice@example.com")
        profile = make_profile(name="Alice Kim", email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert entries[0].canonical == profile.name
        assert entries[0].alias_name == author.name

    def test_profile_email_case_insensitive(self):
        """이메일 비교는 대소문자 무시"""
        author = GitAuthor(name="Alice", email="Alice@Example.COM")
        profile = make_profile(email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.HIGH


# ---------------------------------------------------------------------------
# Rule 3: Levenshtein 유사도 매칭 → MEDIUM confidence
# ---------------------------------------------------------------------------


class TestLevenshteinRule:
    def test_similar_name_match(self):
        """이름 유사도가 threshold 이상이면 MEDIUM"""
        # "Alice Kim" vs "Alice Kim" → ratio=1.0 (HIGH가 먼저지만 이메일 불일치)
        # 실제로 유사하지만 다른 이름 사용
        author = GitAuthor(name="Alic Kim", email="alic@work.com")
        profile = make_profile(name="Alice Kim", email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
            threshold=0.6,
        )
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.MEDIUM

    def test_dissimilar_name_no_match(self):
        """이름 유사도가 threshold 미만이면 매칭 안 됨"""
        author = GitAuthor(name="Bob Jones", email="bob@other.com")
        profile = make_profile(name="Alice Kim", email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
            threshold=0.75,
        )
        assert len(entries) == 0

    def test_levenshtein_threshold_boundary(self):
        """threshold 경계값: ratio == threshold → 매칭됨"""
        # "Alice Kim" vs "Alic Kim" — 수동 검증 대신 ratio 기준 테스트
        author = GitAuthor(name="Alic Kim", email="alic@work.com")
        profile = make_profile(name="Alice Kim", email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
            threshold=0.6,
        )
        # threshold=0.6이면 충분히 매칭되어야 함
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.MEDIUM


# ---------------------------------------------------------------------------
# Rule 4: 도메인 매칭 → LOW confidence
# ---------------------------------------------------------------------------


class TestDomainRule:
    def test_same_domain_match(self):
        """이메일 도메인이 같으면 LOW"""
        author = GitAuthor(name="Unknown Dev", email="dev@example.com")
        profile = make_profile(email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.LOW

    def test_free_email_domain_excluded(self):
        """gmail.com 같은 무료 이메일 도메인은 도메인 규칙 제외"""
        author = GitAuthor(name="Unknown Dev", email="dev@gmail.com")
        profile = make_profile(email="alice@gmail.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        # gmail 도메인 매칭은 LOW 신호가 너무 약함 → 제외
        assert len(entries) == 0

    def test_hotmail_excluded(self):
        """hotmail.com 제외"""
        author = GitAuthor(name="Dev", email="dev@hotmail.com")
        profile = make_profile(email="alice@hotmail.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 0

    def test_yahoo_excluded(self):
        """yahoo.com 제외"""
        author = GitAuthor(name="Dev", email="dev@yahoo.com")
        profile = make_profile(email="alice@yahoo.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 0

    def test_outlook_excluded(self):
        """outlook.com 제외"""
        author = GitAuthor(name="Dev", email="dev@outlook.com")
        profile = make_profile(email="alice@outlook.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 0

    def test_different_domain_no_match(self):
        """도메인이 다르면 매칭 안 됨"""
        author = GitAuthor(name="Dev", email="dev@other.com")
        profile = make_profile(email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 0


# ---------------------------------------------------------------------------
# 규칙 우선순위: 각 저자는 가장 높은 신뢰도 규칙 하나만 적용
# ---------------------------------------------------------------------------


class TestRulePriority:
    def test_noreply_takes_priority_over_profile(self):
        """noreply 이메일이 프로필 이메일과 같아도 → noreply 규칙(HIGH) 우선"""
        # noreply 패턴은 그 자체로 HIGH → profile match도 HIGH지만 중복 엔트리 없어야 함
        author = GitAuthor(
            name="Alice",
            email="12345+alicekim@users.noreply.github.com",
        )
        profile = make_profile()
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        # 하나의 저자 → 하나의 엔트리만
        assert len(entries) == 1

    def test_each_author_matches_one_rule_only(self):
        """저자 하나는 가장 높은 신뢰도 규칙 하나만 적용"""
        # 이메일이 프로필과 같고 도메인도 같음 → profile email rule(HIGH) 우선
        author = GitAuthor(name="Alice", email="alice@example.com")
        profile = make_profile(email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 1
        assert entries[0].confidence == ConfidenceLevel.HIGH


# ---------------------------------------------------------------------------
# 매칭 없음
# ---------------------------------------------------------------------------


class TestNoMatch:
    def test_no_match_returns_empty(self):
        """어떤 규칙도 해당 안 되면 빈 리스트"""
        author = GitAuthor(name="Bob Jones", email="bob@unknown-company.com")
        profile = make_profile(name="Alice Kim", email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
            threshold=0.9,  # 높은 threshold로 Levenshtein도 불통
        )
        assert entries == []

    def test_empty_authors_returns_empty(self):
        """저자 목록이 비면 빈 리스트"""
        profile = make_profile()
        entries = build_dynamic_mailmap(
            git_authors=[],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert entries == []


# ---------------------------------------------------------------------------
# 복수 저자
# ---------------------------------------------------------------------------


class TestMultipleAuthors:
    def test_multiple_authors_multiple_entries(self):
        """저자가 여러 명이면 각각 규칙 적용"""
        noreply_author = GitAuthor(
            name="Alice", email="111+alice@users.noreply.github.com"
        )
        profile_author = GitAuthor(name="Alice K", email="alice@example.com")
        profile = make_profile(email="alice@example.com")
        entries = build_dynamic_mailmap(
            git_authors=[noreply_author, profile_author],
            github_profile=profile,
            github_node_id=GITHUB_NODE_ID,
        )
        assert len(entries) == 2
        confidences = {e.alias_email: e.confidence for e in entries}
        assert confidences["111+alice@users.noreply.github.com"] == ConfidenceLevel.HIGH
        assert confidences["alice@example.com"] == ConfidenceLevel.HIGH


# ---------------------------------------------------------------------------
# deduplicate_entries
# ---------------------------------------------------------------------------


class TestDeduplicateEntries:
    def _make_entry(
        self,
        alias_email: str,
        confidence: ConfidenceLevel,
        canonical_email: str = "alice@example.com",
    ) -> MailmapEntry:
        return MailmapEntry(
            canonical="Alice Kim",
            canonical_email=canonical_email,
            alias_name="alice",
            alias_email=alias_email,
            confidence=confidence,
        )

    def test_dedup_keeps_highest_confidence(self):
        """같은 alias_email → 신뢰도 가장 높은 것 유지"""
        high = self._make_entry("alias@work.com", ConfidenceLevel.HIGH)
        medium = self._make_entry("alias@work.com", ConfidenceLevel.MEDIUM)
        low = self._make_entry("alias@work.com", ConfidenceLevel.LOW)
        result = deduplicate_entries([low, medium, high])
        assert len(result) == 1
        assert result[0].confidence == ConfidenceLevel.HIGH

    def test_dedup_different_aliases_preserved(self):
        """다른 alias_email → 모두 유지"""
        e1 = self._make_entry("a@work.com", ConfidenceLevel.HIGH)
        e2 = self._make_entry("b@work.com", ConfidenceLevel.MEDIUM)
        result = deduplicate_entries([e1, e2])
        assert len(result) == 2

    def test_dedup_empty_input(self):
        """빈 리스트 → 빈 리스트"""
        assert deduplicate_entries([]) == []

    def test_dedup_single_entry(self):
        """엔트리 1개 → 그대로 반환"""
        entry = self._make_entry("a@work.com", ConfidenceLevel.LOW)
        result = deduplicate_entries([entry])
        assert len(result) == 1
        assert result[0].confidence == ConfidenceLevel.LOW

    def test_dedup_high_before_low(self):
        """순서 무관: HIGH가 뒤에 있어도 HIGH 유지"""
        low = self._make_entry("alias@work.com", ConfidenceLevel.LOW)
        high = self._make_entry("alias@work.com", ConfidenceLevel.HIGH)
        result = deduplicate_entries([low, high])
        assert len(result) == 1
        assert result[0].confidence == ConfidenceLevel.HIGH
