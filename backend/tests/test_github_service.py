"""
backend/tests/test_github_service.py
GitHubService 단위 테스트

테스트 항목:
- get_repo_languages: PyGithub 2.9.x url 키 leak 방어 (sanitizer)
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.github_service import GitHubService


class TestGetRepoLanguagesSanitizer:
    """get_repo_languages: PyGithub 2.9.x url 키 leak 방어"""

    @pytest.mark.asyncio
    async def test_drops_non_int_values_from_pygithub_leak(self):
        """PyGithub 2.9.x가 반환 dict에 추가하는 'url' (str) 키를 필터링"""
        svc = GitHubService()

        # PyGithub 2.9.x 실제 버그 재현: int 언어 바이트와 str 'url' 혼재
        polluted = {
            "JavaScript": 37951,
            "HTML": 845,
            "url": "https://api.github.com/repos/owner/repo/languages",
        }
        mock_repo = MagicMock()
        mock_repo.get_languages.return_value = polluted
        mock_gh = MagicMock()
        mock_gh.get_repo.return_value = mock_repo

        with patch.object(svc, "_get_github", return_value=mock_gh):
            result = await svc.get_repo_languages(
                "https://github.com/owner/repo"
            )

        # str 'url' 키는 제거되어야 함
        assert "url" not in result
        assert result == {"JavaScript": 37951, "HTML": 845}

        # 다운스트림 sum(values())가 TypeError 없이 동작함을 확인
        assert sum(result.values()) == 38796

    @pytest.mark.asyncio
    async def test_clean_dict_unchanged(self):
        """leak이 없는 정상 응답은 그대로 반환"""
        svc = GitHubService()

        clean = {"Python": 100000, "Shell": 500}
        mock_repo = MagicMock()
        mock_repo.get_languages.return_value = clean
        mock_gh = MagicMock()
        mock_gh.get_repo.return_value = mock_repo

        with patch.object(svc, "_get_github", return_value=mock_gh):
            result = await svc.get_repo_languages(
                "https://github.com/owner/repo"
            )

        assert result == clean
