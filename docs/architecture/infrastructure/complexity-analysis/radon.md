---
title: "Radon — CC/Halstead 메트릭"
type: component
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [radon, complexity, cyclomatic, halstead, python, infrastructure]
parent: "[[complexity-analysis/MOC]]"
children: []
depends-on: []
affects:
  - "[[application/nodes/complexity-meter-worker]]"
linear: [JIT-95]
phase: 2
---

# Radon — CC/Halstead 메트릭

## 개요

Radon은 **Python 전용** 코드 복잡도 분석 라이브러리로,
CC(Cyclomatic Complexity, 순환복잡도)와 Halstead 메트릭을 산출한다.
ComplexityMeterWorker(W7)가 `complexity_metrics` 생성 시 Python 파일에 적용한다.

## 상세 설계

### 핵심 메트릭

#### CC (Cyclomatic Complexity, 순환복잡도)

| 등급 | CC 범위 | 해석 |
|------|---------|------|
| A | 1–5 | 단순, 낮은 위험 |
| B | 6–10 | 보통 |
| C | 11–15 | 복잡 |
| D | 16–20 | 매우 복잡 |
| E | 21–25 | 불안정 |
| F | 26+ | 테스트 불가 수준 |

#### Halstead 메트릭

| 메트릭 | 심볼 | 설명 |
|--------|------|------|
| 어휘 수(Vocabulary) | h | 고유 연산자 + 고유 피연산자 수 |
| 길이(Length) | N | 전체 연산자 + 피연산자 수 |
| 볼륨(Volume) | V | `N × log2(h)` — 정보량 |
| 난이도(Difficulty) | D | 코드 이해의 어려움 |
| 노력(Effort) | E | `D × V` — 작성/이해에 필요한 정신적 노력 |
| 시간(Time) | T | `E / 18` (초) — 구현에 걸린 시간 추정 |
| 버그 수(Bugs) | B | `V / 3000` — 예상 버그 수 |

### 코드 예시

#### CC 분석

```python
# infrastructure/analysis/complexity_adapter.py
import radon.complexity as radon_cc
from radon.complexity import cc_rank, cc_visit
from radon.metrics import h_visit, mi_visit


def analyze_cyclomatic_complexity(source_code: str) -> list[dict]:
    """Python 파일의 CC(순환복잡도)를 함수/메서드 단위로 분석.

    Args:
        source_code: Python 소스코드 문자열

    Returns:
        [
            {
                "name": "function_name",
                "complexity": 5,
                "rank": "A",
                "start_line": 10,
                "end_line": 20,
                "type": "F"  # F=함수, M=메서드, C=클래스
            },
            ...
        ]
    """
    blocks = cc_visit(source_code)
    return [
        {
            "name": block.name,
            "complexity": block.complexity,
            "rank": cc_rank(block.complexity),
            "start_line": block.lineno,
            "end_line": block.endline,
            "type": block.__class__.__name__[0],  # Function, Method, Class
        }
        for block in blocks
    ]


def get_max_complexity(source_code: str) -> int:
    """파일 내 최대 CC 값 반환. 파싱 실패 시 0."""
    try:
        blocks = cc_visit(source_code)
        if not blocks:
            return 0
        return max(block.complexity for block in blocks)
    except SyntaxError:
        return 0
```

#### Halstead 분석

```python
def analyze_halstead(source_code: str) -> dict:
    """Python 파일의 Halstead 메트릭 산출.

    Returns:
        {
            "h1": 고유 연산자 수,
            "h2": 고유 피연산자 수,
            "N1": 전체 연산자 수,
            "N2": 전체 피연산자 수,
            "vocabulary": h1 + h2,
            "length": N1 + N2,
            "volume": float,
            "difficulty": float,
            "effort": float,
            "time": float,
            "bugs": float,
        }
    """
    try:
        report = h_visit(source_code)
        if not report:
            return {}
        # h_visit은 모듈 단위 집계를 반환
        total = report.total
        return {
            "h1": total.h1,
            "h2": total.h2,
            "N1": total.N1,
            "N2": total.N2,
            "vocabulary": total.vocabulary,
            "length": total.length,
            "volume": total.volume,
            "difficulty": total.difficulty,
            "effort": total.effort,
            "time": total.time,
            "bugs": total.bugs,
        }
    except Exception:
        return {}
```

#### ComplexityMeterWorker(W7) 통합

```python
# application/nodes/complexity_meter_worker.py (발췌)
from infrastructure.analysis.complexity_adapter import (
    analyze_cyclomatic_complexity,
    analyze_halstead,
)
from infrastructure.analysis.language_detector import detect_language


async def complexity_meter_worker(state: dict) -> dict:
    """W7: 레포 파일별 CC + Halstead + MI 분석."""
    repo_files: list[dict] = state["repo_files"]

    complexity_metrics = {
        "per_file": {},
        "summary": {
            "avg_cc": 0.0,
            "max_cc": 0,
            "high_complexity_functions": [],  # CC >= 10
        },
    }

    all_cc_values = []

    for file_info in repo_files:
        lang = detect_language(file_info["path"])
        if lang != "python":
            # Radon은 Python 전용. 다른 언어는 Lizard 사용
            continue

        cc_blocks = analyze_cyclomatic_complexity(file_info["content"])
        halstead = analyze_halstead(file_info["content"])

        for block in cc_blocks:
            all_cc_values.append(block["complexity"])
            if block["complexity"] >= 10:
                complexity_metrics["summary"]["high_complexity_functions"].append({
                    "file": file_info["path"],
                    **block,
                })

        complexity_metrics["per_file"][file_info["path"]] = {
            "language": "python",
            "cc_blocks": cc_blocks,
            "halstead": halstead,
        }

    if all_cc_values:
        complexity_metrics["summary"]["avg_cc"] = (
            sum(all_cc_values) / len(all_cc_values)
        )
        complexity_metrics["summary"]["max_cc"] = max(all_cc_values)

    return {"complexity_metrics_radon": complexity_metrics}
```

### pyproject.toml 의존성

```toml
radon = ">=6.0.1"
```

## 관련 문서

- 상위: [[complexity-analysis/MOC]]
- 함께 사용: [[complexity-analysis/lizard]] (MI 산출), [[complexity-analysis/sonarqube]] (코드스멜)
- 설계 원본: `plan/v5-design/phase2-infrastructure.md` §9.1 W7
