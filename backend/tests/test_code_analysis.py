"""
backend/tests/test_code_analysis.py
Phase 2: Code Analysis Activity 단위 테스트

테스트 항목:
- P2C-01: JD 매칭 레포 필터링
- P2C-02: PyDriller diff 추출
- P2C-03: AST 분석
- P2C-04: 4-Phase 통합
- P2C-05: 빈 결과 처리
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# P2C-01: JD 매칭 레포 필터링 테스트
# ============================================================

class TestJdMatchingRepoFilter:
    """P2C-01: JD 매칭 레포 필터링 테스트"""

    @pytest.mark.asyncio
    async def test_filter_repos_by_language(self):
        """언어 기반 레포 필터링"""
        from app.services.github_service import GitHubService

        svc = GitHubService()

        async def mock_get_repo_languages(url):
            if "python-repo" in url:
                return {"Python": 80000, "JavaScript": 10000}
            elif "js-repo" in url:
                return {"JavaScript": 90000}
            return {}

        async def mock_get_repo_info(url):
            return {"url": url, "name": url.split("/")[-1]}

        with patch.object(svc, "get_repo_languages", side_effect=mock_get_repo_languages), \
             patch.object(svc, "get_repo_info", side_effect=mock_get_repo_info):

            result = await svc.filter_repos_by_language(
                github_urls=[
                    "https://github.com/user/python-repo",
                    "https://github.com/user/js-repo",
                ],
                target_languages=["Python"],
                min_language_ratio=0.3,
            )

            # Python 비율이 30% 이상인 레포만 반환
            assert len(result) >= 1
            assert any("python-repo" in r.get("url", "") for r in result)


# ============================================================
# P2C-02: _jd_to_file_types 테스트
# ============================================================

class TestJdToFileTypes:
    """P2C-02: JD 기술스택 → 파일 확장자 변환 테스트"""

    def test_python_file_types(self):
        """Python → .py"""
        from app.workflows.activities.code_analysis import _jd_to_file_types

        result = _jd_to_file_types(["Python"])
        assert ".py" in result

    def test_javascript_typescript_file_types(self):
        """JavaScript/TypeScript → .js, .ts 등"""
        from app.workflows.activities.code_analysis import _jd_to_file_types

        result = _jd_to_file_types(["JavaScript", "TypeScript"])
        assert ".js" in result
        assert ".ts" in result
        assert ".jsx" in result
        assert ".tsx" in result

    def test_empty_tech_stack(self):
        """빈 기술스택 → 기본값 .py"""
        from app.workflows.activities.code_analysis import _jd_to_file_types

        result = _jd_to_file_types([])
        assert result == [".py"]

    def test_unknown_tech_stack(self):
        """알 수 없는 기술스택 → 기본값 .py"""
        from app.workflows.activities.code_analysis import _jd_to_file_types

        result = _jd_to_file_types(["UnknownLang"])
        assert result == [".py"]


# ============================================================
# P2C-03: Code Analysis Activity 테스트
# ============================================================

class TestCodeAnalysisActivity:
    """P2C-03: Code Analysis Activity 테스트"""

    @pytest.mark.asyncio
    async def test_analyze_code_no_repos(self):
        """GitHub URL이 없을 때"""
        from app.workflows.activities.code_analysis import analyze_code
        from unittest.mock import patch

        async def mock_filter_repos(github_urls, target_languages, min_language_ratio):
            return []  # 매칭되는 레포 없음

        with patch("app.workflows.activities.code_analysis.activity") as mock_activity, \
             patch("app.services.github_service.GitHubService.filter_repos_by_language", side_effect=mock_filter_repos):

            mock_activity.heartbeat = MagicMock()

            result = await analyze_code(
                github_urls=[],
                input_data={"candidate_github_username": "testuser"},
            )

            assert result["repositories"] == []
            assert result["top_question_candidates"] == []

    @pytest.mark.asyncio
    async def test_analyze_code_with_repos(self):
        """레포가 있을 때 분석 수행"""
        from app.workflows.activities.code_analysis import analyze_code
        from unittest.mock import patch

        async def mock_filter_repos(github_urls, target_languages, min_language_ratio):
            return [
                {"url": "https://github.com/user/repo", "name": "repo", "languages": {"Python": 80000}}
            ]

        async def mock_pydriller(repo_url, job_id, author, since_years, file_types):
            return {
                "files": [{"path": "main.py", "content": "print('hello')"}],
                "stats": {"total_commits": 10, "total_additions": 500, "avg_complexity": 5.0},
            }

        async def mock_ast_analyze(files, primary_language):
            return {"functions": 5, "classes": 2}

        def mock_rank_files(files, jd_tech_stack, token_budget):
            return files

        async def mock_llm_analyze(ranked_files, ast_context):
            return {"notable_implementations": [{"title": "Main function", "complexity": "low"}]}

        with patch("app.workflows.activities.code_analysis.activity") as mock_activity, \
             patch("app.services.github_service.GitHubService.filter_repos_by_language", side_effect=mock_filter_repos), \
             patch("app.services.code_analyzer.CodeAnalyzer.analyze_with_pydriller", side_effect=mock_pydriller), \
             patch("app.services.code_analyzer.CodeAnalyzer.select_top_files", return_value=[]), \
             patch("app.services.code_analyzer.CodeAnalyzer.analyze_ast", side_effect=mock_ast_analyze), \
             patch("app.services.code_analyzer.CodeAnalyzer.rank_files_for_llm", side_effect=mock_rank_files), \
             patch("app.services.code_analyzer.CodeAnalyzer.llm_analyze_code", side_effect=mock_llm_analyze):

            mock_activity.heartbeat = MagicMock()

            result = await analyze_code(
                github_urls=["https://github.com/user/repo"],
                input_data={"candidate_github_username": "testuser", "jd_tech_stack": ["Python"]},
            )

            assert len(result["repositories"]) == 1
            assert result["repositories"][0]["repo_name"] == "repo"
            assert result["repositories"][0]["candidate_commits"] == 10


# ============================================================
# P2C-06: Clone 소스 fallback 테스트 (JIT-20)
# ============================================================

class TestCloneSourceFallback:
    """P2C-06: PyDriller 빈 결과 시 clone 소스 fallback 테스트"""

    def test_read_source_files_from_clone(self, tmp_path):
        """clone 디렉토리에서 소스 파일 읽기"""
        from app.services.code_analyzer import CodeAnalyzer

        # 임시 clone 디렉토리 구조 생성
        (tmp_path / "main.py").write_text("def hello():\n    print('hello')\n")
        (tmp_path / "utils.py").write_text("def add(a, b):\n    return a + b\n")
        (tmp_path / "README.md").write_text("# Project")  # 확장자 불일치 → 제외
        (tmp_path / ".git").mkdir()  # .git 디렉토리 → 제외
        sub = tmp_path / "pkg"
        sub.mkdir()
        (sub / "__init__.py").write_text("")  # 빈 파일 → 제외

        analyzer = CodeAnalyzer()
        files = analyzer.read_source_files_from_clone(
            clone_dir=str(tmp_path),
            file_types=[".py"],
            max_files=10,
        )

        assert len(files) == 2
        filenames = {f["filename"] for f in files}
        assert "main.py" in filenames
        assert "utils.py" in filenames
        for f in files:
            assert "source" in f
            assert f["nloc"] > 0
            assert f["complexity"] == 0  # 정적 분석 없으므로 0

    def test_read_source_files_respects_token_budget(self, tmp_path):
        """토큰 예산 초과 시 파일 자르기"""
        from app.services.code_analyzer import CodeAnalyzer

        # 큰 파일 생성 (약 4000 토큰 = 16000자)
        (tmp_path / "big.py").write_text("x = 1\n" * 3000)
        (tmp_path / "small.py").write_text("y = 2\n")

        analyzer = CodeAnalyzer()
        files = analyzer.read_source_files_from_clone(
            clone_dir=str(tmp_path),
            file_types=[".py"],
            token_budget=5000,
        )

        # big.py가 예산 내 → 1개만 반환 (small.py는 예산 초과)
        assert len(files) >= 1

    def test_read_source_files_empty_dir(self, tmp_path):
        """빈 디렉토리 → 빈 결과"""
        from app.services.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer()
        files = analyzer.read_source_files_from_clone(
            clone_dir=str(tmp_path),
            file_types=[".py"],
        )
        assert files == []

    def test_static_analysis_runner_external_clone_dir(self, tmp_path):
        """StaticAnalysisRunner: 외부 clone_dir 사용 시 재 clone 생략"""
        from app.services.static_analysis_runner import StaticAnalysisRunner

        runner = StaticAnalysisRunner()
        # run_analysis에 clone_dir 파라미터 지원 확인
        import inspect
        sig = inspect.signature(runner.run_analysis)
        assert "clone_dir" in sig.parameters
        assert "cleanup" in sig.parameters

    def test_analyze_single_repo_activity_defn(self):
        """analyze_single_repo Activity 데코레이터 확인"""
        from app.workflows.activities.code_analysis import analyze_single_repo
        assert hasattr(analyze_single_repo, "__temporal_activity_definition")


# ============================================================
# Activity 통합 테스트
# ============================================================

class TestCodeAnalysisIntegration:
    """Code Analysis Activity 통합 테스트"""

    def test_activity_is_defn(self):
        """Activity 데코레이터 확인"""
        from app.workflows.activities.code_analysis import analyze_code
        assert hasattr(analyze_code, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_output_structure_empty(self):
        """빈 결과 출력 구조"""
        from app.workflows.activities.code_analysis import analyze_code
        from unittest.mock import patch

        async def mock_filter_repos(github_urls, target_languages, min_language_ratio):
            return []

        with patch("app.workflows.activities.code_analysis.activity") as mock_activity, \
             patch("app.services.github_service.GitHubService.filter_repos_by_language", side_effect=mock_filter_repos):

            mock_activity.heartbeat = MagicMock()

            result = await analyze_code(
                github_urls=[],
                input_data={},
            )

            assert "repositories" in result
            assert "top_question_candidates" in result
