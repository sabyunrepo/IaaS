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
    r"^https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?$"
)
MAX_RETRIES = 2
RETRY_BACKOFF = 1.0  # seconds
POLL_INTERVAL = 5.0  # seconds
MAX_POLL_ATTEMPTS = 24  # 5s × 24 = 최대 2분 대기


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
        """Bright Data 비동기 API 호출 (trigger → poll → retrieve)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. 수집 트리거
            trigger_resp = await client.post(
                f"{self.BASE_URL}/trigger",
                params={"dataset_id": self.DATASET_ID},
                json=[{"url": linkedin_url}],
                headers=self.headers,
            )

            if trigger_resp.status_code == 429:
                raise httpx.HTTPError("Rate limited by Bright Data")
            if trigger_resp.status_code not in (200, 201, 202):
                raise LinkedInFetchError(
                    f"Bright Data trigger error {trigger_resp.status_code}: {trigger_resp.text}"
                )

            trigger_data = trigger_resp.json()
            snapshot_id = trigger_data.get("snapshot_id")
            if not snapshot_id:
                raise LinkedInFetchError(f"No snapshot_id in trigger response: {trigger_data}")

            logger.info(f"Bright Data collection started: {snapshot_id}")

            # 2. 상태 폴링
            for poll_attempt in range(MAX_POLL_ATTEMPTS):
                await asyncio.sleep(POLL_INTERVAL)

                progress_resp = await client.get(
                    f"{self.BASE_URL}/progress/{snapshot_id}",
                    headers=self.headers,
                )

                if progress_resp.status_code != 200:
                    logger.warning(f"Progress check failed: {progress_resp.status_code}")
                    continue

                progress_data = progress_resp.json()
                status = progress_data.get("status", "")

                if status == "ready":
                    logger.info(f"Bright Data collection ready: {snapshot_id}")
                    break
                elif status == "failed":
                    raise LinkedInFetchError(f"Bright Data collection failed: {progress_data}")
                # running 상태면 계속 폴링
            else:
                raise LinkedInFetchError(f"Bright Data timeout after {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s")

            # 3. 결과 조회
            snapshot_resp = await client.get(
                f"{self.BASE_URL}/snapshot/{snapshot_id}",
                params={"format": "json"},
                headers=self.headers,
            )

            if snapshot_resp.status_code == 404:
                logger.warning(f"LinkedIn profile not found: {linkedin_url}")
                return None
            if snapshot_resp.status_code != 200:
                raise LinkedInFetchError(
                    f"Bright Data snapshot error {snapshot_resp.status_code}: {snapshot_resp.text}"
                )

            data = snapshot_resp.json()
            # Bright Data는 배열로 반환
            if isinstance(data, list) and len(data) > 0:
                return self._normalize_profile(data[0], linkedin_url)
            return None

    @staticmethod
    def validate_url(url: str) -> bool:
        """LinkedIn 프로필 URL 유효성 검증"""
        return bool(LINKEDIN_URL_PATTERN.match(url))

    def _normalize_profile(self, data: dict, url: str) -> dict:
        """Bright Data 응답을 내부 형식으로 정규화

        Bright Data LinkedIn 프로필 데이터셋 필드명:
        - name, headline, about, country_code, city
        - experience[] (title, company, company_name, start_date, end_date, description)
        - education[] (school, degree, field_of_study, start_date, end_date)
        - skills[], languages[], certifications[]
        - websites[], personal_urls[]
        """
        # GitHub URL 추출
        github_url = None
        websites = data.get("websites") or data.get("personal_urls") or []
        for site in websites:
            site_url = site if isinstance(site, str) else (site.get("url") or "")
            if "github.com" in site_url:
                github_url = site_url
                break

        return {
            "url": url,
            "full_name": data.get("name") or data.get("full_name"),
            "headline": data.get("headline"),
            "summary": data.get("about") or data.get("summary"),
            "country": data.get("country") or data.get("country_code") or data.get("country_full_name"),
            "city": data.get("city"),
            "experiences": [
                {
                    "title": exp.get("title"),
                    "company": exp.get("company") or exp.get("company_name"),
                    "description": exp.get("description"),
                    "starts_at": exp.get("start_date") or exp.get("starts_at"),
                    "ends_at": exp.get("end_date") or exp.get("ends_at"),
                    "location": exp.get("location"),
                }
                for exp in (data.get("experience") or data.get("experiences") or [])[:10]
            ],
            "education": [
                {
                    "school": edu.get("school") or edu.get("school_name"),
                    "degree": edu.get("degree") or edu.get("degree_name"),
                    "field": edu.get("field_of_study") or edu.get("field"),
                    "starts_at": edu.get("start_date") or edu.get("starts_at"),
                    "ends_at": edu.get("end_date") or edu.get("ends_at"),
                }
                for edu in (data.get("education") or [])[:5]
            ],
            "skills": (data.get("skills") or [])[:30],
            "languages": [
                lang if isinstance(lang, str) else (lang.get("name") or "")
                for lang in (data.get("languages") or [])
            ],
            "certifications": [
                {
                    "name": cert.get("name"),
                    "authority": cert.get("authority") or cert.get("issuing_organization"),
                }
                for cert in (data.get("certifications") or [])[:10]
            ],
            "recommendations_count": data.get("recommendations_count") or len(data.get("recommendations") or []),
            "connections": data.get("connections"),
            "github_url": github_url,
        }


# 하위 호환: 기존 import 경로 유지
ProxycurlService = LinkedInService
