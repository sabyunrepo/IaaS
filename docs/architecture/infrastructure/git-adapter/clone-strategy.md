---
title: "Clone Strategy"
type: note
layer: infrastructure
component: git-adapter
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[git-adapter/MOC]]"
linear: JIT-92
tags: [git, clone, sparse-checkout, shallow]
---

# Clone Strategy

> `infrastructure/git/clone_manager.py` 구현 설계.
> 디스크 I/O와 네트워크 비용을 최소화하면서 blame 분석에 필요한 히스토리만 가져온다.

## 핵심 전략

### 1. Shallow Clone (기본)

```bash
git clone --depth=500 --no-single-branch <url> <dest>
```

- `--depth=500`: 최근 500 커밋만 다운로드. blame 분석에 충분하고 네트워크 비용 최소화.
- `--no-single-branch`: 모든 브랜치 ref를 가져와 기본 브랜치 자동 감지 가능.
- 500 커밋 기준 근거: 대부분의 개인 프로젝트에서 2-3년치 히스토리에 해당. blame 정확도 저하 없음.

### 2. Sparse Checkout (대형 Monorepo 대응)

Monorepo나 불필요한 바이너리/에셋이 많은 레포에 적용한다.

```bash
git clone --depth=500 --filter=blob:none --sparse <url> <dest>
cd <dest>
git sparse-checkout set src/ lib/ app/ pkg/ cmd/
```

- `--filter=blob:none`: 파일 내용(blob)은 checkout 시점에만 다운로드 (partial clone).
- `sparse-checkout set`: 분석 대상 소스 디렉토리만 명시적으로 포함.

### 3. 히스토리 심화 (blame 정확도 향상)

Shallow clone 이후 blame 실행 중 `fatal: no such path ... in HEAD` 오류 발생 시:

```bash
git fetch --unshallow
```

이 작업은 비용이 크므로 blame 오류 감지 시에만 fallback으로 적용한다.

## 구현

```python
# infrastructure/git/clone_manager.py
import asyncio
import tempfile
from pathlib import Path

class CloneManager:
    """Git 레포지토리 shallow clone 관리자"""

    CLONE_DEPTH = 500
    SPARSE_THRESHOLD_MB = 100  # 레포 크기 기준 (GitHub API size 필드)

    async def shallow_clone(
        self,
        clone_url: str,
        repo_size_kb: int = 0,
        target_dirs: list[str] | None = None,
    ) -> Path:
        """레포를 shallow clone하고 작업 디렉토리 경로를 반환.

        Args:
            clone_url: HTTPS clone URL (토큰 인증 포함 가능)
            repo_size_kb: GitHub API의 size 필드 (KB). 0이면 크기 미확인.
            target_dirs: Sparse checkout 대상 디렉토리 목록. None이면 전체.

        Returns:
            Path: clone된 디렉토리 경로 (임시 디렉토리)

        Raises:
            CloneError: git 명령 실패 시
        """
        dest = Path(tempfile.mkdtemp(prefix="jittda_clone_"))
        use_sparse = (
            repo_size_kb > self.SPARSE_THRESHOLD_MB * 1024
            and target_dirs is not None
        )

        if use_sparse:
            await self._sparse_clone(clone_url, dest, target_dirs)
        else:
            await self._standard_clone(clone_url, dest)

        return dest

    async def _standard_clone(self, url: str, dest: Path) -> None:
        cmd = [
            "git", "clone",
            "--depth", str(self.CLONE_DEPTH),
            "--no-single-branch",
            url,
            str(dest),
        ]
        await self._run(cmd)

    async def _sparse_clone(
        self, url: str, dest: Path, target_dirs: list[str]
    ) -> None:
        # 1. filter=blob:none으로 메타데이터만 먼저 수신
        cmd = [
            "git", "clone",
            "--depth", str(self.CLONE_DEPTH),
            "--filter=blob:none",
            "--sparse",
            url,
            str(dest),
        ]
        await self._run(cmd)

        # 2. sparse-checkout 경로 설정
        set_cmd = ["git", "-C", str(dest), "sparse-checkout", "set"] + target_dirs
        await self._run(set_cmd)

    async def _run(self, cmd: list[str]) -> str:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise CloneError(
                f"git command failed: {' '.join(cmd)}\n{stderr.decode()}"
            )
        return stdout.decode()

    async def deepen_if_needed(self, clone_dir: Path) -> None:
        """blame 오류 감지 시 히스토리 전체 다운로드 (fallback)"""
        cmd = ["git", "-C", str(clone_dir), "fetch", "--unshallow"]
        await self._run(cmd)

    async def cleanup(self, clone_dir: Path) -> None:
        """분석 완료 후 임시 디렉토리 제거"""
        import shutil
        shutil.rmtree(clone_dir, ignore_errors=True)


class CloneError(Exception):
    pass
```

## 임시 디렉토리 생명주기

```
identity_resolver_node 진입
    → CloneManager.shallow_clone() → /tmp/jittda_clone_XXXX/
    → (blame, ast 분석 수행)
    → DB에 결과 저장 (Reference Passing)
    → CloneManager.cleanup()  ← finally 블록에서 보장
```

cleanup은 반드시 `finally` 블록에서 호출하여 분석 실패 시에도 디스크 누수를 방지한다.

```python
# application/nodes/identity_resolver.py
clone_dir = None
try:
    clone_dir = await clone_manager.shallow_clone(repo.clone_url, repo.size_kb)
    # ... 분석 ...
finally:
    if clone_dir:
        await clone_manager.cleanup(clone_dir)
```

## Depth 선택 근거

| depth | 평균 clone 시간 | blame 커버리지 | 추천 |
|-------|---------------|--------------|------|
| 50 | ~2s | 최근 변경분만 | X |
| 200 | ~5s | 1년치 | 소형 레포 |
| 500 | ~10s | 2-3년치 | **기본값** |
| full | ~30-120s | 전체 | fallback |

## 관련 문서

- [[blame-extraction]] — clone 후 blame 실행
- [[mailmap-generation]] — clone 직후 .mailmap 파일 작성
