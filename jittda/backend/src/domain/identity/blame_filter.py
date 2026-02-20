"""
Blame Filter — IdentityCluster 기반 blame 라인 필터링

순수 함수 모듈. 외부 의존성 없음 (도메인 모델만 허용).
"""
from collections import defaultdict

from domain.identity.models import BlameLineAttribution, IdentityCluster, PureContribution


def filter_blame_lines(
    lines: list[BlameLineAttribution],
    cluster: IdentityCluster,
) -> list[BlameLineAttribution]:
    """
    blame 라인 필터링 — cluster에 속한 저자의 의미 있는 라인만 반환.

    포함 조건:
    1. author_email이 cluster의 known emails (canonical + 모든 alias) 중 하나
    2. line.is_meaningful_contribution is True (move/copy/whitespace 제외)

    순서 보존.
    """
    known_emails: set[str] = {cluster.canonical_email}
    for entry in cluster.aliases:
        known_emails.add(entry.alias_email)

    return [
        line
        for line in lines
        if line.author_email in known_emails and line.is_meaningful_contribution
    ]


def aggregate_contributions(
    lines: list[BlameLineAttribution],
    language: str,
) -> list[PureContribution]:
    """
    파일 단위 PureContribution 집계.

    blame 라인을 file_path 기준으로 그룹화하여 PureContribution 생성.

    시맨틱 프루닝 이전 단계이므로:
    - pure_logic_lines == total_lines (전체 라인 = 순수 로직 라인)
    - removed_* 모두 0
    - function_bodies 빈 리스트
    """
    grouped: dict[str, list[BlameLineAttribution]] = defaultdict(list)
    for line in lines:
        grouped[line.file_path].append(line)

    result: list[PureContribution] = []
    for file_path, file_lines in grouped.items():
        total = len(file_lines)
        result.append(
            PureContribution(
                file_path=file_path,
                language=language,
                total_lines=total,
                pure_logic_lines=total,
                removed_imports=0,
                removed_comments=0,
                removed_config=0,
                removed_generated=0,
                function_bodies=[],
            )
        )

    return result
