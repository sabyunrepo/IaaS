"""
backend/tests/test_input_enrichment.py
Phase 0: Input Enrichment Activity 단위 테스트

테스트 항목:
- P0-01: PDF 텍스트 추출
- P0-02: GitHub URL 추출 (정규식)
- P0-03: LinkedIn URL 추출
- P0-04: LinkedIn 프로필 수집 (Bright Data)
- P0-05: GitHub User/Org 검증
- P0-06: available_analyses 결정
- P0-07: 문서 파싱 실패 graceful 처리
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# P0-01: PDF 텍스트 추출
# ============================================================

class TestPdfTextExtraction:
    """P0-01: PDF 텍스트 추출 테스트"""

    @pytest.mark.asyncio
    async def test_extract_text_from_txt(self, tmp_path):
        """TXT 파일 추출 (plaintext fallback)"""
        from app.services.document_parser import extract_text

        test_file = tmp_path / "resume.txt"
        test_file.write_text("이름: 홍길동\nGitHub: https://github.com/honggildong/project")

        result = await extract_text(str(test_file))
        assert "홍길동" in result
        assert "github.com" in result

    @pytest.mark.asyncio
    async def test_extract_text_file_not_found(self):
        """존재하지 않는 파일"""
        from app.services.document_parser import extract_text

        with pytest.raises(FileNotFoundError):
            await extract_text("/nonexistent/resume.pdf")

    @pytest.mark.asyncio
    async def test_extract_text_unsupported_format(self, tmp_path):
        """지원하지 않는 형식"""
        from app.services.document_parser import extract_text

        test_file = tmp_path / "resume.xyz"
        test_file.write_text("data")

        with pytest.raises(ValueError, match="Unsupported"):
            await extract_text(str(test_file))


# ============================================================
# P0-02: GitHub URL 추출
# ============================================================

class TestGitHubUrlExtraction:
    """P0-02: GitHub URL 추출 테스트"""

    def test_extract_github_urls_from_text(self):
        """텍스트에서 GitHub URL 추출"""
        from app.workflows.activities.input_enrichment import _extract_urls

        text = """
        Portfolio
        - Project A: https://github.com/user/project-a
        - Project B: https://github.com/user/project-b
        - LinkedIn: https://linkedin.com/in/user
        """
        result = _extract_urls(text)

        assert len(result["github"]) == 2
        assert "https://github.com/user/project-a" in result["github"]
        assert "https://github.com/user/project-b" in result["github"]

    def test_extract_github_urls_with_org(self):
        """조직 레포 URL도 추출되는지 확인"""
        from app.workflows.activities.input_enrichment import _extract_urls

        text = "https://github.com/42cats/crime-cat 프로젝트"
        result = _extract_urls(text)

        assert "https://github.com/42cats/crime-cat" in result["github"]

    def test_extract_no_github_urls(self):
        """GitHub URL이 없는 경우"""
        from app.workflows.activities.input_enrichment import _extract_urls

        text = "일반 텍스트만 있습니다."
        result = _extract_urls(text)

        assert result["github"] == []

    def test_extract_github_username(self):
        """GitHub URL에서 username 추출"""
        from app.workflows.activities.input_enrichment import _extract_github_username

        assert _extract_github_username("https://github.com/user/repo") == "user"
        assert _extract_github_username("https://github.com/org-name/project") == "org-name"
        assert _extract_github_username("invalid-url") is None


# ============================================================
# P0-03: LinkedIn URL 추출
# ============================================================

class TestLinkedInUrlExtraction:
    """P0-03: LinkedIn URL 추출 테스트"""

    def test_extract_linkedin_url(self):
        """텍스트에서 LinkedIn URL 추출"""
        from app.workflows.activities.input_enrichment import _extract_urls

        text = """
        Contact Info:
        LinkedIn: https://www.linkedin.com/in/john-doe
        Email: john@example.com
        """
        result = _extract_urls(text)

        assert len(result["linkedin"]) == 1
        assert "https://www.linkedin.com/in/john-doe" in result["linkedin"]

    def test_extract_linkedin_url_no_www(self):
        """www 없는 LinkedIn URL"""
        from app.workflows.activities.input_enrichment import _extract_urls

        text = "LinkedIn: https://linkedin.com/in/john-doe"
        result = _extract_urls(text)

        assert len(result["linkedin"]) == 1

    def test_extract_no_linkedin_url(self):
        """LinkedIn URL이 없는 경우"""
        from app.workflows.activities.input_enrichment import _extract_urls

        text = "No social media links"
        result = _extract_urls(text)

        assert result["linkedin"] == []


# ============================================================
# P0-04: LinkedIn 프로필 수집 (Bright Data)
# ============================================================

class TestLinkedInProfileFetch:
    """P0-04: LinkedIn 프로필 수집 테스트"""

    def test_validate_linkedin_url(self):
        """LinkedIn URL 유효성 검증"""
        from app.services.linkedin_service import LinkedInService

        # 유효한 URL
        assert LinkedInService.validate_url("https://www.linkedin.com/in/john-doe")
        assert LinkedInService.validate_url("https://linkedin.com/in/john-doe")
        assert LinkedInService.validate_url("https://linkedin.com/in/john-doe/")

        # 무효한 URL
        assert not LinkedInService.validate_url("https://linkedin.com/company/acme")
        assert not LinkedInService.validate_url("https://example.com/in/john")
        assert not LinkedInService.validate_url("")

    @pytest.mark.asyncio
    async def test_get_profile_without_token(self):
        """API 토큰 없으면 None 반환"""
        from app.services.linkedin_service import LinkedInService
        from unittest.mock import patch

        # settings.BRIGHTDATA_API_TOKEN도 None으로 설정해야 함
        with patch("app.services.linkedin_service.settings") as mock_settings:
            mock_settings.BRIGHTDATA_API_TOKEN = None

            svc = LinkedInService(api_token=None)
            result = await svc.get_profile("https://linkedin.com/in/john-doe")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_profile_invalid_url(self):
        """잘못된 URL이면 예외 발생"""
        from app.services.linkedin_service import LinkedInService
        from app.exceptions import LinkedInFetchError

        svc = LinkedInService(api_token="test-key")
        with pytest.raises(LinkedInFetchError, match="Invalid"):
            await svc.get_profile("not-a-linkedin-url")

    def test_normalize_profile_extracts_github(self):
        """프로필에서 GitHub URL 추출"""
        from app.services.linkedin_service import LinkedInService

        svc = LinkedInService(api_token="test")
        data = {
            "name": "Test User",
            "websites": ["https://github.com/testuser"],
        }
        result = svc._normalize_profile(data, "https://linkedin.com/in/test")

        assert result["github_url"] == "https://github.com/testuser"

    def test_normalize_profile_handles_null_fields(self):
        """null 필드 처리"""
        from app.services.linkedin_service import LinkedInService

        svc = LinkedInService(api_token="test")
        data = {
            "name": "Test User",
            "experience": None,  # null일 수 있음
            "education": None,
            "skills": None,
        }
        result = svc._normalize_profile(data, "https://linkedin.com/in/test")

        assert result["experiences"] == []
        assert result["education"] == []
        assert result["skills"] == []


# ============================================================
# P0-05: GitHub User/Org 검증
# ============================================================

class TestGitHubUserOrgValidation:
    """P0-05: GitHub User vs Organization 검증 테스트"""

    @pytest.mark.asyncio
    async def test_get_account_type_user(self):
        """개인 계정 타입 확인"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        with patch.object(svc, "_get_github") as mock_github:
            mock_user = MagicMock()
            mock_user.type = "User"
            mock_user.name = "Test User"
            mock_user.avatar_url = "https://example.com/avatar.jpg"
            mock_user.bio = "Developer"
            mock_user.company = "TechCorp"
            mock_github.return_value.get_user.return_value = mock_user

            result = await svc.get_account_type("testuser")

            assert result["type"] == "User"
            assert result["username"] == "testuser"
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_get_account_type_organization(self):
        """조직 계정 타입 확인"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        with patch.object(svc, "_get_github") as mock_github:
            # get_user가 실패하고 get_organization이 성공
            mock_github.return_value.get_user.side_effect = Exception("Not a user")
            mock_org = MagicMock()
            mock_org.name = "42cats"
            mock_org.avatar_url = "https://example.com/org.jpg"
            mock_github.return_value.get_organization.return_value = mock_org

            result = await svc.get_account_type("42cats")

            assert result["type"] == "Organization"
            assert result["username"] == "42cats"

    @pytest.mark.asyncio
    async def test_infer_username_personal_repo_only(self):
        """개인 레포 URL만 사용 (조직 레포 건너뜀)"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        # Mock get_account_type
        async def mock_get_account_type(username):
            if username == "42cats":
                return {"username": "42cats", "type": "Organization", "error": None}
            elif username == "sabyunrepo":
                return {"username": "sabyunrepo", "type": "User", "error": None}
            return {"username": username, "type": "unknown", "error": "not_found"}

        with patch.object(svc, "get_account_type", side_effect=mock_get_account_type):
            result = await svc.infer_candidate_username(
                github_urls=[
                    "https://github.com/42cats/crime-cat",  # Organization
                    "https://github.com/sabyunrepo/Sesami",  # User (sabyunrepo 계정)
                ],
                candidate_name="BYUN SANGHOON",
            )

            assert result["username"] == "sabyunrepo"
            assert result["confidence"] == "high"
            assert "https://github.com/42cats/crime-cat" in result["skipped_org_repos"]
            assert "https://github.com/sabyunrepo/Sesami" in result["personal_repos"]

    @pytest.mark.asyncio
    async def test_infer_username_real_api_call(self):
        """실제 GitHub API 호출 테스트 (sabyunrepo 계정)"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        # 실제 API 호출 (인증 없이 공개 API)
        result = await svc.get_account_type("sabyunrepo")

        # sabyunrepo는 User 타입
        assert result["username"] == "sabyunrepo"
        assert result["type"] == "User"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_infer_username_no_personal_repos(self):
        """개인 레포가 없으면 username None"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        async def mock_get_account_type(username):
            return {"username": username, "type": "Organization", "error": None}

        with patch.object(svc, "get_account_type", side_effect=mock_get_account_type):
            result = await svc.infer_candidate_username(
                github_urls=["https://github.com/org1/repo", "https://github.com/org2/repo"],
            )

            assert result["username"] is None
            assert result["confidence"] == "none"
            assert len(result["skipped_org_repos"]) == 2
            assert len(result["personal_repos"]) == 0


