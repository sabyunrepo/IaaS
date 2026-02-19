"""
Identity Resolver Worker (W2) — Git 저자 동일인 판별 + Blame 분석.

GitHub API → mailmap 빌드 → git blame 실행 → 순수 기여 필터링.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from application.states.forensic_state import ForensicState
from domain.identity.blame_filter import aggregate_contributions, filter_blame_lines
from domain.identity.mailmap_builder import build_dynamic_mailmap
from domain.identity.models import IdentityCluster
from infrastructure.git.blame_runner import BlameRunner
from infrastructure.git.mailmap_writer import MailmapWriter
from infrastructure.github.github_client import GitHubClient


async def identity_resolver_worker(state: ForensicState) -> dict[str, Any]:
    """Git 저자 Identity Resolution + Blame Attribution을 수행한다."""
    github_client = GitHubClient()
    blame_runner = BlameRunner()
    mailmap_writer = MailmapWriter()

    username = state.get("candidate_username")
    repo_paths = state.get("repo_local_paths", [])

    if not username or not repo_paths:
        return {
            "identity_cluster": None,
            "blame_attributions": [],
        }

    # 1. GitHub 프로필에서 canonical 정보 가져오기
    profile = await github_client.fetch_profile(username)
    node_id = await github_client.get_node_id(username)

    # 2. 각 리포에서 git 저자 추출 + mailmap 생성
    from domain.identity.models import GitAuthor
    from infrastructure.git.clone_manager import CloneManager

    all_blame_lines = []
    total_commits = 0
    verified_commits = 0

    for repo_path_str in repo_paths:
        repo_path = Path(repo_path_str)
        if not repo_path.exists():
            continue

        # Git log에서 저자 추출 (CloneManager의 기능이 아니므로 직접 수행)
        import subprocess

        result = subprocess.run(
            ["git", "log", "--format=%aN|%aE", "--no-merges"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        git_authors = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                name, email = line.split("|", 1)
                git_authors.append(GitAuthor(name=name.strip(), email=email.strip()))
                total_commits += 1

        # 3. Dynamic mailmap 빌드
        mailmap_entries = build_dynamic_mailmap(git_authors, profile, node_id)

        # 4. Mailmap 파일 작성
        if mailmap_entries:
            await mailmap_writer.write(repo_path, mailmap_entries)

        # 5. Blame 실행
        # 소스 파일 목록 수집
        src_files = []
        for ext in ("*.py", "*.js", "*.ts", "*.java", "*.go"):
            src_files.extend(
                str(p.relative_to(repo_path)) for p in repo_path.rglob(ext) if ".git" not in str(p)
            )
        if not src_files:
            continue

        blame_lines = await blame_runner.run_git_blame(repo_path, src_files[:50])

        # 6. 후보자 기여분만 필터링
        cluster = IdentityCluster(
            github_node_id=node_id,
            canonical_name=profile.name,
            canonical_email=profile.email,
            aliases=mailmap_entries,
            total_commits=total_commits,
            verified_commits=0,
        )
        filtered_lines = filter_blame_lines(blame_lines, cluster)
        verified_commits += len(filtered_lines)
        all_blame_lines.extend([line.model_dump() for line in filtered_lines])

    # 최종 클러스터 구성
    final_cluster = IdentityCluster(
        github_node_id=node_id,
        canonical_name=profile.name,
        canonical_email=profile.email,
        aliases=[],
        total_commits=total_commits,
        verified_commits=verified_commits,
    )

    return {
        "identity_cluster": final_cluster.model_dump(),
        "blame_attributions": all_blame_lines,
    }
