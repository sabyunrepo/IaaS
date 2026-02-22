"""
BrightData Client — LinkedIn 프로필 스크레이핑 어댑터.

BrightData Scraping Browser API로 LinkedIn 프로필 HTML/JSON을 가져오고,
Domain의 normalize_linkedin_profile()로 LinkedInProfile 모델로 변환한다.
"""
import asyncio

import httpx

from domain.identity.linkedin_models import LinkedInProfile
from domain.identity.linkedin_normalizer import normalize_linkedin_profile
from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError


class BrightDataClient:
    """BrightData Scraping Browser API 기반 LinkedIn 프로필 스크레이퍼."""

    def __init__(
        self,
        *,
        api_key: str,
        scraping_browser_url: str = "https://api.brightdata.com",
        max_retries: int = 3,
        timeout: float = 30.0,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._api_key = api_key
        self._base_url = scraping_browser_url
        self._max_retries = max_retries
        self._timeout = timeout
        self._cb = circuit_breaker

    async def scrape_profile(self, linkedin_url: str) -> LinkedInProfile | None:
        """LinkedIn 프로필 스크레이핑 → 도메인 모델 변환.

        Returns None if:
        - linkedin_url이 빈 문자열/None
        - BrightData API 호출 실패 (모든 재시도 소진)
        - 프로필 비공개
        - Circuit breaker가 Open 상태
        """
        if not linkedin_url:
            return None

        if self._cb:
            try:
                return await self._cb.call(self._scrape_profile_impl, linkedin_url)
            except CircuitOpenError:
                return None  # BrightData fallback: 빈 프로필
        return await self._scrape_profile_impl(linkedin_url)

    async def _scrape_profile_impl(self, linkedin_url: str) -> LinkedInProfile | None:
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        f"{self._base_url}/scrape",
                        json={"url": linkedin_url, "format": "json"},
                        headers={"Authorization": f"Bearer {self._api_key}"},
                    )

                    if response.status_code == 429:
                        await asyncio.sleep(2**attempt)
                        continue

                    response.raise_for_status()
                    raw_data = response.json()

                    # 비공개 프로필 체크
                    if raw_data.get("is_private") or not raw_data.get("name"):
                        return None

                    return normalize_linkedin_profile(raw_data)

            except httpx.HTTPError:
                if attempt == self._max_retries - 1:
                    return None
                await asyncio.sleep(2**attempt)

        return None
