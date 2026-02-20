"""
BlameRunner — git blame -w -M -C -C 실행 및 파싱.

subprocess/asyncio로 git CLI를 직접 호출한다.
반환 타입은 항상 도메인 모델 BlameLineAttribution.
"""
import asyncio
import re
from pathlib import Path

from domain.identity.models import BlameLineAttribution

# git blame --porcelain 출력 파싱용 정규식
_HEADER_RE = re.compile(
    r"^([0-9a-f]{40}) (\d+) (\d+)(?: (\d+))?$"
)


class BlameRunner:
    """git blame를 실행하고 BlameLineAttribution 리스트를 반환한다."""

    async def run_git_blame(
        self,
        repo_path: Path,
        target_files: list[str],
        *,
        detect_moves: bool = True,
        detect_copies: bool = True,
        ignore_whitespace: bool = True,
    ) -> list[BlameLineAttribution]:
        """대상 파일들에 대해 git blame을 실행한다.

        Args:
            repo_path: 로컬 저장소 경로.
            target_files: blame 대상 파일 경로 리스트 (저장소 루트 기준 상대경로).
            detect_moves: -M 옵션 (파일 내 이동 탐지).
            detect_copies: -C -C 옵션 (파일 간 복사 탐지).
            ignore_whitespace: -w 옵션 (공백 변경 무시).

        Returns:
            BlameLineAttribution 리스트.
        """
        results: list[BlameLineAttribution] = []
        for file_path in target_files:
            attributions = await self._blame_file(
                repo_path,
                file_path,
                detect_moves=detect_moves,
                detect_copies=detect_copies,
                ignore_whitespace=ignore_whitespace,
            )
            results.extend(attributions)
        return results

    async def _blame_file(
        self,
        repo_path: Path,
        file_path: str,
        *,
        detect_moves: bool,
        detect_copies: bool,
        ignore_whitespace: bool,
    ) -> list[BlameLineAttribution]:
        cmd = ["git", "-C", str(repo_path), "blame", "--porcelain"]
        if ignore_whitespace:
            cmd.append("-w")
        if detect_moves:
            cmd.append("-M")
        if detect_copies:
            cmd += ["-C", "-C"]
        cmd.append(file_path)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            if "no such path" in error_msg.lower() or "fatal" in error_msg.lower():
                return []
            raise RuntimeError(f"git blame failed for {file_path}: {error_msg}")

        return self._parse_porcelain(stdout.decode(), file_path)

    def _parse_porcelain(
        self, output: str, file_path: str
    ) -> list[BlameLineAttribution]:
        """git blame --porcelain 출력을 파싱한다."""
        lines = output.split("\n")
        attributions: list[BlameLineAttribution] = []

        i = 0
        current_sha = ""
        current_line_no = 0
        author_name = ""
        author_email = ""

        while i < len(lines):
            line = lines[i]

            header_match = _HEADER_RE.match(line)
            if header_match:
                current_sha = header_match.group(1)
                current_line_no = int(header_match.group(3))
                i += 1
                continue

            if line.startswith("author "):
                author_name = line[7:]
            elif line.startswith("author-mail "):
                author_email = line[12:].strip("<>")
            elif line.startswith("\t"):
                content = line[1:]
                is_whitespace_only = content.strip() == ""
                # -M/-C 로 이동/복사된 라인은 boundary commit(0000...)으로 표시됨
                is_boundary = current_sha == "0" * 40

                attributions.append(
                    BlameLineAttribution(
                        file_path=file_path,
                        line_number=current_line_no,
                        content=content,
                        author_name=author_name,
                        author_email=author_email,
                        commit_sha=current_sha,
                        is_move=False,
                        is_copy=False,
                        is_whitespace_only=is_whitespace_only or is_boundary,
                    )
                )

            i += 1

        return attributions
