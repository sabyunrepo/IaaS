"""
Git Adapter 테스트 — CloneManager, BlameRunner, MailmapWriter
"""
from pathlib import Path

import pytest

from domain.identity.models import ConfidenceLevel, MailmapEntry
from infrastructure.git.blame_runner import BlameRunner
from infrastructure.git.clone_manager import CloneManager, _repo_name_from_url
from infrastructure.git.mailmap_writer import MailmapWriter, _format_entry, _parse_line


# --- CloneManager ---


class TestRepoNameFromUrl:
    def test_https_url(self):
        assert _repo_name_from_url("https://github.com/user/repo.git") == "repo"

    def test_https_url_no_git_suffix(self):
        assert _repo_name_from_url("https://github.com/user/repo") == "repo"

    def test_trailing_slash(self):
        assert _repo_name_from_url("https://github.com/user/repo/") == "repo"

    def test_ssh_url(self):
        assert _repo_name_from_url("git@github.com:user/repo.git") == "repo"


class TestCloneManager:
    @pytest.mark.asyncio
    async def test_cleanup_removes_directory(self, tmp_path: Path):
        clone_dir = tmp_path / "test_repo"
        clone_dir.mkdir()
        (clone_dir / "file.txt").write_text("test")

        manager = CloneManager()
        manager.cleanup(clone_dir)

        assert not clone_dir.exists()

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_is_safe(self, tmp_path: Path):
        manager = CloneManager()
        manager.cleanup(tmp_path / "nonexistent")


# --- MailmapWriter ---


class TestFormatEntry:
    def test_basic_entry(self):
        entry = MailmapEntry(
            canonical="John Doe",
            canonical_email="john@company.com",
            alias_name="johnd",
            alias_email="john.d@gmail.com",
            confidence=ConfidenceLevel.HIGH,
        )
        result = _format_entry(entry)
        assert result == "John Doe <john@company.com> johnd <john.d@gmail.com>"


class TestParseLine:
    def test_valid_line(self):
        line = "John Doe <john@company.com> johnd <john.d@gmail.com>"
        entry = _parse_line(line)
        assert entry is not None
        assert entry.canonical == "John Doe"
        assert entry.canonical_email == "john@company.com"
        assert entry.alias_name == "johnd"
        assert entry.alias_email == "john.d@gmail.com"

    def test_comment_line(self):
        assert _parse_line("# comment") is None

    def test_empty_line(self):
        assert _parse_line("") is None
        assert _parse_line("  ") is None

    def test_single_email_returns_none(self):
        assert _parse_line("John <john@email.com>") is None


class TestMailmapWriter:
    @pytest.mark.asyncio
    async def test_write_and_read_roundtrip(self, tmp_path: Path):
        entries = [
            MailmapEntry(
                canonical="Alice",
                canonical_email="alice@company.com",
                alias_name="alice-old",
                alias_email="alice@gmail.com",
                confidence=ConfidenceLevel.HIGH,
            ),
            MailmapEntry(
                canonical="Bob",
                canonical_email="bob@company.com",
                alias_name="bobby",
                alias_email="bob123@yahoo.com",
                confidence=ConfidenceLevel.MEDIUM,
            ),
        ]

        writer = MailmapWriter()
        mailmap_path = await writer.write(tmp_path, entries)

        assert mailmap_path.exists()
        assert mailmap_path.name == ".mailmap"

        content = mailmap_path.read_text()
        assert "Alice <alice@company.com> alice-old <alice@gmail.com>" in content
        assert "Bob <bob@company.com> bobby <bob123@yahoo.com>" in content

    @pytest.mark.asyncio
    async def test_read_nonexistent_returns_empty(self, tmp_path: Path):
        writer = MailmapWriter()
        entries = await writer.read(tmp_path)
        assert entries == []


# --- BlameRunner ---


class TestBlameRunnerParsing:
    def test_parse_porcelain_basic(self):
        runner = BlameRunner()
        porcelain_output = (
            "abc1234567890123456789012345678901234567 1 1 1\n"
            "author Alice\n"
            "author-mail <alice@example.com>\n"
            "author-time 1700000000\n"
            "author-tz +0900\n"
            "committer Alice\n"
            "committer-mail <alice@example.com>\n"
            "committer-time 1700000000\n"
            "committer-tz +0900\n"
            "summary initial commit\n"
            "filename test.py\n"
            "\tprint('hello')\n"
        )
        result = runner._parse_porcelain(porcelain_output, "test.py")
        assert len(result) == 1
        assert result[0].author_name == "Alice"
        assert result[0].author_email == "alice@example.com"
        assert result[0].content == "print('hello')"
        assert result[0].line_number == 1
        assert result[0].file_path == "test.py"
        assert result[0].is_whitespace_only is False

    def test_parse_porcelain_whitespace_line(self):
        runner = BlameRunner()
        porcelain_output = (
            "abc1234567890123456789012345678901234567 1 1 1\n"
            "author Bob\n"
            "author-mail <bob@example.com>\n"
            "filename test.py\n"
            "\t   \n"
        )
        result = runner._parse_porcelain(porcelain_output, "test.py")
        assert len(result) == 1
        assert result[0].is_whitespace_only is True

    def test_parse_porcelain_empty_output(self):
        runner = BlameRunner()
        result = runner._parse_porcelain("", "test.py")
        assert result == []
