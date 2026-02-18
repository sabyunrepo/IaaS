---
title: "Hard Filter"
type: component
layer: domain
parent: "[[domain/funnel-selection/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-90"]
---

# Hard Filter (Stage 1)

## 목적

전체 레포지토리 목록에서 **분석 가치가 없는 레포를 메타데이터만으로 빠르게 제거**한다. LLM 호출 없이 순수 규칙 기반으로 동작하므로 비용이 0에 가깝다.

## 필터링 규칙

| 규칙 | 조건 | 이유 |
|------|------|------|
| Fork 제거 | `repo.is_fork == True` | 타인 코드이므로 기여 분석 불가 |
| 오래된 레포 | `days_since_push > min_push_days (365)` | 현재 역량과 무관한 과거 코드 |
| Org 기여도 미달 | `is_org_repo and user_contribution_ratio < 0.10` | 팀 레포에서 기여분이 10% 미만이면 실질 기여 없음 |
| 언어 불일치 | JD 요구 언어와 교집합 없음 | JD 직무와 무관한 프로젝트 |

## 구현

```python
# domain/matching/funnel_rules.py

class FunnelConfig(BaseModel):
    min_push_days: int = 365
    min_stars: int = 0
    max_repos: int = 20
    top_k: int = 5
    org_contribution_threshold: float = 0.10
    vector_similarity_min: float = 0.60


def stage1_hard_filter(
    repos: list[RepoMetadata],
    jd_languages: list[str],
    config: FunnelConfig,
) -> list[RepoMetadata]:
    """Stage 1: 메타데이터 기반 하드 필터 (LLM 호출 없음)"""
    filtered = []
    for repo in repos:
        # Fork 제외
        if repo.is_fork:
            continue
        # 최근 push 날짜 확인
        if repo.days_since_push > config.min_push_days:
            continue
        # Org 레포: 기여도 임계치 확인
        if repo.is_org_repo and repo.user_contribution_ratio < config.org_contribution_threshold:
            continue
        # 언어 교집합 확인 (JD에서 요구하는 언어가 레포에 있는지)
        if jd_languages and not set(repo.languages).intersection(set(jd_languages)):
            continue
        filtered.append(repo)
    return filtered
```

## 입력 / 출력

| | 타입 | 설명 |
|--|------|------|
| 입력 | `list[RepoMetadata]` | GraphQL로 수집한 전체 레포 목록 (최대 20개) |
| 입력 | `list[str]` | JD에서 추출한 요구 언어 목록 |
| 입력 | `FunnelConfig` | 필터 임계값 설정 |
| 출력 | `list[RepoMetadata]` | 필터 통과한 레포 목록 |

## 다음 단계

Hard Filter를 통과한 레포는 [[domain/funnel-selection/relevance-scoring]] (Stage 2)로 전달된다.
