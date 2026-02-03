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

    async def get_account_type(self, username: str) -> dict:
        """
        GitHub 계정 타입 확인 (User vs Organization)

        Returns:
            {
                "username": str,
                "type": "User" | "Organization" | "unknown",
                "name": str | None,
                "avatar_url": str | None,
                "error": str | None
            }
        """
        import httpx

        # 먼저 인증된 PyGithub 시도
        try:
            g = self._get_github()
            try:
                user = g.get_user(username)
                return {
                    "username": username,
                    "type": user.type,  # "User" or "Organization"
                    "name": user.name,
                    "avatar_url": user.avatar_url,
                    "bio": user.bio if hasattr(user, 'bio') else None,
                    "company": user.company if hasattr(user, 'company') else None,
                    "error": None,
                }
            except Exception:
                org = g.get_organization(username)
                return {
                    "username": username,
                    "type": "Organization",
                    "name": org.name,
                    "avatar_url": org.avatar_url,
                    "error": None,
                }
        except Exception as e:
            logger.warning(f"PyGithub failed for {username}: {e}, trying unauthenticated...")

        # Fallback: 인증 없이 공개 API 직접 호출
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.github.com/users/{username}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "username": username,
                        "type": data.get("type", "unknown"),
                        "name": data.get("name"),
                        "avatar_url": data.get("avatar_url"),
                        "bio": data.get("bio"),
                        "company": data.get("company"),
                        "error": None,
                    }
                elif resp.status_code == 404:
                    return {
                        "username": username,
                        "type": "unknown",
                        "name": None,
                        "avatar_url": None,
                        "error": "not_found",
                    }
                else:
                    logger.warning(f"GitHub API returned {resp.status_code} for {username}")
        except Exception as e2:
            logger.warning(f"Unauthenticated request also failed for {username}: {e2}")

        return {
            "username": username,
            "type": "unknown",
            "name": None,
            "avatar_url": None,
            "error": "api_failed",
        }

    async def get_repo_contributors(self, url: str, limit: int = 5) -> list[dict]:
        """
        레포지토리 기여자 목록 조회 (기여도 순)

        Returns:
            [{"username": str, "contributions": int, "type": str}, ...]
        """
        import httpx

        path = self._parse_repo_path(url)
        if not path:
            return []

        # 먼저 PyGithub 시도
        try:
            g = self._get_github()
            repo = g.get_repo(path)
            contributors = []

            for contrib in repo.get_contributors()[:limit]:
                contributors.append({
                    "username": contrib.login,
                    "contributions": contrib.contributions,
                    "type": contrib.type,
                    "avatar_url": contrib.avatar_url,
                })

            return contributors
        except Exception as e:
            logger.warning(f"PyGithub failed for contributors {url}: {e}, trying unauthenticated...")

        # Fallback: 인증 없이 공개 API 직접 호출
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.github.com/repos/{path}/contributors",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    params={"per_page": limit},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "username": c.get("login"),
                            "contributions": c.get("contributions", 0),
                            "type": c.get("type", "User"),
                            "avatar_url": c.get("avatar_url"),
                        }
                        for c in data[:limit]
                    ]
        except Exception as e2:
            logger.warning(f"Unauthenticated contributors request also failed: {e2}")

        return []

    async def infer_candidate_username(
        self,
        github_urls: list[str],
        candidate_name: str | None = None,
    ) -> dict:
        """
        GitHub URL들에서 후보자 개인 username 확인

        ⚠️ 개인 계정(User) URL만 사용. Organization URL은 무시.
        임의 추론(기여자 분석)은 하지 않음 - 신뢰성 문제.

        Strategy:
        1. URL에서 owner 추출
        2. owner가 User인지 Organization인지 확인
        3. User 계정만 유효한 것으로 처리
        4. Organization URL은 건너뜀 (code_analysis 대상에서 제외)

        Returns:
            {
                "username": str | None,
                "confidence": "high" | "none",
                "source": str,
                "personal_repos": list[str],  # 개인 레포 URL만
                "skipped_org_repos": list[str],  # 건너뛴 조직 레포
            }
        """
        if not github_urls:
            return {
                "username": None,
                "confidence": "none",
                "source": "no_urls",
                "personal_repos": [],
                "skipped_org_repos": [],
            }

        personal_repos = []
        skipped_org_repos = []
        found_username = None

        for url in github_urls[:10]:  # 최대 10개 URL 처리
            owner = self._extract_owner(url)
            if not owner:
                continue

            account_info = await self.get_account_type(owner)

            if account_info["type"] == "User":
                # 개인 계정 → 유효
                personal_repos.append(url)
                if not found_username:
                    found_username = owner
                    logger.info(f"Found personal GitHub account: {owner} from {url}")

            elif account_info["type"] == "Organization":
                # 조직 계정 → 건너뜀 (임의 추론 안 함)
                skipped_org_repos.append(url)
                logger.info(f"Skipping organization repo (no inference): {owner} from {url}")

            else:
                # unknown (API 실패 등) → 건너뜀
                skipped_org_repos.append(url)
                logger.warning(f"Unknown account type for {owner}, skipping: {url}")

        if found_username and personal_repos:
            return {
                "username": found_username,
                "confidence": "high",
                "source": f"personal_repo:{personal_repos[0]}",
                "personal_repos": personal_repos,
                "skipped_org_repos": skipped_org_repos,
            }

        return {
            "username": None,
            "confidence": "none",
            "source": "no_personal_repos",
            "personal_repos": [],
            "skipped_org_repos": skipped_org_repos,
        }

    def _extract_owner(self, url: str) -> str | None:
        """GitHub URL에서 owner(첫 번째 경로) 추출"""
        match = re.match(r'https?://github\.com/([\w\-]+)', url)
        return match.group(1) if match else None

    def _names_match(self, name1: str, name2: str) -> bool:
        """
        두 이름이 매칭되는지 확인 (다양한 형식 지원)

        Examples:
            - "BYUN SANGHOON" ≈ "Sanghoon Byun" → True
            - "변상훈" ≈ "Sanghoon Byun" → False (다른 스크립트)
            - "John Doe" ≈ "John D." → True (부분 매칭)
        """
        if not name1 or not name2:
            return False

        # 정규화: 소문자, 여분 공백 제거
        n1 = " ".join(name1.lower().split())
        n2 = " ".join(name2.lower().split())

        # 1. 완전 일치
        if n1 == n2:
            return True

        # 2. 단어 집합 비교 (순서 무관)
        words1 = set(n1.split())
        words2 = set(n2.split())

        # 공통 단어가 2개 이상이면 매칭
        common = words1 & words2
        if len(common) >= 2:
            return True

        # 3. 한쪽이 다른쪽에 포함
        if n1 in n2 or n2 in n1:
            return True

        # 4. 성/이름 조합 체크 (동양 이름: 성+이름 vs 서양: 이름+성)
        # "byun sanghoon" vs "sanghoon byun"
        if len(words1) >= 2 and len(words2) >= 2:
            # 순서 뒤집어서 비교
            reversed_n1 = " ".join(reversed(list(words1)))
            reversed_n2 = " ".join(reversed(list(words2)))
            if n1 == reversed_n2 or n2 == reversed_n1:
                return True
            # 단어 집합이 동일 (순서만 다름)
            if words1 == words2:
                return True

        return False
