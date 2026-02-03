"""LinkedIn service (Bright Data) tests."""
import pytest


class TestLinkedInServiceInit:
    def test_importable(self):
        from app.services.linkedin_service import LinkedInService
        assert LinkedInService is not None

    def test_backwards_compat_alias(self):
        from app.services.linkedin_service import ProxycurlService, LinkedInService
        assert ProxycurlService is LinkedInService

    def test_base_url(self):
        from app.services.linkedin_service import LinkedInService
        assert "brightdata" in LinkedInService.BASE_URL

    def test_default_no_api_token(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token=None)
        assert isinstance(svc.api_token, (str, type(None)))


class TestValidateUrl:
    def test_valid_url(self):
        from app.services.linkedin_service import LinkedInService
        assert LinkedInService.validate_url("https://www.linkedin.com/in/john-doe")

    def test_valid_url_no_www(self):
        from app.services.linkedin_service import LinkedInService
        assert LinkedInService.validate_url("https://linkedin.com/in/john-doe")

    def test_valid_url_trailing_slash(self):
        from app.services.linkedin_service import LinkedInService
        assert LinkedInService.validate_url("https://linkedin.com/in/john-doe/")

    def test_invalid_url_company(self):
        from app.services.linkedin_service import LinkedInService
        assert not LinkedInService.validate_url("https://linkedin.com/company/acme")

    def test_invalid_url_random(self):
        from app.services.linkedin_service import LinkedInService
        assert not LinkedInService.validate_url("https://example.com/in/john")

    def test_invalid_url_empty(self):
        from app.services.linkedin_service import LinkedInService
        assert not LinkedInService.validate_url("")


class TestNormalizeProfile:
    def test_basic_fields(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token="test")
        data = {
            "name": "John Doe",
            "headline": "Engineer",
            "about": "Experienced",
            "country": "Korea",
            "city": "Seoul",
        }
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert result["full_name"] == "John Doe"
        assert result["country"] == "Korea"
        assert result["profile_url"] == "https://linkedin.com/in/john"

    def test_github_extraction_from_personal_urls(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token="test")
        data = {
            "personal_urls": [
                {"url": "https://github.com/johndoe"},
                {"url": "https://blog.example.com"},
            ],
        }
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert result["github_url"] == "https://github.com/johndoe"

    def test_github_extraction_from_websites(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token="test")
        data = {
            "websites": ["https://github.com/johndoe", "https://blog.example.com"],
        }
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert result["github_url"] == "https://github.com/johndoe"

    def test_no_github(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token="test")
        result = svc._normalize_profile({}, "https://linkedin.com/in/john")
        assert result["github_url"] is None

    def test_experiences_limit(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token="test")
        data = {"experience": [{"title": f"Job {i}"} for i in range(20)]}
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert len(result["experiences"]) == 10

    def test_certifications_included(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token="test")
        data = {"certifications": [{"name": "AWS", "authority": "Amazon"}]}
        result = svc._normalize_profile(data, "https://linkedin.com/in/john")
        assert len(result["certifications"]) == 1
        assert result["certifications"][0]["name"] == "AWS"

    def test_empty_data(self):
        from app.services.linkedin_service import LinkedInService
        svc = LinkedInService(api_token="test")
        result = svc._normalize_profile({}, "https://linkedin.com/in/john")
        assert result["experiences"] == []
        assert result["skills"] == []
        assert result["certifications"] == []


class TestGetProfileNoKey:
    @pytest.mark.asyncio
    async def test_returns_none_without_token(self):
        from app.services.linkedin_service import LinkedInService
        from unittest.mock import patch

        # settings.BRIGHTDATA_API_TOKEN도 None으로 설정해야 함
        with patch("app.services.linkedin_service.settings") as mock_settings:
            mock_settings.BRIGHTDATA_API_TOKEN = None

            svc = LinkedInService(api_token=None)
            result = await svc.get_profile("https://linkedin.com/in/john")
            assert result is None

    @pytest.mark.asyncio
    async def test_invalid_url_raises(self):
        from app.services.linkedin_service import LinkedInService
        from app.exceptions import LinkedInFetchError
        svc = LinkedInService(api_token="test-key")
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
