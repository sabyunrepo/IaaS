---
title: "Relevance Scoring"
type: component
layer: domain
parent: "[[domain/funnel-selection/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-90"]
---

# Relevance Scoring (Stage 2)

## 목적

Hard Filter를 통과한 레포지토리에 **JD 기반 적합성 점수를 산출**하여 순위를 매긴다. JD의 `tech_stack`과 `requirements`를 기준으로 레포가 해당 직무와 얼마나 관련 있는지를 수치화한다.

## 점수 산출 로직

점수는 0.0 ~ 1.0 범위의 float이며, 세 가지 신호를 합산한다.

| 신호 | 가중치 | 조건 |
|------|--------|------|
| 기술스택 매칭 | `matched_techs * 0.3` | JD tech_stack과 레포 detected_tech_stack의 교집합 개수 |
| 최근 활동 가산 | +0.2 | `days_since_push < 90` (3개월 내 활동) |
| 코드 규모 가산 | +0.1 | `total_loc > 500` (너무 작은 토이 프로젝트 감점) |

## 구현

```python
# domain/matching/funnel_rules.py

def stage2_relevance_score(
    repos: list[RepoMetadata],
    jd_requirements: list[str],
    jd_tech_stack: list[str],
) -> list[tuple[RepoMetadata, float]]:
    """Stage 2: JD 기반 적합성 스코어링

    Returns:
        적합성 점수 내림차순으로 정렬된 (레포, 점수) 튜플 목록
    """
    scored = []
    for repo in repos:
        score = 0.0
        # tech_stack 매칭 (AST/LLM 분석 결과 활용)
        matched_techs = set(repo.detected_tech_stack).intersection(set(jd_tech_stack))
        score += len(matched_techs) * 0.3
        # 최근 활동 가산
        if repo.days_since_push < 90:
            score += 0.2
        # 코드 규모 가산 (너무 작은 레포 감점)
        if repo.total_loc > 500:
            score += 0.1
        scored.append((repo, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)
```

## 기술스택 매칭 원리

`repo.detected_tech_stack`은 레포의 언어, 패키지 파일(`requirements.txt`, `package.json` 등), README 분석으로 감지된 기술 목록이다. JD에서 추출한 `jd_tech_stack`(예: `["Python", "FastAPI", "PostgreSQL"]`)과 교집합을 구하여 스코어에 반영한다.

예시:
```
JD tech_stack:   ["Python", "FastAPI", "PostgreSQL", "Docker"]
repo tech_stack: ["Python", "FastAPI", "Redis"]
교집합:          ["Python", "FastAPI"]  → score += 2 * 0.3 = 0.6
```

## 입력 / 출력

| | 타입 | 설명 |
|--|------|------|
| 입력 | `list[RepoMetadata]` | Stage 1 통과 레포 목록 |
| 입력 | `list[str]` | JD 요구사항 텍스트 목록 |
| 입력 | `list[str]` | JD 기술스택 목록 |
| 출력 | `list[tuple[RepoMetadata, float]]` | (레포, 점수) 튜플, 점수 내림차순 정렬 |

## 다음 단계

Relevance Scoring 상위 레포는 [[domain/funnel-selection/vector-similarity]] (Stage 3)로 전달되어 최종 임계값 판정을 받는다.
