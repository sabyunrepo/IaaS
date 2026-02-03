"""
backend/app/services/github_analyzer.py
GitHub 종합 분석 서비스 (4-Channel)

Channel A: 본인 레포 분석 (code_analyzer.py와 연동)
Channel B: 오픈소스 PR 기여 (GitHub Search API)
Channel C: 이슈 참여 (GitHub Search API)
Channel D: 코드 리뷰 활동 (GitHub Events API)
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubComprehensiveAnalyzer:
    """GitHub 종합 분석 (4-Channel)"""

    def __init__(
        self,
        username: str,
        github_token: str | None = None,
        analysis_years: int | None = None,
    ):
        self.username = username
        self.token = github_token or settings.GITHUB_TOKEN
        self.analysis_years = analysis_years or settings.GITHUB_ANALYSIS_YEARS
        self._github = None

    def _get_github(self):
        """PyGithub 인스턴스 (lazy load)"""
        if self._github is None:
            from github import Github
            self._github = Github(self.token) if self.token else Github()
        return self._github

    @property
    def since_date(self) -> datetime:
        """분석 시작 날짜"""
        return datetime.now(timezone.utc) - timedelta(days=self.analysis_years * 365)

    # ══════════════════════════════════════════════════════════════════
    # Channel B: 오픈소스 PR 기여
    # ══════════════════════════════════════════════════════════════════

    async def analyze_oss_prs(self, max_prs: int = 20) -> list[dict]:
        """
        오픈소스 PR 기여 분석

        검색 쿼리: author:{username} type:pr is:merged -user:{username}
        → 외부 레포에 머지된 PR만 검색

        Returns:
            list[OSSContribution] 형태의 dict 리스트
        """
        logger.info(f"Analyzing OSS PRs for {self.username}")

        try:
            g = self._get_github()
            query = f"author:{self.username} type:pr is:merged -user:{self.username}"

            contributions = []
            for issue in g.search_issues(query, sort="updated", order="desc"):
                if len(contributions) >= max_prs:
                    break

                # merged_at 필터 (분석 기간 내)
                pr = issue.as_pull_request()
                if pr.merged_at and pr.merged_at < self.since_date:
                    continue

                contributions.append({
                    "repo_full_name": issue.repository.full_name,
                    "pr_number": issue.number,
                    "pr_title": issue.title,
                    "pr_description": (issue.body or "")[:500],
                    "pr_url": issue.html_url,
                    "files_changed": pr.changed_files,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "review_comments_count": pr.review_comments,
                    "labels": [label.name for label in issue.labels],
                })

            logger.info(f"Found {len(contributions)} OSS PRs for {self.username}")
            return contributions

        except Exception as e:
            logger.warning(f"Failed to analyze OSS PRs for {self.username}: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════
    # Channel C: 이슈 참여
    # ══════════════════════════════════════════════════════════════════

    async def analyze_issues(self, max_issues: int = 30) -> list[dict]:
        """
        이슈 참여 분석

        검색 쿼리:
          - author:{username} type:issue (작성한 이슈)
          - commenter:{username} type:issue (코멘트한 이슈)

        Returns:
            list[IssueParticipation] 형태의 dict 리스트
        """
        logger.info(f"Analyzing issue participation for {self.username}")

        try:
            g = self._get_github()
            issues_map = {}  # issue_id -> participation

            # 작성한 이슈
            for issue in g.search_issues(
                f"author:{self.username} type:issue",
                sort="updated",
                order="desc"
            ):
                if len(issues_map) >= max_issues:
                    break
                if issue.created_at and issue.created_at < self.since_date:
                    continue

                issues_map[issue.id] = {
                    "repo_full_name": issue.repository.full_name,
                    "issue_number": issue.number,
                    "issue_title": issue.title,
                    "issue_url": issue.html_url,
                    "role": "author",
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "body_summary": (issue.body or "")[:300],
                    "comment_count": issue.comments,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                }

            # 코멘트한 이슈 (작성한 이슈와 중복 제외)
            for issue in g.search_issues(
                f"commenter:{self.username} type:issue -author:{self.username}",
                sort="updated",
                order="desc"
            ):
                if len(issues_map) >= max_issues:
                    break
                if issue.id in issues_map:
                    continue
                if issue.created_at and issue.created_at < self.since_date:
                    continue

                issues_map[issue.id] = {
                    "repo_full_name": issue.repository.full_name,
                    "issue_number": issue.number,
                    "issue_title": issue.title,
                    "issue_url": issue.html_url,
                    "role": "commenter",
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "body_summary": (issue.body or "")[:300],
                    "comment_count": issue.comments,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                }

            participations = list(issues_map.values())
            logger.info(f"Found {len(participations)} issue participations for {self.username}")
            return participations

        except Exception as e:
            logger.warning(f"Failed to analyze issues for {self.username}: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════
    # Channel D: 코드 리뷰 활동
    # ══════════════════════════════════════════════════════════════════

    async def analyze_code_reviews(self, max_reviews: int = 30) -> list[dict]:
        """
        코드 리뷰 활동 분석

        GitHub Events API에서 PullRequestReviewEvent 필터링

        Returns:
            list[CodeReviewActivity] 형태의 dict 리스트
        """
        logger.info(f"Analyzing code reviews for {self.username}")

        try:
            g = self._get_github()
            user = g.get_user(self.username)
            reviews = []

            for event in user.get_events():
                if len(reviews) >= max_reviews:
                    break

                if event.type != "PullRequestReviewEvent":
                    continue

                # 분석 기간 필터
                if event.created_at and event.created_at < self.since_date:
                    continue

                payload = event.payload
                pr = payload.get("pull_request", {})
                review = payload.get("review", {})

                # 본인 PR에 대한 리뷰는 제외 (자기 리뷰)
                if pr.get("user", {}).get("login") == self.username:
                    continue

                reviews.append({
                    "repo_full_name": event.repo.name,
                    "pr_number": pr.get("number"),
                    "pr_title": pr.get("title", ""),
                    "pr_url": pr.get("html_url", ""),
                    "review_state": review.get("state", "COMMENTED"),
                    "review_body": (review.get("body") or "")[:500],
                    "submitted_at": review.get("submitted_at"),
                    "comments_count": 0,  # Events API에서는 인라인 코멘트 수 미제공
                })

            logger.info(f"Found {len(reviews)} code reviews for {self.username}")
            return reviews

        except Exception as e:
            logger.warning(f"Failed to analyze code reviews for {self.username}: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════
    # 통합 분석
    # ══════════════════════════════════════════════════════════════════

    async def analyze_all(self) -> dict:
        """
        4개 채널 전체 분석 (병렬 실행 권장)

        Channel A는 별도로 code_analyzer.py에서 처리

        Returns:
            ComprehensiveGitHubProfile 형태의 dict
        """
        import asyncio

        oss_prs, issues, reviews = await asyncio.gather(
            self.analyze_oss_prs(),
            self.analyze_issues(),
            self.analyze_code_reviews(),
        )

        # 통계 계산
        stats = {
            # Channel B
            "oss_prs_merged": len(oss_prs),
            "oss_repos_contributed": len(set(pr["repo_full_name"] for pr in oss_prs)),

            # Channel C
            "issues_authored": len([i for i in issues if i["role"] == "author"]),
            "issues_commented": len([i for i in issues if i["role"] == "commenter"]),

            # Channel D
            "reviews_given": len(reviews),
            "reviews_approved": len([r for r in reviews if r["review_state"] == "APPROVED"]),
            "reviews_changes_requested": len([r for r in reviews if r["review_state"] == "CHANGES_REQUESTED"]),

            # 토큰 추정
            "estimated_tokens": self._estimate_tokens(oss_prs, issues, reviews),
        }

        return {
            "username": self.username,
            "analysis_period_years": self.analysis_years,
            "oss_contributions": oss_prs,
            "issue_participations": issues,
            "code_reviews": reviews,
            "stats": stats,
        }

    def _estimate_tokens(
        self,
        oss_prs: list[dict],
        issues: list[dict],
        reviews: list[dict],
    ) -> int:
        """토큰 사용량 추정"""
        # 대략적인 추정: PR ~800, Issue ~350, Review ~400 tokens
        return len(oss_prs) * 800 + len(issues) * 350 + len(reviews) * 400


def aggregate_comprehensive_analysis(
    own_repos: list[dict],
    oss_contributions: list[dict],
    issue_participations: list[dict],
    code_reviews: list[dict],
    analysis_years: int,
    candidate_username: str,
) -> dict:
    """
    4-Channel 분석 결과 통합

    기존 CodeAnalysis 형태를 확장하여 ComprehensiveGitHubProfile 반환
    """
    # Channel A 통계
    own_commits = sum(r.get("candidate_commits", 0) for r in own_repos)
    own_additions = sum(r.get("candidate_additions", 0) for r in own_repos)
    own_deletions = sum(
        r.get("analysis", {}).get("stats", {}).get("total_deletions", 0)
        for r in own_repos
    )

    # 전체 통계
    stats = {
        # Channel A
        "own_repos_count": len(own_repos),
        "own_commits_count": own_commits,
        "own_additions": own_additions,
        "own_deletions": own_deletions,

        # Channel B
        "oss_prs_merged": len(oss_contributions),
        "oss_repos_contributed": len(set(pr["repo_full_name"] for pr in oss_contributions)),

        # Channel C
        "issues_authored": len([i for i in issue_participations if i.get("role") == "author"]),
        "issues_commented": len([i for i in issue_participations if i.get("role") == "commenter"]),

        # Channel D
        "reviews_given": len(code_reviews),
        "reviews_approved": len([r for r in code_reviews if r.get("review_state") == "APPROVED"]),
        "reviews_changes_requested": len([r for r in code_reviews if r.get("review_state") == "CHANGES_REQUESTED"]),
    }

    # 토큰 추정
    own_tokens = sum(
        len(r.get("analysis", {}).get("notable_implementations", [])) * 500
        for r in own_repos
    ) + len(own_repos) * 3000
    oss_tokens = len(oss_contributions) * 800
    issue_tokens = len(issue_participations) * 350
    review_tokens = len(code_reviews) * 400
    stats["estimated_tokens"] = own_tokens + oss_tokens + issue_tokens + review_tokens

    # 기존 CodeAnalysis 형태 + 확장
    combined_tech_stack = []
    for r in own_repos:
        if isinstance(r.get("analysis"), dict):
            combined_tech_stack.extend(r["analysis"].get("tech_stack", []))
    combined_tech_stack = list(set(combined_tech_stack))

    top_question_candidates = []
    for r in own_repos:
        if isinstance(r.get("analysis"), dict):
            top_question_candidates.extend(
                r["analysis"].get("notable_implementations", [])[:3]
            )

    return {
        # 기존 CodeAnalysis 호환 필드
        "repositories": own_repos,
        "combined_tech_stack": combined_tech_stack,
        "total_patterns": sum(
            len(r.get("analysis", {}).get("patterns", []))
            for r in own_repos
        ),
        "total_notable_implementations": sum(
            len(r.get("analysis", {}).get("notable_implementations", []))
            for r in own_repos
        ),
        "top_question_candidates": top_question_candidates[:10],

        # 확장 필드 (4-Channel)
        "comprehensive_profile": {
            "username": candidate_username,
            "analysis_period_years": analysis_years,
            "oss_contributions": oss_contributions,
            "issue_participations": issue_participations,
            "code_reviews": code_reviews,
            "stats": stats,
        },
    }
