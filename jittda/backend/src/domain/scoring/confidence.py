"""
Scoring Confidence Determiner

데이터 소스 수와 공개 레포지터리 수를 기반으로 점수 신뢰도를 결정한다.

판별 규칙:
  HIGH   : data_source_count >= 3 AND public_repo_count >= 5
  MEDIUM : data_source_count >= 2 AND public_repo_count >= 2  (HIGH 미충족 시)
  LOW    : 나머지 모든 경우

외부 의존성 없음 — 순수 도메인 로직.
"""
from domain.scoring.models import ScoreConfidence


def determine_confidence(
    data_source_count: int,
    public_repo_count: int,
) -> ScoreConfidence:
    """
    데이터 소스 수와 공개 레포 수로 점수 신뢰도를 반환한다.

    Args:
        data_source_count: 수집된 데이터 소스 수 (GitHub, LinkedIn, JD 등).
        public_repo_count: 후보자의 공개 레포지터리 수.

    Returns:
        ScoreConfidence: HIGH / MEDIUM / LOW
    """
    if data_source_count >= 3 and public_repo_count >= 5:
        return ScoreConfidence.HIGH

    if data_source_count >= 2 and public_repo_count >= 2:
        return ScoreConfidence.MEDIUM

    return ScoreConfidence.LOW
