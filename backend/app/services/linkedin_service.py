"""
backend/app/services/linkedin_service.py
Bright Data Web Scraper API를 통한 LinkedIn 프로필 수집

Proxycurl 서비스 중단(LinkedIn 소송)으로 Bright Data로 마이그레이션.

Bright Data API 흐름:
1. POST /datasets/v3/trigger — 수집 시작 (snapshot_id 반환)
2. GET /datasets/v3/progress/{snapshot_id} — 진행 상태 확인
3. GET /datasets/v3/snapshot/{snapshot_id} — 완료 시 결과 조회
"""
import asyncio
import logging
import re

import httpx

from app.core.config import settings
from app.exceptions import LinkedInFetchError

logger = logging.getLogger(__name__)

LINKEDIN_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?linkedin\.com/in/[\w\-]+(?:/(?:details/[\w\-]+)?)?/?$"
)
MAX_RETRIES = 2
RETRY_BACKOFF = 1.0  # seconds
POLL_INTERVAL = 5.0  # seconds
MAX_POLL_ATTEMPTS = 24  # 5s × 24 = 최대 2분 대기
SNAPSHOT_RETRY_ATTEMPTS = 6  # snapshot 202 재시도 (5s × 6 = 최대 30초)
SNAPSHOT_RETRY_INTERVAL = 5.0  # seconds


