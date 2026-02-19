"""
CloneManager — Git 저장소 shallow clone + sparse checkout.

subprocess/asyncio로 git CLI를 직접 호출한다.
GitPython/PyDriller 사용 금지 (DDD 원칙: CLI Wrapper only).
"""
import asyncio
import shutil
import tempfile
from pathlib import Path


class CloneManager:
    """Git 저장소를 shallow clone하고 sparse checkout을 적용한다."""

    def __init__(self, base_dir: str | None = None):
        self._base_dir = base_dir or tempfile.gettempdir()

    async def shallow_clone(
        self,
        repo_url: str,
        *,
        depth: int = 1,
        branch: str | None = None,
    ) -> Path:
        """Shallow clone을 수행하고 로컬 경로를 반환한다.

        Args:
            repo_url: Git 저장소 URL (https 또는 ssh).
            depth: clone 깊이 (기본 1).
            branch: 특정 브랜치만 clone. None이면 기본 브랜치.

        Returns:
            클론된 로컬 저장소 경로.

        Raises:
            RuntimeError: git clone 실패 시.
        """
        clone_dir = Path(self._base_dir) / _repo_name_from_url(repo_url)
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        cmd = ["git", "clone", "--depth", str(depth)]
        if branch:
            cmd += ["--branch", branch, "--single-branch"]
        cmd += [repo_url, str(clone_dir)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"git clone failed (exit {proc.returncode}): {stderr.decode().strip()}"
            )

        return clone_dir

    async def sparse_checkout(
        self,
        repo_path: Path,
        patterns: list[str],
    ) -> None:
        """기존 clone에 sparse-checkout을 적용하여 특정 경로만 체크아웃한다.

        Args:
            repo_path: 로컬 저장소 경로.
            patterns: sparse-checkout 패턴 (예: ["src/", "*.py"]).

        Raises:
            RuntimeError: sparse-checkout 설정 실패 시.
        """
        await self._run_git(repo_path, "sparse-checkout", "init", "--cone")
        await self._run_git(repo_path, "sparse-checkout", "set", *patterns)

    async def unshallow(self, repo_path: Path) -> None:
        """Shallow clone을 full history로 전환한다 (blame -C -C에 필요)."""
        await self._run_git(repo_path, "fetch", "--unshallow")

    def cleanup(self, repo_path: Path) -> None:
        """클론 디렉토리를 삭제한다."""
        if repo_path.exists():
            shutil.rmtree(repo_path)

    async def _run_git(self, repo_path: Path, *args: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            "git", "-C", str(repo_path), *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"git {' '.join(args)} failed (exit {proc.returncode}): "
                f"{stderr.decode().strip()}"
            )
        return stdout.decode()


def _repo_name_from_url(url: str) -> str:
    """URL에서 저장소 이름 추출. 예: https://github.com/user/repo.git → repo"""
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name
