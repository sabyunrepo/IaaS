"""LinkedIn service (Proxycurl) tests."""
import pytest


class TestProxycurlServiceInit:
    def test_importable(self):
        from app.services.linkedin_service import ProxycurlService
        assert ProxycurlService is not None

    def test_base_url(self):
        from app.services.linkedin_service import ProxycurlService
        assert "proxycurl" in ProxycurlService.BASE_URL

    def test_default_no_api_key(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key=None)
        # settings.PROXYCURL_API_KEY is likely empty in test env
        assert isinstance(svc.api_key, (str, type(None)))


class TestValidateUrl:
    def test_valid_url(self):
        from app.services.linkedin_service import ProxycurlService
        assert ProxycurlService.validate_url("https://www.linkedin.com/in/john-doe")

    def test_valid_url_no_www(self):
        from app.services.linkedin_service import ProxycurlService
        assert ProxycurlService.validate_url("https://linkedin.com/in/john-doe")

    def test_valid_url_trailing_slash(self):
        from app.services.linkedin_service import ProxycurlService
        assert ProxycurlService.validate_url("https://linkedin.com/in/john-doe/")

    def test_invalid_url_company(self):
        from app.services.linkedin_service import ProxycurlService
        assert not ProxycurlService.validate_url("https://linkedin.com/company/acme")

    def test_invalid_url_random(self):
        from app.services.linkedin_service import ProxycurlService
        assert not ProxycurlService.validate_url("https://example.com/in/john")

    def test_invalid_url_empty(self):
        from app.services.linkedin_service import ProxycurlService
        assert not ProxycurlService.validate_url("")


class TestNormalizeProfile:
    def test_basic_fields(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="test")
        data = {
            "full_name": "John Doe",
            "headline": "Engineer",
            "summary": "Experienced",
            "country_full_name": "Korea",
            "city": "Seoul",
        }
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert result["full_name"] == "John Doe"
        assert result["country"] == "Korea"
        assert result["url"] == "https://linkedin.com/in/john"

    def test_github_extraction(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="test")
        data = {
            "personal_urls": [
                {"url": "https://github.com/johndoe"},
                {"url": "https://blog.example.com"},
            ],
        }
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert result["github_url"] == "https://github.com/johndoe"

    def test_no_github(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="test")
        result = svc._normalize_profile({}, "https://linkedin.com/in/john")
        assert result["github_url"] is None

    def test_experiences_limit(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="test")
        data = {"experiences": [{"title": f"Job {i}"} for i in range(20)]}
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert len(result["experiences"]) == 10

    def test_certifications_included(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="test")
        data = {"certifications": [{"name": "AWS", "authority": "Amazon"}]}
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert len(result["certifications"]) == 1
        assert result["certifications"][0]["name"] == "AWS"

    def test_recommendations_count(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="test")
        data = {"recommendations": ["rec1", "rec2"]}
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert result["recommendations_count"] == 2

    def test_empty_data(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="test")
        result = svc._normalize_profile({}, "https://linkedin.com/in/john")
        assert result["experiences"] == []
        assert result["skills"] == []
        assert result["certifications"] == []


class TestGetProfileNoKey:
    @pytest.mark.asyncio
    async def test_returns_none_without_key(self):
        from app.services.linkedin_service import ProxycurlService
        svc = ProxycurlService(api_key="")
        result = await svc.get_profile("https://linkedin.com/in/john")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_url_raises(self):
        from app.services.linkedin_service import ProxycurlService
        from app.exceptions import LinkedInFetchError
        svc = ProxycurlService(api_key="test-key")
        with pytest.raises(LinkedInFetchError, match="Invalid"):
            await svc.get_profile("not-a-url")


class TestRetryConstants:
    def test_max_retries(self):
        from app.services.linkedin_service import MAX_RETRIES
        assert MAX_RETRIES == 2

    def test_retry_backoff(self):
        from app.services.linkedin_service import RETRY_BACKOFF
        assert RETRY_BACKOFF > 0


class TestLinkedInUrlPattern:
    def test_pattern_exists(self):
        from app.services.linkedin_service import LINKEDIN_URL_PATTERN
        assert LINKEDIN_URL_PATTERN is not None
