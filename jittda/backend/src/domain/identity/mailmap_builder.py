"""
동적 .mailmap 생성기

Git 저자 목록과 GitHub 프로필을 비교하여 동일인 여부를 판별하고
Git mailmap 엔트리를 생성한다.

4가지 매칭 규칙 (우선순위 순):
  1. noreply 패턴 → HIGH  (GitHub 공식 noreply 주소)
  2. 프로필 이메일 정확 매칭 → HIGH
  3. Levenshtein 이름 유사도 → MEDIUM  (threshold 이상)
  4. 이메일 도메인 매칭 → LOW  (무료 이메일 도메인 제외)

각 저자는 가장 높은 신뢰도 규칙 하나만 적용된다.
"""

from __future__ import annotations

from Levenshtein import ratio as levenshtein_ratio

from domain.identity.models import ConfidenceLevel, GitAuthor, GitHubProfile, MailmapEntry

# 무료 이메일 도메인 — 도메인 규칙에서 제외 (신호 강도 낮음)
_FREE_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "hotmail.com",
        "yahoo.com",
        "outlook.com",
    }
)

# 신뢰도 우선순위 (숫자 낮을수록 높은 우선순위)
_CONFIDENCE_PRIORITY: dict[ConfidenceLevel, int] = {
    ConfidenceLevel.HIGH: 0,
    ConfidenceLevel.MEDIUM: 1,
    ConfidenceLevel.LOW: 2,
}


def _is_noreply(email: str) -> bool:
    """GitHub noreply 패턴 여부 판별.

    패턴:
      - ``<id>+<login>@users.noreply.github.com``
      - ``noreply@<any>``
    """
    lower = email.lower()
    return lower.endswith("@users.noreply.github.com") or lower.startswith("noreply@")


def _domain_of(email: str) -> str:
    """이메일에서 도메인 추출. ``@`` 없으면 빈 문자열 반환."""
    parts = email.rsplit("@", 1)
    return parts[1].lower() if len(parts) == 2 else ""


def _make_entry(
    author: GitAuthor,
    profile: GitHubProfile,
    confidence: ConfidenceLevel,
) -> MailmapEntry:
    """MailmapEntry 생성 헬퍼."""
    return MailmapEntry(
        canonical=profile.name,
        canonical_email=profile.email,
        alias_name=author.name,
        alias_email=author.email,
        confidence=confidence,
    )


def _match_author(
    author: GitAuthor,
    profile: GitHubProfile,
    threshold: float,
) -> MailmapEntry | None:
    """단일 저자에 대해 4가지 규칙을 순서대로 적용하고 첫 매칭 엔트리를 반환.

    규칙은 우선순위 순으로 평가되며 첫 번째 매칭에서 즉시 반환한다.
    """
    # Rule 1: noreply 패턴 → HIGH
    if _is_noreply(author.email):
        return _make_entry(author, profile, ConfidenceLevel.HIGH)

    # Rule 2: 프로필 이메일 정확 매칭 (대소문자 무시) → HIGH
    if author.email.lower() == profile.email.lower():
        return _make_entry(author, profile, ConfidenceLevel.HIGH)

    # Rule 3: Levenshtein 이름 유사도 → MEDIUM
    similarity = levenshtein_ratio(author.name.lower(), profile.name.lower())
    if similarity >= threshold:
        return _make_entry(author, profile, ConfidenceLevel.MEDIUM)

    # Rule 4: 이메일 도메인 매칭 → LOW (무료 도메인 제외)
    author_domain = _domain_of(author.email)
    profile_domain = _domain_of(profile.email)
    if (
        author_domain
        and author_domain == profile_domain
        and author_domain not in _FREE_EMAIL_DOMAINS
    ):
        return _make_entry(author, profile, ConfidenceLevel.LOW)

    return None


def build_dynamic_mailmap(
    git_authors: list[GitAuthor],
    github_profile: GitHubProfile,
    github_node_id: str,
    threshold: float = 0.75,
) -> list[MailmapEntry]:
    """Git 저자 목록과 GitHub 프로필을 비교하여 mailmap 엔트리 목록을 생성한다.

    Args:
        git_authors: Git 커밋에서 추출한 저자 목록.
        github_profile: 매칭 대상 GitHub 프로필.
        github_node_id: GitHub 글로벌 노드 ID (현재 미사용, 확장을 위해 유지).
        threshold: Levenshtein 유사도 임계값. 기본값 0.75.

    Returns:
        매칭된 MailmapEntry 목록. 매칭되지 않은 저자는 제외.
        각 저자당 최대 하나의 엔트리.
    """
    entries: list[MailmapEntry] = []
    for author in git_authors:
        entry = _match_author(author, github_profile, threshold)
        if entry is not None:
            entries.append(entry)
    return entries


def deduplicate_entries(entries: list[MailmapEntry]) -> list[MailmapEntry]:
    """alias_email 기준으로 중복 엔트리를 제거하고 신뢰도가 가장 높은 것만 유지한다.

    Args:
        entries: 중복 가능성이 있는 MailmapEntry 목록.

    Returns:
        alias_email별로 신뢰도가 가장 높은 엔트리만 포함한 목록.
        입력 순서는 보장되지 않는다.
    """
    best: dict[str, MailmapEntry] = {}
    for entry in entries:
        key = entry.alias_email.lower()
        if key not in best:
            best[key] = entry
        else:
            existing_priority = _CONFIDENCE_PRIORITY[best[key].confidence]
            new_priority = _CONFIDENCE_PRIORITY[entry.confidence]
            if new_priority < existing_priority:
                best[key] = entry
    return list(best.values())
