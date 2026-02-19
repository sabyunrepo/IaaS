"""
Funnel Selection 도메인 규칙

3단계 퍼널로 JD에 적합한 리포지토리를 선별한다.

Stage 1 — Hard Filter  : 포크/오래된 레포/조직 기여 부족/언어 불일치 제거
Stage 2 — Relevance Score: 기술 스택 매칭·최근 활동·코드 규모 점수화 후 내림차순 정렬
Stage 3 — Similarity Gate: 벡터 유사도 임계치 통과 여부 판별
"""
from domain.matching.models import FunnelConfig, RepoMetadata

# ---------------------------------------------------------------------------
# Stage 1: Hard Filter
# ---------------------------------------------------------------------------

_TECH_MATCH_SCORE = 0.3
_RECENT_ACTIVITY_SCORE = 0.2
_LOC_SCORE = 0.1
_RECENT_DAYS_THRESHOLD = 90
_LOC_THRESHOLD = 500


def stage1_hard_filter(
    repos: list[RepoMetadata],
    jd_languages: list[str],
    config: FunnelConfig,
) -> list[RepoMetadata]:
    """
    하드 필터 — 다음 조건 중 하나라도 해당하면 제거.

    1. 포크(is_fork=True)
    2. 오래된 레포(days_since_push > config.min_push_days)
    3. 조직 레포이면서 기여 비율이 임계치 미만(is_org_repo=True and ratio < threshold)
    4. JD 언어 목록과 언어 불일치 (jd_languages 비어 있으면 검사 생략)
    """
    result: list[RepoMetadata] = []
    jd_lang_set = {lang.lower() for lang in jd_languages}

    for repo in repos:
        # Rule 1: 포크 제거
        if repo.is_fork:
            continue

        # Rule 2: 오래된 레포 제거 (strictly greater than)
        if repo.days_since_push > config.min_push_days:
            continue

        # Rule 3: 조직 레포의 낮은 기여 비율 제거 (strictly less than)
        if repo.is_org_repo and repo.user_contribution_ratio < config.org_contribution_threshold:
            continue

        # Rule 4: 언어 불일치 제거 (jd_languages 비어 있으면 생략)
        if jd_lang_set:
            repo_lang_set = {lang.lower() for lang in repo.languages}
            if not jd_lang_set.intersection(repo_lang_set):
                continue

        result.append(repo)

    return result


# ---------------------------------------------------------------------------
# Stage 2: Relevance Score
# ---------------------------------------------------------------------------


def stage2_relevance_score(
    repos: list[RepoMetadata],
    jd_requirements: list[str],
    jd_tech_stack: list[str],
) -> list[tuple[RepoMetadata, float]]:
    """
    관련도 점수화 — 점수 내림차순으로 정렬해 반환.

    점수 계산:
    - 기술 스택 매칭: +0.3 per matched tech (repo.detected_tech_stack ∩ jd_requirements)
    - 최근 활동: +0.2 if days_since_push < 90
    - 코드 규모: +0.1 if total_loc > 500

    jd_requirements: JD에서 요구하는 기술 목록 (기술 스택 매칭에 사용)
    jd_tech_stack: 추가 컨텍스트 (현재 점수 계산에 미사용, 확장용)
    """
    jd_req_set = {req.lower() for req in jd_requirements}
    scored: list[tuple[RepoMetadata, float]] = []

    for repo in repos:
        score = 0.0

        # +0.3 per matched tech
        repo_tech_set = {tech.lower() for tech in repo.detected_tech_stack}
        matched_count = len(jd_req_set.intersection(repo_tech_set))
        score += matched_count * _TECH_MATCH_SCORE

        # +0.2 if recent activity (strictly less than 90 days)
        if repo.days_since_push < _RECENT_DAYS_THRESHOLD:
            score += _RECENT_ACTIVITY_SCORE

        # +0.1 if LOC > 500 (strictly greater than)
        if repo.total_loc > _LOC_THRESHOLD:
            score += _LOC_SCORE

        scored.append((repo, score))

    # Sort descending by score
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Stage 3: Similarity Gate
# ---------------------------------------------------------------------------


def stage3_should_include(similarity: float, config: FunnelConfig) -> bool:
    """
    벡터 유사도 임계치 통과 여부.

    similarity >= config.vector_similarity_min 이면 True.
    """
    return similarity >= config.vector_similarity_min
