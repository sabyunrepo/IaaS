"""
BrightDataClient 테스트

- test_scrape_profile_success: 정상 응답 → LinkedInProfile
- test_scrape_profile_no_url: URL None → None
- test_scrape_profile_empty_url: 빈 문자열 → None
- test_scrape_profile_rate_limit: 429 → exponential backoff 후 재시도 성공
- test_scrape_profile_all_retries_failed: 3회 HTTPError → None
- test_scrape_profile_private: 비공개 프로필 → None
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from infrastructure.linkedin.brightdata_client import BrightDataClient


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> BrightDataClient:
    return BrightDataClient(api_key="test-api-key")


# Raw BrightData JSON that normalize_linkedin_profile can consume.
_VALID_RAW = {
    "name": "Jane Doe",
    "headline": "Software Engineer",
    "location": "Seoul, Korea",
    "summary": "Experienced engineer",
    "profile_url": "https://www.linkedin.com/in/janedoe",
    "experiences": [
        {
            "company": "Acme Corp",
            "title": "Backend Engineer",
            "start_date": "2021-01",
            "end_date": None,
            "description": "Built APIs",
            "location": "Seoul",
        }
    ],
    "educations": [],
    "skills": [{"name": "Python", "endorsement_count": 10}],
    "certifications": [],
}


def _make_response(status_code: int, json_body: dict | None = None) -> MagicMock:
    """httpx.Response 모의 객체를 생성한다."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_body or {}

    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=response,
        )
    else:
        response.raise_for_status.return_value = None

    return response


# ---------------------------------------------------------------------------
# test_scrape_profile_success
# ---------------------------------------------------------------------------


class TestScrapeProfileSuccess:
    @pytest.mark.asyncio
    async def test_scrape_profile_success(self, client: BrightDataClient):
        """정상 BrightData 응답 → LinkedInProfile 도메인 모델 반환."""
        success_response = _make_response(200, _VALID_RAW)

        with patch("infrastructure.linkedin.brightdata_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = success_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            profile = await client.scrape_profile("https://www.linkedin.com/in/janedoe")

        assert profile is not None
        assert profile.name == "Jane Doe"
        assert profile.headline == "Software Engineer"
        assert profile.profile_url == "https://www.linkedin.com/in/janedoe"
        assert len(profile.experiences) == 1
        assert profile.experiences[0].company == "Acme Corp"
        assert profile.experiences[0].is_current is True


# ---------------------------------------------------------------------------
# test_scrape_profile_no_url / empty_url
# ---------------------------------------------------------------------------


class TestScrapeProfileNoUrl:
    @pytest.mark.asyncio
    async def test_scrape_profile_no_url(self, client: BrightDataClient):
        """None URL → API 호출 없이 None 반환."""
        with patch("infrastructure.linkedin.brightdata_client.httpx.AsyncClient") as mock_cls:
            profile = await client.scrape_profile(None)  # type: ignore[arg-type]

        mock_cls.assert_not_called()
        assert profile is None

    @pytest.mark.asyncio
    async def test_scrape_profile_empty_url(self, client: BrightDataClient):
        """빈 문자열 URL → API 호출 없이 None 반환."""
        with patch("infrastructure.linkedin.brightdata_client.httpx.AsyncClient") as mock_cls:
            profile = await client.scrape_profile("")

        mock_cls.assert_not_called()
        assert profile is None


# ---------------------------------------------------------------------------
# test_scrape_profile_rate_limit
# ---------------------------------------------------------------------------


class TestScrapeProfileRateLimit:
    @pytest.mark.asyncio
    async def test_scrape_profile_rate_limit(self, client: BrightDataClient):
        """429 응답 → exponential backoff 후 재시도하여 성공."""
        rate_limit_response = _make_response(429)
        success_response = _make_response(200, _VALID_RAW)

        call_count = 0

        async def post_side_effect(*args, **kwargs):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_response
            return success_response

        with patch("infrastructure.linkedin.brightdata_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = post_side_effect
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch(
                "infrastructure.linkedin.brightdata_client.asyncio.sleep", AsyncMock()
            ) as mock_sleep:
                profile = await client.scrape_profile("https://www.linkedin.com/in/janedoe")

        # 첫 번째 429에서 sleep(2**0 = 1)이 호출되어야 한다.
        mock_sleep.assert_called_once_with(1)
        assert profile is not None
        assert profile.name == "Jane Doe"


# ---------------------------------------------------------------------------
# test_scrape_profile_all_retries_failed
# ---------------------------------------------------------------------------


class TestScrapeProfileAllRetriesFailed:
    @pytest.mark.asyncio
    async def test_scrape_profile_all_retries_failed(self, client: BrightDataClient):
        """모든 재시도에서 HTTPError 발생 → None 반환."""
        with patch("infrastructure.linkedin.brightdata_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.ConnectError("Connection refused")
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch(
                "infrastructure.linkedin.brightdata_client.asyncio.sleep", AsyncMock()
            ) as mock_sleep:
                profile = await client.scrape_profile("https://www.linkedin.com/in/janedoe")

        # max_retries=3: attempt 0,1 에서 sleep, attempt 2(마지막)에서는 sleep 없이 None 반환.
        assert mock_sleep.call_count == 2
        assert profile is None


# ---------------------------------------------------------------------------
# test_scrape_profile_private
# ---------------------------------------------------------------------------


class TestScrapeProfilePrivate:
    @pytest.mark.asyncio
    async def test_scrape_profile_private_flag(self, client: BrightDataClient):
        """is_private=True → None 반환."""
        private_raw = {"is_private": True, "name": "Hidden User"}
        private_response = _make_response(200, private_raw)

        with patch("infrastructure.linkedin.brightdata_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = private_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            profile = await client.scrape_profile("https://www.linkedin.com/in/hidden")

        assert profile is None

    @pytest.mark.asyncio
    async def test_scrape_profile_private_no_name(self, client: BrightDataClient):
        """name 없는 응답 (비공개 프로필 패턴) → None 반환."""
        private_raw = {"is_private": False, "name": ""}
        private_response = _make_response(200, private_raw)

        with patch("infrastructure.linkedin.brightdata_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = private_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            profile = await client.scrape_profile("https://www.linkedin.com/in/hidden")

        assert profile is None