# ============================================================
# P0-06: available_analyses 결정
# ============================================================

class TestAvailableAnalysesDecision:
    """P0-06: 사용 가능한 분석 결정 테스트"""

    @pytest.mark.asyncio
    async def test_jd_only_analysis(self):
        """JD만 있을 때"""
        from app.workflows.activities.input_enrichment import enrich_input
        from unittest.mock import patch

        input_data = {
            "jd_text": "Test JD",
            "resume_path": None,
            "portfolio_path": None,
            "cover_letter_path": None,
            "linkedin_url": None,
            "github_urls": [],
        }

        with patch("app.workflows.activities.input_enrichment.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await enrich_input(input_data)

            assert "jd_analysis" in result["available_analyses"]
            assert "document_analysis" not in result["available_analyses"]
            assert "code_analysis" not in result["available_analyses"]

    @pytest.mark.asyncio
    async def test_all_analyses_available(self):
        """모든 분석 가능할 때"""
        from app.workflows.activities.input_enrichment import enrich_input
        from unittest.mock import patch

        input_data = {
            "jd_text": "Test JD",
            "resume_path": "/tmp/resume.pdf",  # 문서 있음
            "portfolio_path": None,
            "cover_letter_path": None,
            "linkedin_url": None,
            "github_urls": ["https://github.com/user/repo"],  # GitHub 있음
        }

        # Mock 설정
        async def mock_extract_text(path):
            return "Mock resume content with GitHub: https://github.com/user/repo"

        async def mock_get_account_type(username):
            return {"username": username, "type": "User", "error": None}

        async def mock_infer_username(github_urls, candidate_name=None):
            return {
                "username": "user",
                "confidence": "high",
                "personal_repos": github_urls,
                "skipped_org_repos": [],
            }

        # extract_text는 함수 내부에서 동적으로 import되므로 소스 모듈을 mock
        with patch("app.workflows.activities.input_enrichment.activity") as mock_activity, \
             patch("app.services.document_parser.extract_text", side_effect=mock_extract_text), \
             patch("app.services.github_service.GitHubService.get_account_type", side_effect=mock_get_account_type), \
             patch("app.services.github_service.GitHubService.infer_candidate_username", side_effect=mock_infer_username):

            mock_activity.heartbeat = MagicMock()

            result = await enrich_input(input_data)

            assert "jd_analysis" in result["available_analyses"]
            # document_analysis는 resume_path가 있으면 포함
            # code_analysis는 personal_repos가 있으면 포함

    @pytest.mark.asyncio
    async def test_code_analysis_disabled_without_personal_repos(self):
        """개인 레포 없으면 code_analysis 비활성화"""
        from app.workflows.activities.input_enrichment import enrich_input
        from unittest.mock import patch

        input_data = {
            "jd_text": "Test JD",
            "github_urls": ["https://github.com/org/repo"],  # 조직 레포만
        }

        async def mock_infer_username(github_urls, candidate_name=None):
            return {
                "username": None,
                "confidence": "none",
                "personal_repos": [],  # 개인 레포 없음
                "skipped_org_repos": github_urls,
            }

        with patch("app.workflows.activities.input_enrichment.activity") as mock_activity, \
             patch("app.services.github_service.GitHubService.infer_candidate_username", side_effect=mock_infer_username):

            mock_activity.heartbeat = MagicMock()

            result = await enrich_input(input_data)

            assert "code_analysis" not in result["available_analyses"]


# ============================================================
# P0-07: 문서 파싱 실패 graceful 처리
# ============================================================

class TestGracefulDocumentParsingFailure:
    """P0-07: 문서 파싱 실패 시 graceful 처리 테스트"""

    @pytest.mark.asyncio
    async def test_resume_parse_failure_continues(self):
        """이력서 파싱 실패해도 계속 진행"""
        from app.workflows.activities.input_enrichment import enrich_input
        from unittest.mock import patch

        input_data = {
            "jd_text": "Test JD",
            "resume_path": "/tmp/corrupted.pdf",
            "linkedin_url": "https://www.linkedin.com/in/test-user",
        }

        async def mock_extract_text(path):
            raise ValueError("All parsers failed for: /tmp/corrupted.pdf")

        mock_linkedin_profile = {
            "profile_url": "https://www.linkedin.com/in/test-user",
            "full_name": "Test User",
            "github_url": None,
        }

        # extract_text는 함수 내부에서 동적으로 import되므로 소스 모듈을 mock
        with patch("app.workflows.activities.input_enrichment.activity") as mock_activity, \
             patch("app.services.document_parser.extract_text", side_effect=mock_extract_text), \
             patch("app.services.linkedin_service.LinkedInService.get_profile", return_value=mock_linkedin_profile):

            mock_activity.heartbeat = MagicMock()

            result = await enrich_input(input_data)

            # 파싱 실패해도 결과 반환
            assert result is not None
            # document_errors에 실패 기록
            assert len(result.get("document_errors", [])) >= 1
            assert result["document_errors"][0]["source"] == "resume"
            # LinkedIn은 성공
            assert result.get("linkedin_profile") is not None

    @pytest.mark.asyncio
    async def test_all_documents_fail_continues(self):
        """모든 문서 파싱 실패해도 계속 진행"""
        from app.workflows.activities.input_enrichment import enrich_input
        from unittest.mock import patch

        input_data = {
            "jd_text": "Test JD",
            "resume_path": "/tmp/bad1.pdf",
            "portfolio_path": "/tmp/bad2.pdf",
            "cover_letter_path": "/tmp/bad3.pdf",
        }

        async def mock_extract_text(path):
            raise ValueError(f"All parsers failed for: {path}")

        # extract_text는 함수 내부에서 동적으로 import되므로 소스 모듈을 mock
        with patch("app.workflows.activities.input_enrichment.activity") as mock_activity, \
             patch("app.services.document_parser.extract_text", side_effect=mock_extract_text):

            mock_activity.heartbeat = MagicMock()

            result = await enrich_input(input_data)

            # 모두 실패해도 결과 반환
            assert result is not None
            # 3개 모두 기록
            assert len(result.get("document_errors", [])) == 3
            # JD 분석은 여전히 가능
            assert "jd_analysis" in result["available_analyses"]


# ============================================================
# 통합 테스트
# ============================================================

class TestInputEnrichmentIntegration:
    """Input Enrichment Activity 통합 테스트"""

    def test_activity_is_defn(self):
        """Activity 데코레이터 확인"""
        from app.workflows.activities.input_enrichment import enrich_input
        assert hasattr(enrich_input, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_minimal_input(self):
        """최소 입력 (JD만)"""
        from app.workflows.activities.input_enrichment import enrich_input
        from unittest.mock import patch

        input_data = {"jd_text": "Simple JD for testing"}

        with patch("app.workflows.activities.input_enrichment.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await enrich_input(input_data)

            assert result["raw_input"] == input_data
            assert result["github_urls"] == []
            assert result["linkedin_profile"] is None
            assert "jd_analysis" in result["available_analyses"]

    @pytest.mark.asyncio
    async def test_output_structure(self):
        """출력 구조 검증"""
        from app.workflows.activities.input_enrichment import enrich_input
        from unittest.mock import patch

        input_data = {"jd_text": "Test JD"}

        with patch("app.workflows.activities.input_enrichment.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await enrich_input(input_data)

            # 필수 필드 확인
            required_fields = [
                "raw_input",
                "github_urls",
                "candidate_github_username",
                "linkedin_profile",
                "extraction_sources",
                "available_analyses",
                "document_errors",
            ]
            for field in required_fields:
                assert field in result, f"Missing field: {field}"
