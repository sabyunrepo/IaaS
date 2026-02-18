---
title: "신뢰도 체계 (Confidence Levels)"
type: component
layer: domain
parent: "[[domain/scoring-system/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# 신뢰도 체계 (Confidence Levels)

> 모든 점수 산출 결과에는 신뢰도 플래그가 함께 반환된다.
> 신뢰도는 데이터 소스 수(횡)와 공개 레포 수(종)로 결정되는 2차원 매트릭스다.
> 비개발자 HR 담당자가 점수의 신뢰성을 직관적으로 파악할 수 있도록 설계되었다.

## 3단계 신뢰도 기준

| 신뢰도 | 표시 | 조건 | 해석 |
|--------|------|------|------|
| 높음 | 🟢 | 데이터 소스 3개 이상 **AND** 공개 레포 5개 이상 | 충분한 근거로 산출된 점수. 면접에 그대로 활용 가능 |
| 중간 | 🟡 | 데이터 소스 2개 **AND** 공개 레포 2-4개 | 참고 자료로 활용. 면접에서 보완 질문 권장 |
| 낮음 | 🔴 | 데이터 소스 1개 이하 **OR** 공개 레포 1개 이하 | 데이터 부족. 점수 신뢰성 낮음. 직접 확인 필수 |

## 데이터 소스 × 공개 레포 매트릭스

```
                    공개 레포 수
                    0-1개    2-4개    5개 이상
                  ┌────────┬────────┬─────────┐
데이터   1개 이하  │  🔴낮음 │  🔴낮음 │  🔴낮음  │
소스     2개       │  🔴낮음 │  🟡중간 │  🟡중간  │
수       3개 이상  │  🔴낮음 │  🟡중간 │  🟢높음  │
                  └────────┴────────┴─────────┘
```

## 데이터 소스 정의

신뢰도 산정에 사용되는 데이터 소스 종류:

| 소스 ID | 소스명 | 제공 정보 |
|---------|--------|---------|
| `github` | GitHub 레포지토리 | 코드, 커밋 히스토리, blame |
| `linkedin` | LinkedIn 프로필 | 경력, 스킬, 학력 |
| `resume` | 이력서/포트폴리오 | 자기 기술 경력 및 프로젝트 |

3개 소스 모두 연결 시 🟢, 2개는 🟡, 1개 이하는 무조건 🔴.

## 산출 코드

```python
# domain/scoring/confidence.py

from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"    # 🟢
    MEDIUM = "medium"  # 🟡
    LOW = "low"      # 🔴

    @property
    def emoji(self) -> str:
        return {"high": "🟢", "medium": "🟡", "low": "🔴"}[self.value]

    @property
    def label_ko(self) -> str:
        return {"high": "높음", "medium": "중간", "low": "낮음"}[self.value]


def determine_confidence(
    data_source_count: int,
    public_repo_count: int,
) -> ConfidenceLevel:
    """
    데이터 소스 수와 공개 레포 수로 신뢰도를 판정한다.

    높음(🟢): 소스 3개 이상 AND 공개 레포 5개 이상
    중간(🟡): 소스 2개 AND 공개 레포 2-4개
    낮음(🔴): 소스 1개 이하 OR 공개 레포 1개 이하
    """
    if data_source_count <= 1 or public_repo_count <= 1:
        return ConfidenceLevel.LOW

    if data_source_count >= 3 and public_repo_count >= 5:
        return ConfidenceLevel.HIGH

    if data_source_count >= 2 and 2 <= public_repo_count <= 4:
        return ConfidenceLevel.MEDIUM

    # 소스 3개 이상이지만 레포 2-4개인 경우 → 중간
    if data_source_count >= 3 and 2 <= public_repo_count <= 4:
        return ConfidenceLevel.MEDIUM

    return ConfidenceLevel.LOW
```

## 점수 출력 연동

```python
# domain/scoring/calculator.py (발췌)
from domain.scoring.confidence import ConfidenceLevel, determine_confidence

@dataclass
class ScoringResult:
    final_score: float
    logic_score: float
    mastery_score: float
    stability_score: float
    authenticity_score: float
    confidence: ConfidenceLevel      # 🟢🟡🔴
    data_source_count: int
    public_repo_count: int

    @property
    def confidence_display(self) -> str:
        """비개발자용 신뢰도 표시 문자열."""
        return f"{self.confidence.emoji} {self.confidence.label_ko}"
```

## 비개발자 UX 적용

신뢰도는 ResultPage의 모든 지표 카드 우상단에 배지로 표시된다:

```
┌─────────────────────────────┐
│ 논리력 점수         🟢 높음  │
│ ████████████░░░░ 78점        │
│ 근거: cc_avg=4.2, 12개 파일  │
└─────────────────────────────┘
```

- 🟢 높음: 초록 배지, "신뢰할 수 있는 분석" 툴팁
- 🟡 중간: 노란 배지, "추가 확인 권장" 툴팁
- 🔴 낮음: 빨간 배지, "데이터 부족 — 참고용으로만 활용" 툴팁
