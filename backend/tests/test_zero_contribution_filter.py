"""Zero-Contribution 레포 필터링 + 기여도 검증 유닛 테스트 (JIT-39).

테스트 시나리오:
1. 정상 레포: 커밋 10개 → contributions=10, 결과에 포함
2. Zero 레포: author 매칭 후 커밋 0개 → 결과에서 제외 + 로그 기록
3. 정합성 불일치: contributions=5이지만 SHA 3개 → 경고 + 3으로 보정
4. 전체 레포 Zero: 모든 레포 기여도 0 → 원본 유지 fallback
5. Langfuse 검증: breakdown에 repo_contribution_breakdown 메타데이터 존재
"""

import pytest

from app.services.github_service import GitHubService


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def normal_repo() -> dict:
    """정상 기여 레포 (커밋 10개)."""
    return {
        "repo_name": "my-project",
        "repo_url": "https://github.com/user/my-project",
        "candidate_commits": 10,
        "commit_count": 10,
        "monthly_contributions": [2, 1, 3, 0, 1, 0, 0, 1, 0, 2, 0, 0],
        "analysis": {"tech_stack": ["Python"], "patterns": []},
        "notable_implementations": [],
    }


@pytest.fixture
def zero_repo() -> dict:
    """Zero-contribution 레포 (author 매칭 후 커밋 0개)."""
    return {
        "repo_name": "forked-repo",
        "repo_url": "https://github.com/org/forked-repo",
        "candidate_commits": 0,
        "commit_count": 0,
        "monthly_contributions": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "analysis": {"tech_stack": ["JavaScript"], "patterns": []},
        "notable_implementations": [],
    }


@pytest.fixture
def mismatched_repo() -> dict:
    """정합성 불일치 레포 (contributions=5, 실제 SHA=3)."""
    return {
        "repo_name": "partial-repo",
        "repo_url": "https://github.com/user/partial-repo",
        "candidate_commits": 5,
        "commit_count": 5,
        "monthly_contributions": [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "analysis": {"tech_stack": ["TypeScript"], "patterns": []},
        "notable_implementations": [],
    }


# ──────────────────────────────────────────────
# Test: validate_repo_contributions
# ──────────────────────────────────────────────

class TestValidateRepoContributions:
    """GitHubService.validate_repo_contributions() 유닛 테스트."""

    def test_normal_repo_valid(self, normal_repo):
        """시나리오 1: 정상 레포 — contributions=10, 결과에 포함."""
        result = GitHubService.validate_repo_contributions(normal_repo)

        assert result["is_zero_contribution"] is False
        assert result["original_contributions"] == 10
        assert result["validated_contributions"] == 10
        assert result["correction_applied"] is False
        assert result["correction_reason"] is None
        assert result["repo_name"] == "my-project"

    def test_zero_contribution_detected(self, zero_repo):
        """시나리오 2: Zero 레포 — 커밋 0개 → is_zero_contribution=True."""
        result = GitHubService.validate_repo_contributions(zero_repo)

        assert result["is_zero_contribution"] is True
        assert result["original_contributions"] == 0
        assert result["validated_contributions"] == 0
        assert result["repo_name"] == "forked-repo"

    def test_contribution_mismatch_corrected(self, mismatched_repo):
        """시나리오 3: 정합성 불일치 — contributions=5, SHA=3 → 3으로 보정."""
        result = GitHubService.validate_repo_contributions(mismatched_repo)

        assert result["is_zero_contribution"] is False
        assert result["original_contributions"] == 5
        assert result["validated_contributions"] == 3
        assert result["correction_applied"] is True
        assert "mismatch" in result["correction_reason"]
        assert "reported=5" in result["correction_reason"]
        assert "actual_sha_count=3" in result["correction_reason"]

    def test_empty_monthly_fallback(self):
        """monthly_contributions 없을 때 candidate_commits fallback."""
        repo = {
            "repo_name": "no-monthly",
            "candidate_commits": 7,
            "monthly_contributions": [],
        }
        result = GitHubService.validate_repo_contributions(repo)

        # monthly 빈 리스트 → sum=0 → candidate_commits(7) 사용
        assert result["validated_contributions"] == 7
        assert result["is_zero_contribution"] is False

    def test_no_monthly_key(self):
        """monthly_contributions 키 자체가 없을 때."""
        repo = {
            "repo_name": "no-key",
            "candidate_commits": 5,
        }
        result = GitHubService.validate_repo_contributions(repo)

        assert result["validated_contributions"] == 5
        assert result["is_zero_contribution"] is False


# ──────────────────────────────────────────────
# Test: Zero-contribution 필터링 통합 로직
# ──────────────────────────────────────────────

class TestZeroContributionFiltering:
    """code_analysis.py의 필터링 로직을 시뮬레이션하는 통합 테스트."""

    def test_mixed_repos_filtering(self, normal_repo, zero_repo, mismatched_repo):
        """정상 + Zero + 불일치 혼합 → Zero만 제외."""
        repositories = [normal_repo, zero_repo, mismatched_repo]

        filtered = []
        breakdown = []
        zero_count = 0

        for repo in repositories:
            v = GitHubService.validate_repo_contributions(repo)
            breakdown.append(v)
            if v["is_zero_contribution"]:
                zero_count += 1
                continue
            if v["correction_applied"]:
                repo["candidate_commits"] = v["validated_contributions"]
                repo["commit_count"] = v["validated_contributions"]
            filtered.append(repo)

        assert len(filtered) == 2
        assert zero_count == 1
        assert filtered[0]["repo_name"] == "my-project"
        assert filtered[1]["repo_name"] == "partial-repo"
        # 보정 확인
        assert filtered[1]["candidate_commits"] == 3

    def test_all_zero_fallback(self, zero_repo):
        """시나리오 4: 전체 레포 Zero → 원본 유지 fallback."""
        zero_repo2 = {**zero_repo, "repo_name": "another-zero"}
        repositories = [zero_repo, zero_repo2]

        filtered = []
        for repo in repositories:
            v = GitHubService.validate_repo_contributions(repo)
            if not v["is_zero_contribution"]:
                filtered.append(repo)

        # 전체 Zero → fallback
        if not filtered and repositories:
            filtered = repositories

        assert len(filtered) == 2
        assert filtered[0]["repo_name"] == "forked-repo"

    def test_breakdown_has_all_repos(self, normal_repo, zero_repo):
        """시나리오 5: breakdown에 모든 레포(포함/제외 모두)의 검증 결과 존재."""
        repositories = [normal_repo, zero_repo]

        breakdown = []
        for repo in repositories:
            v = GitHubService.validate_repo_contributions(repo)
            breakdown.append(v)

        assert len(breakdown) == 2
        assert breakdown[0]["repo_name"] == "my-project"
        assert breakdown[0]["is_zero_contribution"] is False
        assert breakdown[1]["repo_name"] == "forked-repo"
        assert breakdown[1]["is_zero_contribution"] is True

        # Langfuse metadata 구조 검증
        for entry in breakdown:
            assert "is_zero_contribution" in entry
            assert "original_contributions" in entry
            assert "validated_contributions" in entry
            assert "correction_applied" in entry
            assert "repo_name" in entry
