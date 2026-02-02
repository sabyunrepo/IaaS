"""
backend/app/services/github_service.py
GitHub API 서비스 (PyGithub 기반)
"""
import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubService:
    """GitHub API를 통한 레포 메타데이터 조회"""

    def __init__(self, token: str | None = None):
        self.token = token or settings.GITHUB_TOKEN

    def _get_github(self):
        from github import Github
        return Github(self.token) if self.token else Github()

    def _parse_repo_path(self, url: str) -> str | None:
        """GitHub URL에서 owner/repo 추출"""
        match = re.match(r'https?://github\.com/([\w\-]+/[\w\-\.]+)', url)
        if match:
            return match.group(1).rstrip(".")
        return None

    async def get_repo_info(self, url: str) -> dict:
        """레포 기본 정보 조회"""
        path = self._parse_repo_path(url)
        if not path:
            return {"url": url, "error": "invalid_url"}

        try:
            g = self._get_github()
            repo = g.get_repo(path)
            return {
                "url": url,
                "name": repo.name,
                "full_name": repo.full_name,
                "size": repo.size,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "default_branch": repo.default_branch,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "description": repo.description,
            }
        except Exception as e:
            logger.warning(f"Failed to get repo info for {url}: {e}")
            return {"url": url, "error": str(e)}

    async def get_repo_languages(self, url: str) -> dict[str, int]:
        """레포 언어 비율 조회 (bytes)"""
        path = self._parse_repo_path(url)
        if not path:
            return {}

        try:
            g = self._get_github()
            repo = g.get_repo(path)
            return dict(repo.get_languages())
        except Exception as e:
            logger.warning(f"Failed to get languages for {url}: {e}")
            return {}

    async def filter_repos_by_language(
        self,
        github_urls: list[str],
        target_languages: list[str],
        min_language_ratio: float = 0.3,
    ) -> list[dict]:
        """JD 기술스택과 매칭되는 레포 필터링"""
        target_set = {lang.lower() for lang in target_languages}
        matched = []

        for url in github_urls:
            languages = await self.get_repo_languages(url)
            if not languages:
                continue

            total_bytes = sum(languages.values())
            if total_bytes == 0:
                continue

            matched_bytes = sum(
                bytes_count for lang, bytes_count in languages.items()
                if lang.lower() in target_set
            )
            ratio = matched_bytes / total_bytes

            if ratio >= min_language_ratio:
                info = await self.get_repo_info(url)
                info["languages"] = languages
                info["jd_match_ratio"] = ratio
                matched.append(info)

        return matched