class LinkedInService:
    """LinkedIn 프로필 데이터 수집 (Bright Data Web Scraper API)

    Bright Data 비동기 API 패턴:
    - trigger: 수집 요청 → snapshot_id 반환
    - progress: 상태 폴링 (running/ready/failed)
    - snapshot: 완료 후 결과 조회
    """

    BASE_URL = "https://api.brightdata.com/datasets/v3"
    DATASET_ID = "gd_l1viktl72bvl7bjuj0"  # LinkedIn People Profile dataset

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token or settings.BRIGHTDATA_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}" if self.api_token else "",
            "Content-Type": "application/json",
        }

    async def get_profile(self, linkedin_url: str) -> dict | None:
        """LinkedIn 프로필 조회 (비동기 수집 + 폴링)

        Returns:
            프로필 dict or None (API 토큰 미설정 시 또는 404)

        Raises:
            LinkedInFetchError: API 호출 실패 시
        """
        if not self.api_token:
            logger.warning("BRIGHTDATA_API_TOKEN not set, skipping LinkedIn fetch")
            return None

        if not self.validate_url(linkedin_url):
            raise LinkedInFetchError(f"Invalid LinkedIn URL: {linkedin_url}")

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                return await self._fetch_profile(linkedin_url)
            except LinkedInFetchError:
                raise
            except httpx.HTTPError as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF * (2 ** attempt)
                    logger.info(f"Retry {attempt + 1}/{MAX_RETRIES} for {linkedin_url} in {wait}s")
                    await asyncio.sleep(wait)

        raise LinkedInFetchError(f"Bright Data request failed after retries: {last_error}") from last_error

    async def _fetch_profile(self, linkedin_url: str) -> dict | None:
        """Bright Data 비동기 API 호출 (메인 프로필 URL)

        Bright Data Web Scraper API는 메인 프로필 URL에서 experience, education,
        skills, projects 등 모든 섹션을 추출함. /details/ 세부 페이지 URL은
        dead_page로 처리되므로 메인 URL만 전송.
        """
        urls = [{"url": linkedin_url}]

        async with httpx.AsyncClient(timeout=30.0) as client:
            snapshot_id = await self._trigger_collection(client, urls)
            if not snapshot_id:
                raise LinkedInFetchError(
                    f"Bright Data trigger failed: {linkedin_url}"
                )

            logger.info(f"Bright Data collection started: {snapshot_id}")
            data = await self._poll_and_fetch(client, snapshot_id, linkedin_url)

            if data is None:
                return None

            return self._normalize_profile(data[0], linkedin_url)

    async def _trigger_collection(
        self, client: httpx.AsyncClient, urls: list[dict]
    ) -> str | None:
        """Bright Data 수집 트리거. 성공 시 snapshot_id, 실패 시 None 반환."""
        try:
            trigger_resp = await client.post(
                f"{self.BASE_URL}/trigger",
                params={"dataset_id": self.DATASET_ID},
                json=urls,
                headers=self.headers,
            )

            logger.info(
                f"Bright Data trigger response: status={trigger_resp.status_code}, "
                f"urls={len(urls)}, body={trigger_resp.text[:500]}"
            )

            if trigger_resp.status_code == 429:
                raise httpx.HTTPError("Rate limited by Bright Data")

            if trigger_resp.status_code not in (200, 201, 202):
                logger.error(
                    f"Bright Data trigger error: status={trigger_resp.status_code}, "
                    f"body={trigger_resp.text[:1000]}, urls={[u['url'] for u in urls]}"
                )
                return None

            trigger_data = trigger_resp.json()
            snapshot_id = trigger_data.get("snapshot_id")
            if not snapshot_id:
                logger.error(f"No snapshot_id in trigger response: {trigger_data}")
                return None

            return snapshot_id

        except httpx.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Bright Data trigger exception: {e}", exc_info=True)
            return None

    async def _poll_and_fetch(
        self, client: httpx.AsyncClient, snapshot_id: str, linkedin_url: str
    ) -> list[dict] | None:
        """상태 폴링 + 결과 조회. 실패 시 None 반환 (예외 발생 안 함)."""
        try:
            # 상태 폴링
            for poll_attempt in range(MAX_POLL_ATTEMPTS):
                await asyncio.sleep(POLL_INTERVAL)

                progress_resp = await client.get(
                    f"{self.BASE_URL}/progress/{snapshot_id}",
                    headers=self.headers,
                )

                if progress_resp.status_code != 200:
                    logger.warning(
                        f"Progress check failed: status={progress_resp.status_code}, "
                        f"body={progress_resp.text[:500]}"
                    )
                    continue

                progress_data = progress_resp.json()
                status = progress_data.get("status", "")

                if status == "ready":
                    logger.info(f"Bright Data collection ready: {snapshot_id}")
                    break
                elif status == "failed":
                    logger.error(
                        f"Bright Data collection failed: snapshot={snapshot_id}, "
                        f"response={progress_data}"
                    )
                    return None
                # running 상태면 계속 폴링
            else:
                logger.error(
                    f"Bright Data timeout after {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s: "
                    f"snapshot={snapshot_id}"
                )
                return None

            # 결과 조회 (JIT-79: 202 재시도 — 데이터 준비 중일 수 있음)
            data = None
            for snapshot_attempt in range(SNAPSHOT_RETRY_ATTEMPTS):
                snapshot_resp = await client.get(
                    f"{self.BASE_URL}/snapshot/{snapshot_id}",
                    params={"format": "json"},
                    headers=self.headers,
                )

                logger.info(
                    f"Bright Data snapshot response: status={snapshot_resp.status_code}, "
                    f"snapshot={snapshot_id}, attempt={snapshot_attempt + 1}/{SNAPSHOT_RETRY_ATTEMPTS}"
                )

                if snapshot_resp.status_code == 200:
                    data = snapshot_resp.json()
                    break
                elif snapshot_resp.status_code == 202:
                    logger.info(
                        f"Bright Data snapshot not ready yet (202), "
                        f"retrying in {SNAPSHOT_RETRY_INTERVAL}s..."
                    )
                    await asyncio.sleep(SNAPSHOT_RETRY_INTERVAL)
                    continue
                elif snapshot_resp.status_code == 404:
                    logger.warning(f"LinkedIn profile not found: {linkedin_url}")
                    return None
                else:
                    logger.error(
                        f"Bright Data snapshot error: status={snapshot_resp.status_code}, "
                        f"body={snapshot_resp.text[:1000]}"
                    )
                    return None
            else:
                logger.error(
                    f"Bright Data snapshot still not ready after "
                    f"{SNAPSHOT_RETRY_ATTEMPTS * SNAPSHOT_RETRY_INTERVAL}s: "
                    f"snapshot={snapshot_id}"
                )
                return None
            if not isinstance(data, list) or len(data) == 0:
                logger.warning(f"Empty snapshot data for {linkedin_url}: {type(data)}")
                return None

            return data

        except httpx.HTTPError:
            raise
        except Exception as e:
            logger.error(f"Poll/fetch exception: {e}", exc_info=True)
            return None

    @staticmethod
    def validate_url(url: str) -> bool:
        """LinkedIn 프로필 URL 유효성 검증"""
        return bool(LINKEDIN_URL_PATTERN.match(url))

    def _normalize_profile(self, data: dict, url: str) -> dict:
        """Bright Data 응답을 내부 형식으로 정규화

        Bright Data LinkedIn People Profile 데이터셋 필드:
        - 기본: name, headline, about, country_code, city, avatar
        - 경력: experience[] — 중첩 positions[] 구조 지원
          - 단일 포지션: {title, company, start_date, end_date, description}
          - 그룹 포지션: {company, positions: [{title, start_date, end_date, ...}]}
        - 학력: education[] (title/school, degree, field, start_year/start_date, end_year/end_date)
        - 기술: Bright Data는 skills 필드 미반환 → about/experience/project에서 추출
        - 프로젝트: projects[] (title, start_date, description)
        - 수상: honors_and_awards[] (title, publication, date, description)
        - 활동: activity[] (interaction, title, link)
        - 연결: followers, connections
        - 회사: current_company, current_company_name
        - 링크: websites[], personal_urls[], bio_links[]
        """
        # 디버그: Bright Data 원본 키 로깅 (필드 누락 진단용)
        raw_keys = sorted(data.keys()) if isinstance(data, dict) else []
        logger.info(f"Bright Data raw keys: {raw_keys}")
        # GitHub URL 추출 (websites, bio_links 등에서)
        github_url = None
        all_websites = []
        for source in [data.get("websites"), data.get("personal_urls"), data.get("bio_links")]:
            if source:
                for site in source:
                    site_url = site if isinstance(site, str) else (site.get("url") or "")
                    if site_url:
                        all_websites.append(site_url)
                        if "github.com" in site_url and not github_url:
                            github_url = site_url

        # 현재 회사 추출
        current_company = None
        if data.get("current_company"):
            cc = data["current_company"]
            current_company = cc.get("name") if isinstance(cc, dict) else cc
        elif data.get("current_company_name"):
            current_company = data["current_company_name"]

        # 경력 정규화 — Bright Data 중첩 positions 구조 지원
        # Bright Data 형식: experience[].positions[] (한 회사에 여러 직책)
        # 단일 형식: experience[].title (직책이 바로 있는 경우)
        experiences = []
        raw_exp = data.get("experience") or data.get("experiences") or []
        if not raw_exp:
            logger.warning("Bright Data returned empty experience array")
        if raw_exp:
            for exp in raw_exp[:10]:
                if not isinstance(exp, dict):
                    continue

                positions = exp.get("positions")
                if positions and isinstance(positions, list):
                    # 그룹 형식: 한 회사에 여러 포지션
                    company_name = exp.get("company") or exp.get("company_name") or exp.get("title", "")
                    company_location = exp.get("location")
                    for pos in positions:
                        if not isinstance(pos, dict):
                            continue
                        experiences.append({
                            "title": pos.get("title") or pos.get("subtitle"),
                            "company": company_name,
                            "description": pos.get("description"),
                            "starts_at": pos.get("start_date") or pos.get("starts_at"),
                            "ends_at": pos.get("end_date") or pos.get("ends_at"),
                            "duration": pos.get("duration") or pos.get("duration_short"),
                            "location": pos.get("location") or company_location,
                        })
                else:
                    # 단일 형식: 직접 title/company가 있는 경우
                    experiences.append({
                        "title": exp.get("title"),
                        "company": exp.get("company") or exp.get("company_name"),
                        "description": exp.get("description"),
                        "starts_at": exp.get("start_date") or exp.get("starts_at"),
                        "ends_at": exp.get("end_date") or exp.get("ends_at"),
                        "duration": exp.get("duration") or exp.get("duration_short"),
                        "location": exp.get("location"),
                    })
        experiences = experiences[:10]  # 최대 10개

        # Fallback: experience가 비었지만 current_company가 있으면 최소 1개 구성
        if not experiences and current_company:
            headline = data.get("headline") or data.get("position") or ""
            experiences.append({
                "title": headline if headline else None,
                "company": current_company,
                "description": None,
                "starts_at": None,
                "ends_at": None,
                "duration": None,
                "location": data.get("city") or data.get("location"),
            })

        # 학력 정규화 — Bright Data는 start_year/end_year 사용, title이 학교명
        education = []
        raw_edu = data.get("education") or []
        if not raw_edu:
            logger.warning("Bright Data returned empty education array")
        if raw_edu:
            for edu in raw_edu[:5]:
                if not isinstance(edu, dict):
                    continue
                education.append({
                    "school": edu.get("school") or edu.get("school_name") or edu.get("title"),
                    "degree": edu.get("degree") or edu.get("degree_name"),
                    "field": edu.get("field_of_study") or edu.get("field"),
                    "starts_at": edu.get("start_date") or edu.get("starts_at") or edu.get("start_year"),
                    "ends_at": edu.get("end_date") or edu.get("ends_at") or edu.get("end_year"),
                })

        # 프로젝트 정규화 (새로 추가)
        projects = []
        raw_projects = data.get("projects") or []
        for proj in raw_projects[:10]:
            if not isinstance(proj, dict):
                continue
            projects.append({
                "title": proj.get("title"),
                "start_date": proj.get("start_date"),
                "end_date": proj.get("end_date"),
                "description": proj.get("description"),
                "url": proj.get("url"),
            })

        # 수상/인증 정규화 (새로 추가)
        honors = []
        raw_honors = data.get("honors_and_awards") or []
        for honor in raw_honors[:10]:
            if not isinstance(honor, dict):
                continue
            honors.append({
                "title": honor.get("title"),
                "issuer": honor.get("publication") or honor.get("issuer"),
                "date": honor.get("date"),
                "description": honor.get("description"),
            })

        # 활동 정규화 (새로 추가)
        activity = []
        raw_activity = data.get("activity") or []
        for act in raw_activity[:10]:
            if not isinstance(act, dict):
                continue
            activity.append({
                "interaction": act.get("interaction"),
                "title": act.get("title"),
                "link": act.get("link"),
            })

        # 자격증 정규화
        certifications = []
        raw_certs = data.get("certifications") or []
        for cert in raw_certs[:10]:
            if not isinstance(cert, dict):
                continue
            certifications.append({
                "name": cert.get("name"),
                "authority": cert.get("authority") or cert.get("issuing_organization"),
            })

        # 언어 정규화
        languages = []
        raw_langs = data.get("languages") or []
        for lang in raw_langs:
            if isinstance(lang, str):
                languages.append(lang)
            elif isinstance(lang, dict):
                languages.append(lang.get("name") or "")

        # 추천서 정규화 (JIT-47)
        recommendations = []
        raw_recs = data.get("recommendations") or []
        for rec in raw_recs[:20]:
            if not isinstance(rec, dict):
                continue
            recommendations.append({
                "from_user": rec.get("from_user") or rec.get("recommender") or rec.get("name") or "Anonymous",
                "text": rec.get("text") or rec.get("recommendation_text") or rec.get("description"),
                "date": rec.get("date"),
                "relationship": rec.get("relationship") or rec.get("subtitle"),
            })

        # 봉사활동 정규화 (JIT-47)
        volunteer = []
        raw_volunteer = data.get("volunteering") or data.get("volunteer_experience") or []
        for vol in raw_volunteer[:10]:
            if not isinstance(vol, dict):
                continue
            volunteer.append({
                "organization": vol.get("organization") or vol.get("company") or vol.get("title") or "",
                "role": vol.get("role") or vol.get("position") or vol.get("subtitle"),
                "cause": vol.get("cause"),
                "starts_at": vol.get("start_date") or vol.get("starts_at"),
                "ends_at": vol.get("end_date") or vol.get("ends_at"),
                "description": vol.get("description"),
            })

        # 스킬 추출: Bright Data API는 skills 필드를 반환하지 않으므로
        # 원본 데이터에 skills가 있으면 사용, 없으면 텍스트에서 추출
        raw_skills = data.get("skills") or []
        if not raw_skills:
            raw_skills = self._extract_skills_from_text(data, experiences, projects)

        # 경력 수 및 스킬 수 로깅 (진단용)
        logger.info(
            f"LinkedIn normalized: {len(experiences)} experiences, "
            f"{len(education)} education, {len(raw_skills)} skills, "
            f"{len(projects)} projects, {len(recommendations)} recommendations, "
            f"{len(volunteer)} volunteer"
        )

        return {
            # 기본 정보
            "profile_url": url,
            "full_name": data.get("name") or data.get("full_name"),
            "headline": data.get("headline") or data.get("position"),
            "summary": data.get("about") or data.get("summary"),
            "country": data.get("country") or data.get("country_code") or data.get("country_full_name"),
            "city": data.get("city") or data.get("location"),
            "avatar_url": data.get("avatar"),

            # 현재 회사
            "current_company": current_company,

            # 경력/학력/기술
            "experiences": experiences,
            "education": education,
            "skills": raw_skills[:30],
            "languages": languages,
            "certifications": certifications,

            # 프로젝트/수상 (새로 추가)
            "projects": projects,
            "honors_and_awards": honors,

            # 활동 (새로 추가)
            "activity": activity,

            # 추천서/봉사활동 (JIT-46/47)
            "recommendations": recommendations,
            "volunteer_experience": volunteer,

            # 연결
            "followers": data.get("followers"),
            "connections": data.get("connections"),

            # 링크
            "github_url": github_url,
            "websites": all_websites,
        }

    @staticmethod
    def _extract_skills_from_text(
        data: dict,
        experiences: list[dict],
        projects: list[dict],
    ) -> list[str]:
        """프로필 텍스트에서 기술 스킬 키워드를 추출

        Bright Data가 skills 필드를 반환하지 않을 때 fallback으로 사용.
        about, headline, experience descriptions, project descriptions에서
        일반적인 기술 키워드를 매칭하여 추출.
        """
        # 텍스트 수집
        texts = []
        about = data.get("about") or data.get("summary") or ""
        headline = data.get("headline") or data.get("position") or ""
        texts.append(about)
        texts.append(headline)

        for exp in experiences:
            desc = exp.get("description") or ""
            title = exp.get("title") or ""
            texts.append(desc)
            texts.append(title)

        for proj in projects:
            desc = proj.get("description") or ""
            texts.append(desc)

        combined = " ".join(texts).lower()
        if not combined.strip():
            return []

        # 기술 키워드 사전 (대소문자 무관 매칭)
        tech_keywords = {
            # Languages
            "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang",
            "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
            # Frontend
            "react", "vue", "angular", "next.js", "nuxt", "svelte", "tailwind",
            "html", "css", "sass", "webpack", "vite",
            # Backend
            "node.js", "express", "fastapi", "django", "flask", "spring",
            "rails", "laravel", "gin", "fiber",
            # Data / ML
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
            "machine learning", "deep learning", "nlp", "computer vision",
            "langchain", "llm", "generative ai", "rag",
            # Cloud / DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "ci/cd", "github actions", "jenkins", "ansible",
            # Database
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "dynamodb", "firebase", "supabase", "pgvector",
            # Tools / Concepts
            "git", "linux", "api", "rest", "graphql", "grpc",
            "microservices", "agile", "scrum", "devops",
            "temporal", "kafka", "rabbitmq", "celery",
        }

        found = []
        for keyword in tech_keywords:
            # 단어 경계 체크 (간단한 substring 매칭)
            if keyword in combined:
                # 원본 대소문자 보존
                found.append(keyword.title() if len(keyword) > 3 else keyword.upper())

        return sorted(set(found))


# 하위 호환: 기존 import 경로 유지
ProxycurlService = LinkedInService
