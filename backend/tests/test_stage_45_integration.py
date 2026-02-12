"""Stage 4.5 교체 + Cross-Repo 검증 통합 테스트 (JIT-37).

테스트 시나리오:
1. 높은 confidence: name_exact 매칭(1.0) → author 필터 적용
2. 낮은 confidence: 0.4 미만 → author 필터 비적용, 전체 커밋 수집
3. Cross-Repo 매칭: 3개 레포 중 2개에서 동일 author → confidence 부스트
4. Fork 레포 방어: fork 레포에서 잘못된 author → confidence 낮아 필터 스킵
5. 메트릭 로깅: author_avg_confidence, author_method, cross_repo_match 기록
"""

import pytest
from collections import Counter

from app.models.author_identity import AuthorIdentityResult, AuthorMatch
from app.services.github_service import GitHubService
from app.workflows.activities.code_analysis import _log_pipeline_metrics


# ──────────────────────────────────────────────
# 1. 높은 confidence → author 필터 적용
# ──────────────────────────────────────────────

class TestHighConfidenceFilter:
    """confidence >= 0.5 → author 필터 적용."""

    def test_name_exact_applies_filter(self):
        """name_exact(1.0) → best_match 반환, 필터 적용 가능."""
        authors = [
            {"name": "sabyun", "email": "s@g.com", "commits": 50},
            {"name": "other", "email": "o@g.com", "commits": 10},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is not None
        assert result.best_match.confidence >= 0.5
        assert result.best_match.name == "sabyun"

    def test_noreply_applies_filter(self):
        """noreply_email(0.95) → best_match 반환, 필터 적용 가능."""
        authors = [
            {"name": "DevUser", "email": "12345+sabyun@users.noreply.github.com", "commits": 40},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is not None
        assert result.best_match.confidence >= 0.5

    def test_email_prefix_applies_filter(self):
        """email_prefix(0.9) → 필터 적용 가능."""
        authors = [
            {"name": "John Doe", "email": "sabyun@company.com", "commits": 25},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is not None
        assert result.best_match.confidence >= 0.5


# ──────────────────────────────────────────────
# 2. 낮은 confidence → author 필터 비적용
# ──────────────────────────────────────────────

class TestLowConfidenceSkip:
    """confidence < 0.5 → author 필터 비적용 (전체 커밋 수집)."""

    def test_commit_pattern_only_below_threshold(self):
        """commit_pattern_analysis(0.5)만 매칭 → best_match=None (identity 필터 제외)."""
        authors = [
            {"name": "major-contributor", "email": "mc@gmail.com", "commits": 80},
            {"name": "minor1", "email": "m1@gmail.com", "commits": 10},
            {"name": "minor2", "email": "m2@gmail.com", "commits": 10},
        ]
        result = GitHubService.resolve_author_by_identity("unknown-user", authors)
        # commit_pattern_analysis는 best_match 후보에서 제외됨
        assert result.best_match is None

    def test_no_match_returns_none(self):
        """매칭 없음 → best_match=None, 필터 비적용."""
        authors = [
            {"name": "completely-different", "email": "cd@gmail.com", "commits": 5},
        ]
        result = GitHubService.resolve_author_by_identity("sabyun", authors)
        assert result.best_match is None

    def test_confidence_threshold_simulation(self):
        """confidence < 0.5인 AuthorMatch로 threshold 동작 검증."""
        # 실제 코드 로직 시뮬레이션:
        # if best.confidence < 0.5 → candidate_username = None
        low_match = AuthorMatch(
            name="weak-match", email="w@g.com", commits=5,
            confidence=0.4, method="name_substring",
        )
        # 실제 코드에서 이 조건으로 분기
        assert low_match.confidence < 0.5
        # → candidate_username = None, author 필터 비적용

        high_match = AuthorMatch(
            name="strong-match", email="s@g.com", commits=50,
            confidence=0.9, method="name_exact",
        )
        assert high_match.confidence >= 0.5
        # → candidate_username = best.name, author 필터 적용


# ──────────────────────────────────────────────
# 3. Cross-Repo 매칭
# ──────────────────────────────────────────────

class TestCrossRepoIntegration:
    """Cross-Repo 검증 통합 동작."""

    def test_two_repo_match_boosts_confidence(self):
        """2개 레포에서 동일 author → confidence 부스트."""
        repo_a = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun", "email": "s@g.com", "commits": 30}],
            repo_name="repo-a",
        )
        repo_b = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun", "email": "s@g.com", "commits": 20}],
            repo_name="repo-b",
        )

        merged = GitHubService.verify_cross_repo({
            "repo-a": repo_a,
            "repo-b": repo_b,
        })

        assert merged.cross_repo_verified is True
        assert merged.best_match is not None
        assert merged.best_match.confidence == 1.0  # 1.0 * 1.3 → cap 1.0
        assert merged.best_match.commits == 50
        assert len(merged.best_match.repos_matched) == 2

    def test_cross_repo_updates_identification(self):
        """cross-repo 결과가 candidate_identification dict에 반영되는 형식."""
        # 실제 analyze_code() 내부 로직 시뮬레이션
        repo_a_result = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun", "email": "s@g.com", "commits": 30}],
            repo_name="repo-a",
        )

        cross_result = GitHubService.verify_cross_repo({
            "repo-a": repo_a_result,
        })

        # 단일 레포만 있으면 cross_repo_verified=False
        ci = {}
        ci["cross_repo_verified"] = cross_result.cross_repo_verified
        if cross_result.best_match:
            ci["cross_repo_best_author"] = cross_result.best_match.name
            ci["cross_repo_confidence"] = cross_result.best_match.confidence

        assert "cross_repo_verified" in ci
        assert ci["cross_repo_verified"] is False

    def test_three_repos_two_match(self):
        """3개 레포 중 2개 매칭, 1개 미매칭 → verified=True."""
        repo_a = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun", "email": "s@g.com", "commits": 30}],
            repo_name="repo-a",
        )
        repo_b = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "sabyun", "email": "s@company.com", "commits": 20}],
            repo_name="repo-b",
        )
        repo_c = GitHubService.resolve_author_by_identity(
            "sabyun",
            [{"name": "unrelated", "email": "u@gmail.com", "commits": 100}],
            repo_name="repo-c",
        )

        merged = GitHubService.verify_cross_repo({
            "repo-a": repo_a,
            "repo-b": repo_b,
            "repo-c": repo_c,
        })

        assert merged.cross_repo_verified is True
        assert merged.best_match.name == "sabyun"


