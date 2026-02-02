"""
backend/app/services/linkedin_service.py
Proxycurl API를 통한 LinkedIn 프로필 수집
"""
import logging

import httpx

from app.core.config import settings
from app.exceptions import LinkedInFetchError

logger = logging.getLogger(__name__)


class ProxycurlService:
    """LinkedIn 프로필 데이터 수집 (Proxycurl API)"""

    BASE_URL = "https://nubela.co/proxycurl/api/v2/linkedin"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.PROXYCURL_API_KEY

    async def get_profile(self, linkedin_url: str) -> dict | None:
        """LinkedIn 프로필 조회

        Returns:
            프로필 dict or None (API 키 미설정 시)

        Raises:
            LinkedInFetchError: API 호출 실패 시
        """
        if not self.api_key:
            logger.warning("PROXYCURL_API_KEY not set, skipping LinkedIn fetch")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    self.BASE_URL,
                    params={"linkedin_profile_url": linkedin_url, "use_cache": "if-present"},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )

            if resp.status_code == 200:
                data = resp.json()
                return self._normalize_profile(data, linkedin_url)
            elif resp.status_code == 404:
                logger.warning(f"LinkedIn profile not found: {linkedin_url}")
                return None
            else:
                raise LinkedInFetchError(
                    f"Proxycurl API error {resp.status_code}: {resp.text}"
                )

        except httpx.HTTPError as e:
            raise LinkedInFetchError(f"Proxycurl request failed: {e}") from e

    def _normalize_profile(self, data: dict, url: str) -> dict:
        """Proxycurl 응답을 내부 형식으로 정규화"""
        github_url = None
        for site in data.get("personal_emails", []):
            pass  # emails not useful for github
        # Check websites for GitHub
        for site in data.get("personal_urls", []) or []:
            if "github.com" in (site.get("url") or ""):
                github_url = site["url"]
                break

        return {
            "url": url,
            "full_name": data.get("full_name"),
            "headline": data.get("headline"),
            "summary": data.get("summary"),
            "country": data.get("country_full_name"),
            "city": data.get("city"),
            "experiences": [
                {
                    "title": exp.get("title"),
                    "company": exp.get("company"),
                    "description": exp.get("description"),
                    "starts_at": exp.get("starts_at"),
                    "ends_at": exp.get("ends_at"),
                }
                for exp in (data.get("experiences") or [])[:10]
            ],
            "education": [
                {
                    "school": edu.get("school"),
                    "degree": edu.get("degree_name"),
                    "field": edu.get("field_of_study"),
                }
                for edu in (data.get("education") or [])[:5]
            ],
            "skills": data.get("skills", [])[:30],
            "languages": [
                lang.get("name") for lang in (data.get("languages") or [])
            ],
            "github_url": github_url,
        }
