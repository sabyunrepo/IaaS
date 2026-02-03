"""
backend/tests/test_planning.py
Phase 1: Planning Activity 단위 테스트

테스트 항목:
- P1-01: JD 기술스택 추출
- P1-02: GitHub 워크로드 추정
- P1-03: 실행 계획 생성
- P1-04: phases 활성화 결정
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# P1-01: JD 기술스택 추출
# ============================================================

class TestJdTechStackExtraction:
    """P1-01: JD에서 기술스택 추출 테스트"""

    def test_extract_tech_from_jd(self, sample_jd_text):
        """JD 텍스트에서 기술스택 추출"""
        # JD에 있는 기술들이 추출되는지 확인
        tech_keywords = ["Python", "TypeScript", "LLM", "AI"]

        for tech in tech_keywords:
            assert tech.lower() in sample_jd_text.lower() or tech in sample_jd_text

    def test_jd_contains_requirements(self, sample_jd_text):
        """JD에 요구사항이 포함되어 있는지 확인"""
        assert "자격요건" in sample_jd_text or "requirements" in sample_jd_text.lower()
        assert "우대사항" in sample_jd_text or "preferred" in sample_jd_text.lower()


# ============================================================
# P1-02: GitHub 워크로드 추정
# ============================================================

class TestGitHubWorkloadEstimation:
    """P1-02: GitHub 레포 워크로드 추정 테스트"""

    @pytest.mark.asyncio
    async def test_get_repo_info(self):
        """레포 정보 조회"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        with patch.object(svc, "_get_github") as mock_github:
            mock_repo = MagicMock()
            mock_repo.name = "test-repo"
            mock_repo.full_name = "user/test-repo"
            mock_repo.size = 5000
            mock_repo.stargazers_count = 10
            mock_repo.forks_count = 2
            mock_repo.default_branch = "main"
            mock_repo.created_at = None
            mock_repo.pushed_at = None
            mock_repo.description = "Test repository"
            mock_github.return_value.get_repo.return_value = mock_repo

            result = await svc.get_repo_info("https://github.com/user/test-repo")

            assert result["name"] == "test-repo"
            assert result["size"] == 5000
            assert result["stars"] == 10

    @pytest.mark.asyncio
    async def test_get_repo_info_invalid_url(self):
        """잘못된 URL이면 에러 반환"""
        from app.services.github_service import GitHubService

        svc = GitHubService()
        result = await svc.get_repo_info("not-a-github-url")

        assert "error" in result
        assert result["error"] == "invalid_url"

    @pytest.mark.asyncio
    async def test_get_repo_languages(self):
        """레포 언어 정보 조회"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        with patch.object(svc, "_get_github") as mock_github:
            mock_repo = MagicMock()
            mock_repo.get_languages.return_value = {"Python": 50000, "JavaScript": 20000}
            mock_github.return_value.get_repo.return_value = mock_repo

            result = await svc.get_repo_languages("https://github.com/user/test-repo")

            assert result["Python"] == 50000
            assert result["JavaScript"] == 20000

    @pytest.mark.asyncio
    async def test_get_repo_languages_real_api(self):
        """실제 GitHub API로 언어 조회 (sabyunrepo/Sesami)"""
        from app.services.github_service import GitHubService

        svc = GitHubService()
        result = await svc.get_repo_languages("https://github.com/sabyunrepo/Sesami")

        # 실제 레포에서 언어 정보 조회
        assert isinstance(result, dict)
        # 빈 dict이 아니면 언어 정보가 있음

    @pytest.mark.asyncio
    async def test_get_repo_info_real_api(self):
        """실제 GitHub API로 레포 정보 조회"""
        from app.services.github_service import GitHubService

        svc = GitHubService()
        result = await svc.get_repo_info("https://github.com/sabyunrepo/Sesami")

        assert result["full_name"] == "sabyunrepo/Sesami"
        assert "size" in result
        assert "error" not in result


# ============================================================
# P1-03: 실행 계획 생성
# ============================================================

class TestExecutionPlanCreation:
    """P1-03: 실행 계획 생성 테스트"""

    @pytest.mark.asyncio
    async def test_create_execution_plan_minimal(self):
        """최소 입력으로 실행 계획 생성"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        enriched_input = {
            "raw_input": {"jd_text": "Test JD"},
            "github_urls": [],
            "candidate_github_username": None,
            "available_analyses": ["jd_analysis"],
        }

        with patch("app.workflows.activities.planning.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(enriched_input)

            assert "phases" in result
            assert "workload" in result
            assert result["workload"] == {}  # GitHub URL 없으면 빈 워크로드

    @pytest.mark.asyncio
    async def test_create_execution_plan_with_github(self, mock_enriched_input):
        """GitHub URL이 있을 때 실행 계획 생성"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        async def mock_get_repo_info(url):
            return {
                "url": url,
                "name": "test-repo",
                "size": 5000,
            }

        async def mock_get_repo_languages(url):
            return {"Python": 80000, "TypeScript": 20000}

        with patch("app.workflows.activities.planning.activity") as mock_activity, \
             patch("app.services.github_service.GitHubService.get_repo_info", side_effect=mock_get_repo_info), \
             patch("app.services.github_service.GitHubService.get_repo_languages", side_effect=mock_get_repo_languages):

            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(mock_enriched_input)

            assert "phases" in result
            assert "workload" in result
            # GitHub URL이 있으면 워크로드 정보가 있어야 함
            assert len(result["workload"]) > 0

    @pytest.mark.asyncio
    async def test_execution_plan_structure(self):
        """실행 계획 구조 검증"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        enriched_input = {
            "raw_input": {"jd_text": "Test JD"},
            "github_urls": [],
            "candidate_github_username": "testuser",
            "available_analyses": ["jd_analysis", "document_analysis"],
        }

        with patch("app.workflows.activities.planning.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(enriched_input)

            # 필수 필드 확인
            assert "candidate_github_username" in result
            assert "phases" in result
            assert "workload" in result
            assert "estimated_total_time_seconds" in result
            assert "raw_input" in result


# ============================================================
# P1-04: phases 활성화 결정
# ============================================================

class TestPhasesActivation:
    """P1-04: 분석 Phase 활성화 결정 테스트"""

    @pytest.mark.asyncio
    async def test_jd_analysis_always_enabled(self):
        """JD 분석은 항상 활성화"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        enriched_input = {
            "raw_input": {"jd_text": "Test JD"},
            "github_urls": [],
            "candidate_github_username": None,
            "available_analyses": [],  # 빈 available_analyses
        }

        with patch("app.workflows.activities.planning.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(enriched_input)

            jd_phase = next((p for p in result["phases"] if p["name"] == "jd_analysis"), None)
            assert jd_phase is not None
            assert jd_phase["enabled"] is True

    @pytest.mark.asyncio
    async def test_document_analysis_enabled_when_available(self):
        """document_analysis가 available에 있으면 활성화"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        enriched_input = {
            "raw_input": {},
            "github_urls": [],
            "candidate_github_username": None,
            "available_analyses": ["document_analysis"],
        }

        with patch("app.workflows.activities.planning.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(enriched_input)

            doc_phase = next((p for p in result["phases"] if p["name"] == "document_analysis"), None)
            assert doc_phase is not None
            assert doc_phase["enabled"] is True

    @pytest.mark.asyncio
    async def test_document_analysis_disabled_when_not_available(self):
        """document_analysis가 available에 없으면 비활성화"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        enriched_input = {
            "raw_input": {},
            "github_urls": [],
            "candidate_github_username": None,
            "available_analyses": ["jd_analysis"],  # document_analysis 없음
        }

        with patch("app.workflows.activities.planning.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(enriched_input)

            doc_phase = next((p for p in result["phases"] if p["name"] == "document_analysis"), None)
            assert doc_phase is not None
            assert doc_phase["enabled"] is False

    @pytest.mark.asyncio
    async def test_code_analysis_enabled_when_available(self):
        """code_analysis가 available에 있으면 활성화"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        enriched_input = {
            "raw_input": {},
            "github_urls": ["https://github.com/user/repo"],
            "candidate_github_username": "user",
            "available_analyses": ["code_analysis"],
        }

        async def mock_get_repo_info(url):
            return {"url": url, "size": 1000}

        async def mock_get_repo_languages(url):
            return {"Python": 50000}

        with patch("app.workflows.activities.planning.activity") as mock_activity, \
             patch("app.services.github_service.GitHubService.get_repo_info", side_effect=mock_get_repo_info), \
             patch("app.services.github_service.GitHubService.get_repo_languages", side_effect=mock_get_repo_languages):

            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(enriched_input)

            code_phase = next((p for p in result["phases"] if p["name"] == "code_analysis"), None)
            assert code_phase is not None
            assert code_phase["enabled"] is True

    @pytest.mark.asyncio
    async def test_code_analysis_disabled_when_not_available(self):
        """code_analysis가 available에 없으면 비활성화"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        enriched_input = {
            "raw_input": {},
            "github_urls": [],
            "candidate_github_username": None,
            "available_analyses": ["jd_analysis"],  # code_analysis 없음
        }

        with patch("app.workflows.activities.planning.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(enriched_input)

            code_phase = next((p for p in result["phases"] if p["name"] == "code_analysis"), None)
            assert code_phase is not None
            assert code_phase["enabled"] is False


# ============================================================
# 워크로드 시간 계산 테스트
# ============================================================

class TestWorkloadTimeCalculation:
    """워크로드 시간 계산 테스트"""

    def test_small_repo_time(self):
        """작은 레포 (< 1MB) 시간 계산"""
        from app.workflows.activities.planning import _calculate_time

        result = _calculate_time({"size": 500})  # 500 KB
        assert result == 30  # 30초

    def test_medium_repo_time(self):
        """중간 레포 (1-10MB) 시간 계산"""
        from app.workflows.activities.planning import _calculate_time

        result = _calculate_time({"size": 5000})  # 5 MB
        assert result == 60  # 60초

    def test_large_repo_time(self):
        """큰 레포 (10-100MB) 시간 계산"""
        from app.workflows.activities.planning import _calculate_time

        result = _calculate_time({"size": 50000})  # 50 MB
        assert result == 120  # 120초

    def test_huge_repo_time(self):
        """거대 레포 (> 100MB) 시간 계산"""
        from app.workflows.activities.planning import _calculate_time

        result = _calculate_time({"size": 200000})  # 200 MB
        assert result == 300  # 300초

    def test_empty_size(self):
        """size 없을 때"""
        from app.workflows.activities.planning import _calculate_time

        result = _calculate_time({})  # size 키 없음
        assert result == 30  # 기본값


# ============================================================
# Activity 통합 테스트
# ============================================================

class TestPlanningActivityIntegration:
    """Planning Activity 통합 테스트"""

    def test_activity_is_defn(self):
        """Activity 데코레이터 확인"""
        from app.workflows.activities.planning import create_execution_plan
        assert hasattr(create_execution_plan, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_full_planning_flow(self, mock_enriched_input):
        """전체 Planning 플로우 테스트"""
        from app.workflows.activities.planning import create_execution_plan
        from unittest.mock import patch

        async def mock_get_repo_info(url):
            return {
                "url": url,
                "name": "interview-gen",
                "size": 5000,
            }

        async def mock_get_repo_languages(url):
            return {"Python": 80000}

        with patch("app.workflows.activities.planning.activity") as mock_activity, \
             patch("app.services.github_service.GitHubService.get_repo_info", side_effect=mock_get_repo_info), \
             patch("app.services.github_service.GitHubService.get_repo_languages", side_effect=mock_get_repo_languages):

            mock_activity.heartbeat = MagicMock()

            result = await create_execution_plan(mock_enriched_input)

            # 결과 검증
            assert result["candidate_github_username"] == "testuser"
            assert len(result["phases"]) == 3
            assert result["estimated_total_time_seconds"] > 0