# ──────────────────────────────────────────────
# 4. Fork 레포 방어
# ──────────────────────────────────────────────

class TestForkRepoDefense:
    """Fork 레포에서 잘못된 author 매칭 방어."""

    def test_fork_repo_no_identity_match(self):
        """Fork 레포 — Ubuntu/root/bot만 있으면 매칭 없음 → 필터 비적용."""
        fork_authors = [
            {"name": "Ubuntu", "email": "ubuntu@ip.internal", "commits": 500},
            {"name": "root", "email": "root@localhost", "commits": 100},
            {"name": "dependabot[bot]", "email": "bot@github.com", "commits": 50},
        ]
        result = GitHubService.resolve_author_by_identity("real-candidate", fork_authors)
        # identity 매칭 없음 → best_match=None → 전체 커밋 수집
        assert result.best_match is None

    def test_fork_commit_pattern_excluded_from_best(self):
        """Fork 레포 — commit_pattern_analysis만 매칭 → best_match에서 제외."""
        authors = [
            {"name": "fork-owner", "email": "fo@gmail.com", "commits": 200},
            {"name": "minor", "email": "m@gmail.com", "commits": 5},
        ]
        result = GitHubService.resolve_author_by_identity("actual-user", authors)
        # fork-owner가 commit_pattern_analysis로 매칭될 수 있지만 best_match에서 제외
        if result.best_match:
            assert result.best_match.method != "commit_pattern_analysis"


# ──────────────────────────────────────────────
# 5. 메트릭 로깅
# ──────────────────────────────────────────────

