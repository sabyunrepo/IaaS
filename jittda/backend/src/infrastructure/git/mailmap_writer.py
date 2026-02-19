"""
MailmapWriter — .mailmap 파일 생성 및 적용.

MailmapEntry 도메인 모델 리스트를 받아 .mailmap 형식으로 변환하여 파일에 쓴다.
"""
from pathlib import Path

from domain.identity.models import MailmapEntry


class MailmapWriter:
    """도메인 MailmapEntry를 .mailmap 파일로 기록한다."""

    async def write(
        self,
        repo_path: Path,
        entries: list[MailmapEntry],
    ) -> Path:
        """MailmapEntry 리스트를 .mailmap 파일로 작성한다.

        .mailmap 형식:
            Canonical Name <canonical@email> Alias Name <alias@email>

        Args:
            repo_path: 저장소 루트 경로.
            entries: MailmapEntry 리스트.

        Returns:
            생성된 .mailmap 파일 경로.
        """
        mailmap_path = repo_path / ".mailmap"
        lines = [_format_entry(entry) for entry in entries]
        mailmap_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return mailmap_path

    async def read(self, repo_path: Path) -> list[MailmapEntry]:
        """기존 .mailmap 파일을 파싱하여 MailmapEntry 리스트로 반환한다."""
        mailmap_path = repo_path / ".mailmap"
        if not mailmap_path.exists():
            return []

        entries: list[MailmapEntry] = []
        for line in mailmap_path.read_text(encoding="utf-8").splitlines():
            entry = _parse_line(line)
            if entry:
                entries.append(entry)
        return entries


def _format_entry(entry: MailmapEntry) -> str:
    """MailmapEntry → .mailmap 한 줄 형식."""
    return (
        f"{entry.canonical} <{entry.canonical_email}> "
        f"{entry.alias_name} <{entry.alias_email}>"
    )


def _parse_line(line: str) -> MailmapEntry | None:
    """단일 .mailmap 라인을 MailmapEntry로 파싱한다.

    형식: Canonical Name <canonical@email> Alias Name <alias@email>
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # <email> 토큰 추출
    emails: list[str] = []
    parts = line.split("<")
    names: list[str] = []

    for i, part in enumerate(parts):
        if ">" in part:
            email, rest = part.split(">", 1)
            emails.append(email.strip())
            if rest.strip():
                names.append(rest.strip())
        elif i == 0 and part.strip():
            names.append(part.strip())

    if len(emails) < 2:
        return None

    canonical_name = names[0] if names else ""
    alias_name = names[1] if len(names) > 1 else ""

    from domain.identity.models import ConfidenceLevel

    return MailmapEntry(
        canonical=canonical_name,
        canonical_email=emails[0],
        alias_name=alias_name,
        alias_email=emails[1],
        confidence=ConfidenceLevel.MEDIUM,
    )
