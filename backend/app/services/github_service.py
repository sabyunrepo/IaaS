"""
backend/app/services/github_service.py
GitHub API 서비스 (PyGithub 기반)
"""
import asyncio
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

    async def get_user_repos(self, profile_url: str, max_repos: int = 10) -> list[str]:
        """
        GitHub 프로필 URL에서 사용자의 레포지토리 목록 가져오기

        Args:
            profile_url: GitHub 프로필 URL (e.g., https://github.com/username)
            max_repos: 최대 가져올 레포 수 (기본 10개)

        Returns:
            레포지토리 URL 목록
        """
        import httpx

        # 프로필 URL에서 username 추출
        match = re.match(r'https?://github\.com/([\w\-]+)/?$', profile_url)
        if not match:
            logger.warning(f"Invalid GitHub profile URL: {profile_url}")
            return []

        username = match.group(1)

        # 먼저 PyGithub 시도
        try:
            g = self._get_github()
            user = g.get_user(username)
            repos = []
            for repo in user.get_repos(sort="pushed")[:max_repos]:
                if not repo.fork:  # fork된 레포 제외
                    repos.append(repo.html_url)
            return repos
        except Exception as e:
            logger.warning(f"PyGithub failed for user repos {username}: {e}, trying unauthenticated...")

        # Fallback: 인증 없이 공개 API 직접 호출
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.github.com/users/{username}/repos",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    params={"sort": "pushed", "per_page": max_repos},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        repo["html_url"] for repo in data
                        if not repo.get("fork", False)
                    ]
        except Exception as e2:
            logger.warning(f"Unauthenticated repos request also failed for {username}: {e2}")

        return []

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
        GitHub URL들에서 후보자 개인 username 확인 + 조직 레포 기여자 매칭

        Strategy:
        1. URL에서 owner 추출
        2. owner가 User인지 Organization인지 확인
        3. Organization → Contributors API로 candidate_name 매칭 (Stage 3)
        4. 매칭 성공 시 confidence: "medium", 실패 시 confidence: "low"

        Returns:
            {
                "username": str | None,
                "confidence": "high" | "medium" | "low" | "none",
                "source": str,
                "personal_repos": list[str],
                "skipped_org_repos": list[str],  # 하위 호환
                "org_repos": list[dict],  # [{"url", "candidate_username", "confidence"}]
            }
        """
        if not github_urls:
            return {
                "username": None,
                "confidence": "none",
                "source": "no_urls",
                "personal_repos": [],
                "skipped_org_repos": [],
                "org_repos": [],
            }

        personal_repos = []
        skipped_org_repos = []
        org_repos = []
        found_username = None

        for url in github_urls[:10]:  # 최대 10개 URL 처리
            owner = self._extract_owner(url)
            if not owner:
                continue

            account_info = await self.get_account_type(owner)

            if account_info["type"] == "User":
                # Stage 1-2: 개인 계정 → 유효
                personal_repos.append(url)
                if not found_username:
                    found_username = owner
                    logger.info(f"Found personal GitHub account: {owner} from {url}")

            elif account_info["type"] == "Organization":
                # Stage 3: 조직 레포 → Contributors API 매칭 시도
                skipped_org_repos.append(url)  # 하위 호환 유지
                org_entry = {
                    "url": url,
                    "candidate_username": None,
                    "confidence": "low",
                }

                if candidate_name:
                    try:
                        match = await self.infer_candidate_from_contributors(
                            repo_url=url,
                            candidate_name=candidate_name,
                        )
                        if match:
                            org_entry["candidate_username"] = match["username"]
                            org_entry["confidence"] = "medium"
                            org_entry["contributions"] = match["contributions"]
                            if not found_username:
                                found_username = match["username"]
                            logger.info(
                                f"Org repo contributor match: {match['username']} "
                                f"in {url} ({match['contributions']} contributions)"
                            )
                        else:
                            logger.info(
                                f"No contributor match for '{candidate_name}' in {url}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Contributor matching failed for {url}: {e}"
                        )
                else:
                    logger.info(
                        f"Skipping org repo (no candidate_name for matching): {url}"
                    )

                org_repos.append(org_entry)

            else:
                # unknown (API 실패 등) → 건너뜀
                skipped_org_repos.append(url)
                logger.warning(f"Unknown account type for {owner}, skipping: {url}")

        # 결과 결정
        if found_username and personal_repos:
            return {
                "username": found_username,
                "confidence": "high",
                "source": f"personal_repo:{personal_repos[0]}",
                "personal_repos": personal_repos,
                "skipped_org_repos": skipped_org_repos,
                "org_repos": org_repos,
            }

        if found_username and org_repos:
            matched_org = next(
                (r for r in org_repos if r["candidate_username"]), None
            )
            return {
                "username": found_username,
                "confidence": "medium",
                "source": f"org_contributor:{matched_org['url']}" if matched_org else "org_repo",
                "personal_repos": personal_repos,
                "skipped_org_repos": skipped_org_repos,
                "org_repos": org_repos,
            }

        return {
            "username": None,
            "confidence": "none",
            "source": "no_personal_repos",
            "personal_repos": [],
            "skipped_org_repos": skipped_org_repos,
            "org_repos": org_repos,
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

    async def infer_candidate_from_contributors(
        self,
        repo_url: str,
        candidate_name: str,
    ) -> dict | None:
        """
        레포 Contributors API에서 후보자 이름 매칭

        Args:
            repo_url: GitHub 레포 URL
            candidate_name: 후보자 이름 (LinkedIn full_name 등)

        Returns:
            매칭 시: {"username": str, "contributions": int}
            미매칭 시: None
        """
        import httpx

        contributors = await self.get_repo_contributors(repo_url, limit=10)
        if not contributors:
            return None

        for contrib in contributors:
            username = contrib.get("username")
            if not username:
                continue

            # GitHub 프로필에서 display name 조회
            try:
                g = self._get_github()
                user = g.get_user(username)
                display_name = user.name
            except Exception:
                # Fallback: 인증 없이 조회
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        resp = await client.get(
                            f"https://api.github.com/users/{username}",
                            headers={"Accept": "application/vnd.github.v3+json"},
                        )
                        if resp.status_code == 200:
                            display_name = resp.json().get("name")
                        else:
                            display_name = None
                except Exception:
                    display_name = None

            if display_name and self._names_match(candidate_name, display_name):
                logger.info(
                    f"Contributor match: {username} ({display_name}) "
                    f"≈ {candidate_name} in {repo_url}"
                )
                return {
                    "username": username,
                    "contributions": contrib.get("contributions", 0),
                }

        return None

    @staticmethod
    async def extract_git_authors(clone_dir: str, limit: int = 20) -> list[dict]:
        """
        git shortlog에서 커밋 작성자 목록 추출

        Args:
            clone_dir: shallow clone 디렉토리 경로
            limit: 최대 반환 수

        Returns:
            [{"name": str, "email": str, "commits": int}, ...]
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "-C", clone_dir, "shortlog", "-sne", "--all",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            if proc.returncode != 0:
                return []

            authors = []
            for line in stdout.decode("utf-8", errors="replace").strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                # 형식: "  123\tName <email>"
                match = re.match(r'(\d+)\t(.+?)\s+<(.+?)>', line)
                if match:
                    authors.append({
                        "name": match.group(2).strip(),
                        "email": match.group(3).strip(),
                        "commits": int(match.group(1)),
                    })
            return authors[:limit]
        except Exception as e:
            logger.warning(f"extract_git_authors failed for {clone_dir}: {e}")
            return []

    @staticmethod
    def resolve_author_by_identity(
        github_username: str,
        git_authors: list[dict],
    ) -> tuple[dict | None, str]:
        """
        GitHub username을 기반으로 git author 식별 (다중 휴리스틱).

        매칭 전략 (우선순위 순):
        1. name 완전 일치 (github_username == author.name)
        2. noreply email에서 GitHub username 추출 후 일치
        3. email 접두어 휴리스틱 (id@gmail.com, id@company.com → 접두어 비교)
        4. name에 username 포함 (substring match)
        5. 최다 커밋 작성자 fallback (3명 이하 개인 레포)

        Args:
            github_username: GitHub 프로필 username
            git_authors: extract_git_authors() 반환값

        Returns:
            (matched_author, match_method) or (None, "")
        """
        if not github_username or not git_authors:
            return None, ""

        username_lower = github_username.lower()

        # 1) name 완전 일치
        for a in git_authors:
            if a["name"].lower() == username_lower:
                return a, "name_exact"

        # 2) noreply email 매칭
        #    형태: "12345+username@users.noreply.github.com"
        for a in git_authors:
            email = a.get("email", "")
            m = re.match(r'(\d+\+)?(.+?)@users\.noreply\.github\.com', email)
            if m and m.group(2).lower() == username_lower:
                return a, "noreply_email"

        # 3) email 접두어 휴리스틱
        #    id@gmail.com, id@company.com 등에서 접두어가 username과 일치
        for a in git_authors:
            email = a.get("email", "")
            if email and "@" in email:
                prefix = email.split("@")[0].lower()
                # "user+tag@domain" 형태 정리
                if "+" in prefix:
                    prefix = prefix.split("+")[-1]
                if prefix == username_lower:
                    return a, "email_prefix"

        # 4) name에 username 포함 (substring match)
        #    예: username="sabyun", author.name="sabyun-dev"
        for a in git_authors:
            name_lower = a["name"].lower()
            if len(username_lower) >= 3 and (
                username_lower in name_lower or name_lower in username_lower
            ):
                return a, "name_substring"

        # 5) 최다 커밋 작성자 fallback (개인 레포 가정, 3명 이하)
        if len(git_authors) <= 3:
            top = max(git_authors, key=lambda a: a["commits"])
            return top, "top_committer_fallback"

        return None, ""

    async def match_candidate_from_git_log(
        self,
        clone_dir: str,
        candidate_name: str,
    ) -> dict | None:
        """
        git log 작성자에서 후보자 이름 매칭

        Args:
            clone_dir: shallow clone 디렉토리 경로
            candidate_name: 후보자 이름

        Returns:
            매칭 시: {"name": str, "email": str, "commits": int, "username": str | None}
            미매칭 시: None
        """
        authors = await self.extract_git_authors(clone_dir)
        if not authors:
            return None

        for author in authors:
            if self._names_match(candidate_name, author["name"]):
                # noreply email에서 username 추출 시도
                username = None
                email = author.get("email", "")
                noreply_match = re.match(
                    r'(\d+\+)?(.+?)@users\.noreply\.github\.com', email
                )
                if noreply_match:
                    username = noreply_match.group(2)

                logger.info(
                    f"Git log match: {author['name']} <{email}> "
                    f"≈ {candidate_name} (username={username})"
                )
                return {
                    "name": author["name"],
                    "email": email,
                    "commits": author["commits"],
                    "username": username,
                }

        return None