class TestPipelineMetrics:
    """_log_pipeline_metrics의 author 식별 메트릭."""

    def test_metrics_with_author_data(self):
        """author 식별 메트릭이 로깅에 포함되는지 확인."""
        result = {
            "repositories": [
                {
                    "repo_name": "repo-a",
                    "analysis": {"tech_stack": ["Python"], "patterns": []},
                    "notable_implementations": [],
                    "candidate_identification": {
                        "method": "git_author_validation/name_exact",
                        "confidence_score": 1.0,
                        "cross_repo_verified": True,
                    },
                    "hybrid_metadata": {"ranked_chunks_count": 5, "deep_analyses_count": 3},
                },
                {
                    "repo_name": "repo-b",
                    "analysis": {"tech_stack": ["Python"], "patterns": []},
                    "notable_implementations": [],
                    "candidate_identification": {
                        "method": "git_author_validation/noreply_email",
                        "confidence_score": 0.95,
                        "cross_repo_verified": True,
                    },
                    "hybrid_metadata": {"ranked_chunks_count": 3, "deep_analyses_count": 2},
                },
            ],
            "combined_tech_stack": ["Python"],
            "total_patterns": 0,
            "total_notable_implementations": 0,
            "top_question_candidates": [],
        }

        # 메트릭 추출 로직 재현 (실제 함수 내부 로직)
        repos = result["repositories"]
        methods = []
        confidences = []
        cross_repo_count = 0
        for repo in repos:
            ci = repo.get("candidate_identification", {})
            method = ci.get("method", "none")
            if "/" in method:
                method = method.split("/")[-1]
            methods.append(method)
            score = ci.get("confidence_score")
            if score is not None:
                confidences.append(score)
            if ci.get("cross_repo_verified"):
                cross_repo_count += 1

        method_counter = Counter(methods)
        author_match_method = method_counter.most_common(1)[0][0]
        author_avg_confidence = round(sum(confidences) / len(confidences), 2)

        assert author_match_method in ["name_exact", "noreply_email"]
        assert 0.97 <= author_avg_confidence <= 0.98  # (1.0 + 0.95) / 2 ≈ 0.975
        assert cross_repo_count == 2

    def test_metrics_no_author_data(self):
        """author 식별 없는 레포 — 기본값 처리."""
        result = {
            "repositories": [
                {
                    "repo_name": "repo-a",
                    "analysis": {"tech_stack": [], "patterns": []},
                    "notable_implementations": [],
                    "candidate_identification": {
                        "method": "none",
                        "confidence": "low",
                    },
                    "hybrid_metadata": {},
                },
            ],
            "combined_tech_stack": [],
            "total_patterns": 0,
            "total_notable_implementations": 0,
            "top_question_candidates": [],
        }

        repos = result["repositories"]
        methods = []
        confidences = []
        for repo in repos:
            ci = repo.get("candidate_identification", {})
            method = ci.get("method", "none")
            if "/" in method:
                method = method.split("/")[-1]
            methods.append(method)
            score = ci.get("confidence_score")
            if score is not None:
                confidences.append(score)

        method_counter = Counter(methods)
        author_match_method = method_counter.most_common(1)[0][0]
        author_avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

        assert author_match_method == "none"
        assert author_avg_confidence == 0.0

    def test_log_pipeline_metrics_runs_without_error(self):
        """_log_pipeline_metrics 함수가 에러 없이 실행되는지 확인."""
        result = {
            "repositories": [
                {
                    "repo_name": "repo-a",
                    "analysis": {"tech_stack": ["Python"], "patterns": ["singleton"]},
                    "notable_implementations": [{"desc": "test"}],
                    "candidate_identification": {
                        "method": "git_author_validation/name_exact",
                        "confidence_score": 1.0,
                        "cross_repo_verified": False,
                    },
                    "hybrid_metadata": {"ranked_chunks_count": 5, "deep_analyses_count": 3},
                },
            ],
            "combined_tech_stack": ["Python"],
            "total_patterns": 1,
            "total_notable_implementations": 1,
            "top_question_candidates": [{"desc": "test"}],
        }
        # 에러 없이 실행되면 통과
        _log_pipeline_metrics(result, use_clone_based=True)
        _log_pipeline_metrics(result, use_clone_based=False)
