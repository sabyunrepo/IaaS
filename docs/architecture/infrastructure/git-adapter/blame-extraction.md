---
title: "Blame Extraction"
type: note
layer: infrastructure
component: git-adapter
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[git-adapter/MOC]]"
linear: JIT-92
tags: [git, blame, identity-resolution, forensic]
---

# Blame Extraction

> `infrastructure/git/blame_runner.py` 구현 설계.
> `git blame -w -M -C -C --line-porcelain` 으로 지원자의 순수 로직 기여분만 추출한다.
> identity_cluster 기반 필터링은 `domain/identity/blame_filter.py`에 위임한다.

## Git Blame 플래그 선택 근거

| 플래그 | 의미 | 제외 대상 |
|--------|------|----------|
| `-w` | ignore whitespace | 공백/탭 수정만 한 커밋 |
| `-M` | detect moved lines within file | 파일 내 코드 이동 (리팩토링) |
| `-C` (첫 번째) | detect copied lines from other files in same commit | 동일 커밋의 타 파일 복사 |
| `-C` (두 번째) | extend copy detection across all commits | 모든 히스토리에서의 코드 복사 |
| `--line-porcelain` | 줄 단위 머신 파싱 가능 출력 | - |

`-C -C` 두 번 적용이 핵심이다. 단순 `-C` 한 번은 같은 커밋 내 복사만 감지하지만, `-C -C`는 전체 git 히스토리에서 복사 출처를 추적하여 "남의 코드 복사 후 커밋"을 탐지한다.

## --line-porcelain 출력 형식

```
<commit_sha> <orig_line> <final_line> <line_count>
author <name>
author-mail <email>
author-time <unix_timestamp>
author-tz <+HHMM>
committer <name>
committer-mail <email>
committer-time <unix_timestamp>
committer-tz <+HHMM>
summary <commit_message_first_line>
filename <file_name>
	<actual_line_content>
```

한 줄의 귀속 정보가 위 블록 형태로 반복된다. `\t`로 시작하는 줄이 실제 코드 내용이다.

## 구현

```python
# infrastructure/git/blame_runner.py
import asyncio
import re
from pathlib import Path
from domain.identity.models import BlameLineAttribution

class BlameRunner:
    """git blame -w -M -C -C 실행 및 파싱"""

    BLAME_FLAGS = ["-w", "-M", "-C", "-C", "--line-porcelain"]

    async def run_git_blame(
        self,
        clone_dir: Path,
        file_paths: list[str],
        mailmap_applied: bool = True,
    ) -> list[BlameLineAttribution]:
        """지정 파일 목록에 대해 blame을 실행하고 파싱 결과를 반환.

        Args:
            clone_dir: shallow clone된 레포 루트 경로
            file_paths: blame 대상 파일 경로 목록 (레포 기준 상대 경로)
            mailmap_applied: .mailmap이 이미 clone_dir에 작성되었는지 여부

        Returns:
            list[BlameLineAttribution]: 줄 단위 귀속 정보
        """
        results: list[BlameLineAttribution] = []

        for file_path in file_paths:
            lines = await self._blame_file(clone_dir, file_path)
            results.extend(lines)

        return results

    async def _blame_file(
        self, clone_dir: Path, file_path: str
    ) -> list[BlameLineAttribution]:
        cmd = [
            "git", "-C", str(clone_dir),
            "blame",
            *self.BLAME_FLAGS,
            "--",
            file_path,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(clone_dir),
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            stderr_text = stderr.decode()
            # shallow clone에서 히스토리 부족 오류 감지
            if "no such path" in stderr_text or "bad object" in stderr_text:
                raise BlameHistoryError(file_path, stderr_text)
            # 파일 없음(삭제된 파일) → 빈 결과 반환
            return []

        return self._parse_porcelain(file_path, stdout.decode())

    def _parse_porcelain(
        self, file_path: str, raw: str
    ) -> list[BlameLineAttribution]:
        """--line-porcelain 출력을 BlameLineAttribution 목록으로 변환"""
        lines: list[BlameLineAttribution] = []
        blocks = raw.split("\n")
        i = 0

        current: dict = {}
        while i < len(blocks):
            line = blocks[i]

            # 커밋 SHA 헤더 (40자 hex + 줄 번호 정보)
            if re.match(r"^[0-9a-f]{40} ", line):
                parts = line.split()
                current = {"commit_sha": parts[0]}
                i += 1
                continue

            if line.startswith("author "):
                current["author_name"] = line[7:]
            elif line.startswith("author-mail "):
                current["author_email"] = line[12:].strip("<>")
            elif line.startswith("filename "):
                current["filename"] = line[9:]
            elif line.startswith("\t"):
                # 실제 코드 내용 줄
                content = line[1:]  # leading \t 제거
                lines.append(BlameLineAttribution(
                    file_path=file_path,
                    line_number=len(lines) + 1,
                    content=content,
                    author_name=current.get("author_name", ""),
                    author_email=current.get("author_email", ""),
                    commit_sha=current.get("commit_sha", ""),
                    is_move=False,   # -M 감지는 별도 post-processing
                    is_copy=False,   # -C -C 감지는 별도 post-processing
                    is_whitespace_only=(content.strip() == ""),
                ))

            i += 1

        return lines


class BlameHistoryError(Exception):
    """shallow clone 히스토리 부족으로 blame 실패"""
    def __init__(self, file_path: str, detail: str):
        super().__init__(f"blame failed for {file_path}: {detail}")
        self.file_path = file_path
```

## identity_cluster 기반 필터링 연동

blame 결과의 필터링은 infrastructure가 아닌 domain에서 수행한다. `blame_runner`는 전체 귀속 라인을 반환하고, `domain/identity/blame_filter.py`가 identity_cluster와 교차하여 지원자 라인만 추린다.

```python
# application/nodes/identity_resolver.py (발췌)
blame_lines = await blame_runner.run_git_blame(
    clone_dir,
    target_files,
)
# domain 위임: 지원자 소유 라인만 필터
pure_lines = blame_filter.filter_by_cluster(blame_lines, identity_cluster)
```

`BlameFilter.filter_by_cluster()` 규칙:

```python
# domain/identity/blame_filter.py
def filter_by_cluster(
    lines: list[BlameLineAttribution],
    cluster: IdentityCluster,
) -> list[BlameLineAttribution]:
    """identity_cluster에 속하는 이메일/이름의 라인만 보존"""
    canonical_emails = {e.alias_email for e in cluster.aliases}
    canonical_emails.add(cluster.canonical_email)

    return [
        line for line in lines
        if line.author_email in canonical_emails
        and not line.is_whitespace_only
        and not line.is_move
        and not line.is_copy
    ]
```

## 에러 처리 전략

| 오류 상황 | 처리 방법 |
|----------|----------|
| shallow clone 히스토리 부족 | `CloneManager.deepen_if_needed()` 호출 후 재시도 |
| 파일 삭제/이름 변경 | 빈 list 반환, 다음 파일 계속 처리 |
| 바이너리 파일 | git이 자동으로 blame 거부 → 빈 list |
| 인코딩 오류 | `errors='replace'`로 디코딩, 해당 줄 건너뜀 |

## 관련 문서

- [[clone-strategy]] — 사전에 shallow clone 수행
- [[mailmap-generation]] — blame 실행 전 .mailmap 적용 필수
- [[domain/identity-resolution/MOC]] — blame_filter.filter_by_cluster() 로직
