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
        """JD 기술스택과 매칭되는 레포 필터링 (하위 호환)"""
        return await self.select_relevant_repos(
            github_urls=github_urls,
            target_languages=target_languages,
            min_language_ratio=min_language_ratio,
        )

    async def select_relevant_repos(
        self,
        github_urls: list[str],
        target_languages: list[str],
        min_language_ratio: float = 0.2,
        jd_text: str = "",
        jd_keywords: list[str] | None = None,
    ) -> list[dict]:
        """JD 기반 레포 관련성 스코어링 + 필터링 (JIT-49)

        스코어링 공식:
            score = (lang_match × 0.3) + (size_activity × 0.3) + (jd_keyword × 0.4)

        Args:
            github_urls: 레포 URL 목록
            target_languages: JD 기술스택 언어 목록
            min_language_ratio: 최소 언어 비율 (하위 호환)
            jd_text: JD 전체 텍스트 (키워드 매칭용)
            jd_keywords: JD 키워드 목록 (없으면 jd_text에서 추출)

        Returns:
            관련성 높은 순으로 정렬된 레포 목록
        """
        target_set = {lang.lower() for lang in target_languages}
        scored_repos = []

        # JD 키워드 추출 (jd_text에서)
        if not jd_keywords and jd_text:
            jd_keywords = self._extract_jd_keywords(jd_text)

        for url in github_urls:
            languages = await self.get_repo_languages(url)
            if not languages:
                continue

            total_bytes = sum(languages.values())
            if total_bytes == 0:
                continue

            info = await self.get_repo_info(url)
            if info.get("error"):
                continue

            # 최소 레포 크기 필터 (100KB 이하 제외)
            repo_size = info.get("size", 0) or 0
            if repo_size < 100:
                logger.debug(f"Skipping small repo ({repo_size}KB): {url}")
                continue

            # 스코어링
            score = self._score_repo_relevance(
                info=info,
                languages=languages,
                total_bytes=total_bytes,
                target_set=target_set,
                jd_keywords=jd_keywords or [],
            )

            if score >= 0.2:
                info["languages"] = languages
                info["jd_match_ratio"] = score
                info["relevance_score"] = score
                scored_repos.append(info)

        # 관련성 높은 순 정렬
        scored_repos.sort(key=lambda r: r.get("relevance_score", 0), reverse=True)

        logger.info(
            f"Repo selection: {len(github_urls)} candidates → "
            f"{len(scored_repos)} relevant (target_languages={target_languages})"
        )

        return scored_repos

    @staticmethod
    def _score_repo_relevance(
        info: dict,
        languages: dict,
        total_bytes: int,
        target_set: set[str],
        jd_keywords: list[str],
    ) -> float:
        """레포 관련성 점수 계산 (JIT-49)

        score = (lang_match × 0.3) + (size_activity × 0.3) + (jd_keyword × 0.4)
        """
        # 1. 언어 매칭 점수 (0.0-1.0)
        matched_bytes = sum(
            bytes_count for lang, bytes_count in languages.items()
            if lang.lower() in target_set
        )
        lang_match = matched_bytes / total_bytes if total_bytes > 0 else 0.0

        # 2. 크기/활동 점수 (0.0-1.0)
        repo_size = info.get("size", 0) or 0
        size_score = min(repo_size / 5000, 1.0)
        stars = info.get("stars", 0) or 0
        forks = info.get("forks", 0) or 0
        activity_score = min((stars + forks * 2) / 50, 1.0)
        size_activity = size_score * 0.7 + activity_score * 0.3

        # 3. JD 키워드 매칭 점수 (0.0-1.0)
        jd_keyword_score = 0.0
        if jd_keywords:
            description = (info.get("description") or "").lower()
            repo_name = (info.get("name") or "").lower()
            searchable = f"{description} {repo_name}"

            matched_keywords = sum(
                1 for kw in jd_keywords
                if kw.lower() in searchable
            )
            jd_keyword_score = min(matched_keywords / max(len(jd_keywords), 1), 1.0)

        score = (lang_match * 0.3) + (size_activity * 0.3) + (jd_keyword_score * 0.4)
        return round(score, 3)

    @staticmethod
    def _extract_jd_keywords(jd_text: str) -> list[str]:
        """JD 텍스트에서 기술 키워드 추출"""
        tech_keywords = {
            "python", "javascript", "typescript", "java", "go", "rust", "ruby",
            "react", "vue", "angular", "next.js", "nuxt", "svelte",
            "node.js", "express", "fastapi", "django", "flask", "spring",
            "tensorflow", "pytorch", "langchain", "llm", "rag",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "graphql", "rest", "grpc", "microservices",
            "temporal", "kafka", "rabbitmq", "celery",
            "ci/cd", "github actions", "jenkins",
            "machine learning", "deep learning", "nlp", "computer vision",
        }
        jd_lower = jd_text.lower()
        return [kw for kw in tech_keywords if kw in jd_lower]

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
        repo_name: str = "",
        github_profile: dict | None = None,
    ) -> "AuthorIdentityResult":
        """
        GitHub username을 기반으로 git author 식별 (8단계 휴리스틱).

        매칭 전략 (우선순위 순):
        0. github_profile — GitHub API profile name/email 매칭 (confidence=0.95)
        1. name_exact — name 완전 일치 (confidence=1.0)
        2. noreply_email — noreply email 매칭 (confidence=0.95)
        3. email_prefix — email 접두어 일치 (confidence=0.9)
        4. name_substring — name에 username 포함, ≥3자 (confidence=0.7)
        5. email_domain_match — 동일 커스텀 도메인 이메일 (confidence=0.6)
        6. commit_pattern_analysis — 커밋 빈도/점유율 분석 (confidence=0.5)
        7. top_committer_fallback — 삭제 (JIT-35)

        Args:
            github_username: GitHub 프로필 username
            git_authors: extract_git_authors() 반환값
            repo_name: 레포 이름 (cross-repo 검증용)
            github_profile: GitHub API /users/{username} 응답 (name, email)

        Returns:
            AuthorIdentityResult (matches 배열 + best_match)
        """
        from app.models.author_identity import AuthorIdentityResult, AuthorMatch

        if not github_username or not git_authors:
            return AuthorIdentityResult()

        username_lower = github_username.lower()
        matches: list[AuthorMatch] = []
        repos = [repo_name] if repo_name else []

        # 0) JIT-72: GitHub API profile name/email 크로스 매칭
        if github_profile:
            profile_name = (github_profile.get("name") or "").strip().lower()
            profile_email = (github_profile.get("email") or "").strip().lower()

            for a in git_authors:
                matched = False
                # profile email과 git author email 일치 (가장 강력한 신호)
                if profile_email and a.get("email", "").lower() == profile_email:
                    matched = True
                # profile name과 git author name 일치 (대소문자 무시)
                elif profile_name and a["name"].lower() == profile_name:
                    matched = True

                if matched and not any(am.name == a["name"] and am.email == a.get("email", "") for am in matches):
                    matches.append(AuthorMatch(
                        name=a["name"], email=a.get("email", ""),
                        commits=a["commits"], confidence=0.95,
                        method="github_profile", repos_matched=repos,
                    ))

        # 1) name 완전 일치
        for a in git_authors:
            if a["name"].lower() == username_lower:
                matches.append(AuthorMatch(
                    name=a["name"], email=a.get("email", ""),
                    commits=a["commits"], confidence=1.0,
                    method="name_exact", repos_matched=repos,
                ))

        # 2) noreply email 매칭
        #    형태: "12345+username@users.noreply.github.com"
        for a in git_authors:
            email = a.get("email", "")
            m = re.match(r'(\d+\+)?(.+?)@users\.noreply\.github\.com', email)
            if m and m.group(2).lower() == username_lower:
                if not any(am.name == a["name"] and am.email == email for am in matches):
                    matches.append(AuthorMatch(
                        name=a["name"], email=email,
                        commits=a["commits"], confidence=0.95,
                        method="noreply_email", repos_matched=repos,
                    ))

        # 3) email 접두어 휴리스틱
        for a in git_authors:
            email = a.get("email", "")
            if email and "@" in email:
                prefix = email.split("@")[0].lower()
                if "+" in prefix:
                    prefix = prefix.split("+")[-1]
                if prefix == username_lower:
                    if not any(am.name == a["name"] and am.email == email for am in matches):
                        matches.append(AuthorMatch(
                            name=a["name"], email=email,
                            commits=a["commits"], confidence=0.9,
                            method="email_prefix", repos_matched=repos,
                        ))

        # 4) name substring 매칭 (≥3자)
        for a in git_authors:
            name_lower = a["name"].lower()
            if len(username_lower) >= 3 and (
                username_lower in name_lower or name_lower in username_lower
            ):
                if not any(am.name == a["name"] for am in matches):
                    matches.append(AuthorMatch(
                        name=a["name"], email=a.get("email", ""),
                        commits=a["commits"], confidence=0.7,
                        method="name_substring", repos_matched=repos,
                    ))

        # 5) email domain 매칭 (동일 커스텀 도메인)
        #    gmail.com 등 공개 도메인은 제외
        public_domains = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "users.noreply.github.com", "naver.com", "daum.net",
            "protonmail.com", "icloud.com", "me.com",
            "github.com", "localhost",
        }
        # 인프라/자동생성 도메인 TLD 차단
        infra_tlds = {".internal", ".local", ".localdomain", ".arpa"}

        def _is_infra_domain(domain: str) -> bool:
            return any(domain.endswith(tld) for tld in infra_tlds)

        candidate_domains: set[str] = set()
        for a in git_authors:
            email = a.get("email", "")
            if email and "@" in email:
                domain = email.split("@")[1].lower()
                if domain not in public_domains and not _is_infra_domain(domain):
                    candidate_domains.add(domain)

        if candidate_domains:
            for a in git_authors:
                email = a.get("email", "")
                if email and "@" in email:
                    domain = email.split("@")[1].lower()
                    if domain in candidate_domains and domain not in public_domains:
                        if not any(am.name == a["name"] for am in matches):
                            matches.append(AuthorMatch(
                                name=a["name"], email=email,
                                commits=a["commits"], confidence=0.6,
                                method="email_domain_match", repos_matched=repos,
                            ))

        # 6) commit_pattern_analysis — 커밋 점유율 기반
        #    총 커밋의 50% 이상 + 절대 커밋 수 10+ 인 author
        total_commits = sum(a["commits"] for a in git_authors)
        if total_commits > 0:
            for a in git_authors:
                share = a["commits"] / total_commits
                if share >= 0.5 and a["commits"] >= 10:
                    if not any(am.name == a["name"] for am in matches):
                        matches.append(AuthorMatch(
                            name=a["name"], email=a.get("email", ""),
                            commits=a["commits"], confidence=0.5,
                            method="commit_pattern_analysis", repos_matched=repos,
                        ))

        # best_match = identity-linked 매칭만 (commit_pattern_analysis 제외)
        #   commit_pattern_analysis는 username 연관 없이 커밋 점유율만 보는
        #   약한 신호이므로, best_match 후보에서 제외하여 fork 방어
        identity_matches = [
            m for m in matches if m.method != "commit_pattern_analysis"
        ]
        best = (
            max(identity_matches, key=lambda m: (m.confidence, m.commits))
            if identity_matches
            else None
        )

        return AuthorIdentityResult(
            matches=matches,
            best_match=best,
            cross_repo_verified=False,
        )

    @staticmethod
    def verify_cross_repo(
        results_by_repo: dict[str, "AuthorIdentityResult"],
    ) -> "AuthorIdentityResult":
        """
        복수 레포의 AuthorIdentityResult를 종합하여 cross-repo 검증 수행.

        - 2+ 레포에서 동일 author 매칭 → confidence *= 1.3 (cap 1.0)
        - 1개 레포에서만 매칭 + 다른 레포 기여 0 → confidence *= 0.5

        Args:
            results_by_repo: {repo_name: AuthorIdentityResult}

        Returns:
            종합 AuthorIdentityResult
        """
        from app.models.author_identity import AuthorIdentityResult, AuthorMatch

        if not results_by_repo:
            return AuthorIdentityResult()

        # author name → 매칭된 레포들 수집
        author_repos: dict[str, list[str]] = {}
        author_matches: dict[str, list[AuthorMatch]] = {}

        for repo_name, result in results_by_repo.items():
            for m in result.matches:
                key = m.name.lower()
                author_repos.setdefault(key, []).append(repo_name)
                author_matches.setdefault(key, []).append(m)

        total_repos = len(results_by_repo)
        merged: list[AuthorMatch] = []

        for author_key, repo_list in author_repos.items():
            all_matches = author_matches[author_key]
            # 최고 confidence 매치 기준
            best_of_author = max(all_matches, key=lambda m: (m.confidence, m.commits))
            repos_matched = sorted(set(repo_list))
            n_repos = len(repos_matched)

            base_confidence = best_of_author.confidence

            if n_repos >= 2:
                # cross-repo 부스트
                adjusted = min(base_confidence * 1.3, 1.0)
            elif total_repos >= 2 and n_repos == 1:
                # 1개만 매칭 + 다른 레포 존재 → 패널티
                adjusted = base_confidence * 0.5
            else:
                adjusted = base_confidence

            total_commits = sum(m.commits for m in all_matches)
            merged.append(AuthorMatch(
                name=best_of_author.name,
                email=best_of_author.email,
                commits=total_commits,
                confidence=round(adjusted, 2),
                method=best_of_author.method,
                repos_matched=repos_matched,
            ))

        cross_verified = any(len(repos) >= 2 for repos in author_repos.values())
        best = max(merged, key=lambda m: (m.confidence, m.commits)) if merged else None

        return AuthorIdentityResult(
            matches=merged,
            best_match=best,
            cross_repo_verified=cross_verified,
        )

    @staticmethod
    def validate_repo_contributions(
        repo_result: dict,
    ) -> dict:
        """
        레포 기여도 정합성 검증 (JIT-39)

        1. contributions vs 실제 커밋 수 일치 확인
        2. 불일치 시 실제 커밋 수로 보정
        3. zero-contribution 여부 판별

        Args:
            repo_result: analyze_single_repo 결과 dict

        Returns:
            {
                "is_zero_contribution": bool,
                "original_contributions": int,
                "validated_contributions": int,
                "correction_applied": bool,
                "correction_reason": str | None,
                "repo_name": str,
            }
        """
        repo_name = repo_result.get("repo_name", "unknown")
        commit_count = repo_result.get("candidate_commits", 0)
        # monthly_contributions 합산 = 실제 커밋 SHA 기반 수치
        monthly = repo_result.get("monthly_contributions", [])
        actual_commit_sum = sum(monthly) if monthly else commit_count

        correction_applied = False
        correction_reason = None

        # 정합성 검증: contributions와 실제 커밋 수 비교
        if commit_count != actual_commit_sum and actual_commit_sum > 0:
            correction_applied = True
            correction_reason = (
                f"contributions mismatch: reported={commit_count}, "
                f"actual_sha_count={actual_commit_sum}"
            )
            logger.warning(
                f"[JIT-39] {repo_name}: {correction_reason} — "
                f"correcting to {actual_commit_sum}"
            )

        validated = actual_commit_sum if correction_applied else commit_count
        is_zero = validated == 0

        if is_zero:
            logger.info(
                f"[JIT-39] repo {repo_name} excluded: "
                f"zero contributions after author filtering"
            )

        return {
            "is_zero_contribution": is_zero,
            "original_contributions": commit_count,
            "validated_contributions": validated,
            "correction_applied": correction_applied,
            "correction_reason": correction_reason,
            "repo_name": repo_name,
        }

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
