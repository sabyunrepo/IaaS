"""
Funnel Selection 도메인 테스트

TDD: 테스트 먼저 작성 후 모델/규칙 구현.
3단계 퍼널 — Stage1(하드 필터) / Stage2(관련도 점수) / Stage3(유사도 임계치)
"""
import pytest
from pydantic import ValidationError

from domain.matching.models import FunnelConfig, RepoMetadata
from domain.matching.funnel_rules import (
    stage1_hard_filter,
    stage2_relevance_score,
    stage3_should_include,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_repo(
    *,
    name: str = "my-repo",
    owner: str = "alice",
    url: str = "https://github.com/alice/my-repo",
    is_fork: bool = False,
    is_org_repo: bool = False,
    days_since_push: int = 30,
    languages: list[str] | None = None,
    total_loc: int = 1000,
    detected_tech_stack: list[str] | None = None,
    user_contribution_ratio: float = 1.0,
    description: str = "",
) -> RepoMetadata:
    return RepoMetadata(
        name=name,
        owner=owner,
        url=url,
        is_fork=is_fork,
        is_org_repo=is_org_repo,
        days_since_push=days_since_push,
        languages=languages if languages is not None else ["Python"],
        total_loc=total_loc,
        detected_tech_stack=detected_tech_stack if detected_tech_stack is not None else [],
        user_contribution_ratio=user_contribution_ratio,
        description=description,
    )


def make_config(**kwargs) -> FunnelConfig:
    return FunnelConfig(**kwargs)


# ---------------------------------------------------------------------------
# RepoMetadata model tests
# ---------------------------------------------------------------------------


class TestRepoMetadata:
    def test_creation_defaults(self):
        repo = RepoMetadata(
            name="repo",
            owner="alice",
            url="https://github.com/alice/repo",
            is_fork=False,
            days_since_push=10,
        )
        assert repo.name == "repo"
        assert repo.is_org_repo is False
        assert repo.total_loc == 0
        assert repo.user_contribution_ratio == 1.0
        assert repo.languages == []
        assert repo.detected_tech_stack == []
        assert repo.description == ""

    def test_days_since_push_ge0(self):
        with pytest.raises(ValidationError):
            RepoMetadata(
                name="repo",
                owner="alice",
                url="https://github.com/alice/repo",
                is_fork=False,
                days_since_push=-1,
            )

    def test_total_loc_ge0(self):
        with pytest.raises(ValidationError):
            RepoMetadata(
                name="repo",
                owner="alice",
                url="https://github.com/alice/repo",
                is_fork=False,
                days_since_push=10,
                total_loc=-1,
            )

    def test_contribution_ratio_bounds(self):
        with pytest.raises(ValidationError):
            RepoMetadata(
                name="repo",
                owner="alice",
                url="https://github.com/alice/repo",
                is_fork=False,
                days_since_push=10,
                user_contribution_ratio=1.1,
            )
        with pytest.raises(ValidationError):
            RepoMetadata(
                name="repo",
                owner="alice",
                url="https://github.com/alice/repo",
                is_fork=False,
                days_since_push=10,
                user_contribution_ratio=-0.1,
            )


# ---------------------------------------------------------------------------
# FunnelConfig model tests
# ---------------------------------------------------------------------------


class TestFunnelConfig:
    def test_defaults(self):
        cfg = FunnelConfig()
        assert cfg.min_push_days == 365
        assert cfg.min_stars == 0
        assert cfg.max_repos == 20
        assert cfg.top_k == 5
        assert cfg.org_contribution_threshold == pytest.approx(0.10)
        assert cfg.vector_similarity_min == pytest.approx(0.60)

    def test_custom_values(self):
        cfg = FunnelConfig(min_push_days=180, top_k=3, vector_similarity_min=0.75)
        assert cfg.min_push_days == 180
        assert cfg.top_k == 3
        assert cfg.vector_similarity_min == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# Stage1: hard filter
# ---------------------------------------------------------------------------


class TestStage1HardFilter:
    def _default_config(self) -> FunnelConfig:
        return FunnelConfig(min_push_days=365)

    # --- forks removed ---
    def test_removes_forks(self):
        repos = [make_repo(is_fork=True)]
        result = stage1_hard_filter(repos, ["Python"], self._default_config())
        assert result == []

    # --- old repos removed ---
    def test_removes_old_repos(self):
        repos = [make_repo(days_since_push=400)]  # > 365
        result = stage1_hard_filter(repos, ["Python"], self._default_config())
        assert result == []

    def test_keeps_repo_at_boundary(self):
        """Exactly min_push_days should still pass (<=)."""
        repos = [make_repo(days_since_push=365)]
        result = stage1_hard_filter(repos, ["Python"], self._default_config())
        assert len(result) == 1

    # --- org contribution too low ---
    def test_removes_low_org_contribution(self):
        """Org repo with user_contribution_ratio below threshold is removed."""
        cfg = FunnelConfig(org_contribution_threshold=0.10)
        repos = [make_repo(is_org_repo=True, user_contribution_ratio=0.05)]
        result = stage1_hard_filter(repos, ["Python"], cfg)
        assert result == []

    def test_keeps_org_above_threshold(self):
        cfg = FunnelConfig(org_contribution_threshold=0.10)
        repos = [make_repo(is_org_repo=True, user_contribution_ratio=0.15)]
        result = stage1_hard_filter(repos, ["Python"], cfg)
        assert len(result) == 1

    def test_org_at_exact_threshold_kept(self):
        cfg = FunnelConfig(org_contribution_threshold=0.10)
        repos = [make_repo(is_org_repo=True, user_contribution_ratio=0.10)]
        result = stage1_hard_filter(repos, ["Python"], cfg)
        assert len(result) == 1

    def test_non_org_repo_contribution_not_checked(self):
        """Non-org repos with low contribution ratio are NOT filtered by this rule."""
        cfg = FunnelConfig(org_contribution_threshold=0.10)
        repos = [make_repo(is_org_repo=False, user_contribution_ratio=0.01)]
        result = stage1_hard_filter(repos, ["Python"], cfg)
        assert len(result) == 1

    # --- language mismatch ---
    def test_removes_language_mismatch(self):
        repos = [make_repo(languages=["JavaScript"])]
        result = stage1_hard_filter(repos, ["Python"], self._default_config())
        assert result == []

    def test_keeps_matching_language(self):
        repos = [make_repo(languages=["Python", "Shell"])]
        result = stage1_hard_filter(repos, ["Python"], self._default_config())
        assert len(result) == 1

    def test_empty_jd_languages_skips_language_check(self):
        repos = [make_repo(languages=["JavaScript"])]
        result = stage1_hard_filter(repos, [], self._default_config())
        assert len(result) == 1

    # --- keeps matching repo ---
    def test_keeps_fully_matching_repo(self):
        repos = [
            make_repo(
                is_fork=False,
                days_since_push=10,
                is_org_repo=False,
                languages=["Python"],
            )
        ]
        result = stage1_hard_filter(repos, ["Python"], self._default_config())
        assert len(result) == 1

    # --- multiple repos mixed ---
    def test_filters_multiple_mixed(self):
        repos = [
            make_repo(name="fork-repo", is_fork=True),
            make_repo(name="old-repo", days_since_push=400),
            make_repo(name="good-repo", is_fork=False, days_since_push=30, languages=["Python"]),
        ]
        result = stage1_hard_filter(repos, ["Python"], self._default_config())
        assert len(result) == 1
        assert result[0].name == "good-repo"


# ---------------------------------------------------------------------------
# Stage2: relevance score
# ---------------------------------------------------------------------------


class TestStage2RelevanceScore:
    def test_tech_stack_match_scores(self):
        """Each matched tech adds +0.3. Isolate: no recent bonus (days>=90), no LOC bonus (loc<=500)."""
        repo = make_repo(detected_tech_stack=["FastAPI", "PostgreSQL"], days_since_push=200, total_loc=0)
        result = stage2_relevance_score([repo], ["FastAPI", "PostgreSQL"], [])
        assert len(result) == 1
        _, score = result[0]
        assert score == pytest.approx(0.6)  # 2 × 0.3

    def test_single_tech_match(self):
        """Isolate: no recent bonus (days>=90), no LOC bonus (loc<=500)."""
        repo = make_repo(detected_tech_stack=["FastAPI"], days_since_push=200, total_loc=0)
        result = stage2_relevance_score([repo], ["FastAPI"], [])
        _, score = result[0]
        assert score == pytest.approx(0.3)

    def test_no_tech_match(self):
        """Isolate: no recent bonus (days>=90), no LOC bonus (loc<=500)."""
        repo = make_repo(detected_tech_stack=["Django"], days_since_push=200, total_loc=0)
        result = stage2_relevance_score([repo], ["FastAPI"], [])
        _, score = result[0]
        assert score == pytest.approx(0.0)

    def test_recent_activity_bonus(self):
        """days_since_push < 90 adds +0.2."""
        repo = make_repo(days_since_push=30, detected_tech_stack=[], total_loc=0)
        result = stage2_relevance_score([repo], [], [])
        _, score = result[0]
        assert score == pytest.approx(0.2)

    def test_no_recent_activity_bonus_at_boundary(self):
        """days_since_push == 90 does NOT trigger bonus (strictly <90)."""
        repo = make_repo(days_since_push=90, detected_tech_stack=[], total_loc=0)
        result = stage2_relevance_score([repo], [], [])
        _, score = result[0]
        assert score == pytest.approx(0.0)

    def test_loc_bonus(self):
        """total_loc > 500 adds +0.1."""
        repo = make_repo(total_loc=501, days_since_push=200, detected_tech_stack=[])
        result = stage2_relevance_score([repo], [], [])
        _, score = result[0]
        assert score == pytest.approx(0.1)

    def test_no_loc_bonus_at_boundary(self):
        """total_loc == 500 does NOT trigger bonus (strictly >500)."""
        repo = make_repo(total_loc=500, days_since_push=200, detected_tech_stack=[])
        result = stage2_relevance_score([repo], [], [])
        _, score = result[0]
        assert score == pytest.approx(0.0)

    def test_all_bonuses_combined(self):
        """tech(0.3) + recent(0.2) + loc(0.1) = 0.6 for a single tech match."""
        repo = make_repo(
            detected_tech_stack=["FastAPI"],
            days_since_push=10,
            total_loc=1000,
        )
        result = stage2_relevance_score([repo], ["FastAPI"], [])
        _, score = result[0]
        assert score == pytest.approx(0.6)

    def test_sorted_descending(self):
        """Results are sorted by score descending."""
        low = make_repo(name="low", detected_tech_stack=[], total_loc=0, days_since_push=200)
        high = make_repo(
            name="high", detected_tech_stack=["FastAPI"], days_since_push=10, total_loc=1000
        )
        result = stage2_relevance_score([low, high], ["FastAPI"], [])
        assert result[0][0].name == "high"
        assert result[1][0].name == "low"

    def test_sorted_descending_three_items(self):
        r0 = make_repo(name="r0", detected_tech_stack=[], total_loc=0, days_since_push=200)
        r1 = make_repo(
            name="r1", detected_tech_stack=["FastAPI", "PostgreSQL"], days_since_push=10, total_loc=1000
        )
        r2 = make_repo(name="r2", detected_tech_stack=["FastAPI"], days_since_push=200, total_loc=0)
        result = stage2_relevance_score([r0, r1, r2], ["FastAPI", "PostgreSQL"], [])
        names = [r.name for r, _ in result]
        assert names[0] == "r1"   # 0.3+0.3+0.2+0.1 = 0.9
        assert names[1] == "r2"   # 0.3
        assert names[2] == "r0"   # 0.0

    def test_empty_repos(self):
        result = stage2_relevance_score([], ["FastAPI"], [])
        assert result == []


# ---------------------------------------------------------------------------
# Stage3: similarity threshold
# ---------------------------------------------------------------------------


class TestStage3ShouldInclude:
    def _cfg(self, min_sim: float = 0.60) -> FunnelConfig:
        return FunnelConfig(vector_similarity_min=min_sim)

    def test_above_threshold(self):
        assert stage3_should_include(0.75, self._cfg()) is True

    def test_below_threshold(self):
        assert stage3_should_include(0.50, self._cfg()) is False

    def test_exact_threshold(self):
        assert stage3_should_include(0.60, self._cfg()) is True

    def test_zero_similarity(self):
        assert stage3_should_include(0.0, self._cfg()) is False

    def test_perfect_similarity(self):
        assert stage3_should_include(1.0, self._cfg()) is True

    def test_custom_threshold(self):
        cfg = self._cfg(min_sim=0.80)
        assert stage3_should_include(0.79, cfg) is False
        assert stage3_should_include(0.80, cfg) is True
        assert stage3_should_include(0.81, cfg) is True
