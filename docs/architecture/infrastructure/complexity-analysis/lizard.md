---
title: "Lizard — MI (Maintainability Index)"
type: component
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [lizard, complexity, maintainability, multi-language, infrastructure]
parent: "[[complexity-analysis/MOC]]"
children: []
depends-on: []
affects:
  - "[[application/nodes/complexity-meter-worker]]"
linear: [JIT-95]
phase: 2
---

# Lizard — MI (Maintainability Index)

## 개요

Lizard는 **다중 언어** 코드 복잡도 분석 도구로,
Python, JavaScript, TypeScript, Java, Go를 포함한 15개 이상 언어를 지원한다.
Radon이 Python 전용인 것과 달리 Lizard는 모든 언어의 CC와
MI(Maintainability Index, 유지보수성 지수)를 산출한다.
ComplexityMeterWorker(W7)에서 Python 이외 언어 파일에 적용된다.

## 상세 설계

### 핵심 메트릭

#### MI (Maintainability Index)

MI는 Halstead Volume, CC, LOC를 결합한 복합 지표다.

```
MI = 171 - 5.2 × ln(Halstead Volume) - 0.23 × CC - 16.2 × ln(LOC)
```

| MI 범위 | 해석 |
|---------|------|
| 85–100 | 유지보수 용이 |
| 65–84 | 보통 |
| 0–64 | 유지보수 어려움 |

#### Lizard 함수 단위 지표

| 필드 | 설명 |
|------|------|
| `cyclomatic_complexity` | 함수 CC |
| `nloc` | 순수 코드 라인 수 (Non-comment LOC) |
| `token_count` | 함수 내 토큰 수 |
| `parameter_count` | 파라미터 수 |
| `length` | 함수 전체 라인 수 (주석 포함) |
| `start_line` | 함수 시작 라인 |
| `end_line` | 함수 끝 라인 |

### 코드 예시

#### 단일 파일 분석

```python
# infrastructure/analysis/complexity_adapter.py
import lizard


def analyze_with_lizard(
    source_code: str, file_path: str
) -> dict:
    """Lizard로 파일 복잡도 분석. Python 이외 모든 언어에 적용.

    Args:
        source_code: 소스코드 문자열
        file_path: 파일 경로 (언어 감지용 — 확장자 기반)

    Returns:
        {
            "average_cyclomatic_complexity": float,
            "average_nloc": float,
            "average_token_count": float,
            "total_nloc": int,
            "functions": [
                {
                    "name": str,
                    "cyclomatic_complexity": int,
                    "nloc": int,
                    "token_count": int,
                    "parameter_count": int,
                    "start_line": int,
                    "end_line": int,
                },
                ...
            ],
        }
    """
    # lizard.analyze_file.analyze_source_code(언어, 코드)
    # 또는 파일 경로 기반으로 언어 자동 감지
    result = lizard.analyze_file.analyze_source_code(
        file_path,  # 경로로 언어 감지 (실제 파일 읽기 아님)
        source_code,
    )

    functions = [
        {
            "name": func.name,
            "cyclomatic_complexity": func.cyclomatic_complexity,
            "nloc": func.nloc,
            "token_count": func.token_count,
            "parameter_count": func.parameter_count,
            "start_line": func.start_line,
            "end_line": func.end_line,
            "long_name": func.long_name,  # 클래스::메서드 형식
        }
        for func in result.function_list
    ]

    return {
        "average_cyclomatic_complexity": result.average_cyclomatic_complexity,
        "average_nloc": result.average_nloc,
        "average_token_count": result.average_token_count,
        "total_nloc": result.nloc,
        "functions": functions,
    }
```

#### MI 산출

```python
import math


def compute_mi(
    halstead_volume: float, cyclomatic_complexity: int, loc: int
) -> float:
    """MI(Maintainability Index) 직접 계산.

    Microsoft Visual Studio 공식 기반:
        MI = 171 - 5.2 × ln(V) - 0.23 × CC - 16.2 × ln(LOC)

    반환값은 0~100 범위로 정규화.

    Args:
        halstead_volume: Radon h_visit()의 volume 값
        cyclomatic_complexity: 함수/파일 CC
        loc: 코드 라인 수 (공백/주석 제외)
    """
    if halstead_volume <= 0 or loc <= 0:
        return 0.0

    raw_mi = (
        171
        - 5.2 * math.log(halstead_volume)
        - 0.23 * cyclomatic_complexity
        - 16.2 * math.log(loc)
    )
    # 0~100 범위로 정규화 (max(0, raw_mi * 100 / 171))
    return max(0.0, min(100.0, raw_mi * 100 / 171))


def mi_rank(mi_score: float) -> str:
    """MI 점수를 등급으로 변환."""
    if mi_score >= 85:
        return "A"  # 유지보수 용이
    elif mi_score >= 65:
        return "B"  # 보통
    else:
        return "C"  # 유지보수 어려움
```

#### 임계값 필터 — 고위험 함수 탐지

```python
def find_high_risk_functions(
    lizard_result: dict,
    cc_threshold: int = 10,
    nloc_threshold: int = 50,
) -> list[dict]:
    """CC >= threshold 또는 NLOC >= threshold인 함수 추출.

    Args:
        cc_threshold: CC 위험 임계값 (기본 10)
        nloc_threshold: NLOC 위험 임계값 (기본 50줄)

    Returns:
        위험 함수 목록 (파일 경로 포함)
    """
    high_risk = []
    for func in lizard_result.get("functions", []):
        if (
            func["cyclomatic_complexity"] >= cc_threshold
            or func["nloc"] >= nloc_threshold
        ):
            high_risk.append({
                **func,
                "risk_reason": (
                    "high_cc" if func["cyclomatic_complexity"] >= cc_threshold
                    else "long_function"
                ),
            })
    return high_risk
```

#### ComplexityMeterWorker(W7) 통합

```python
# application/nodes/complexity_meter_worker.py (발췌)
from infrastructure.analysis.complexity_adapter import analyze_with_lizard
from infrastructure.analysis.language_detector import detect_language


async def complexity_meter_worker(state: dict) -> dict:
    """W7: Radon(Python) + Lizard(그 외) 병합 분석."""
    repo_files: list[dict] = state["repo_files"]
    complexity_metrics = {"per_file": {}, "summary": {"avg_cc": 0.0, "max_cc": 0}}
    all_cc = []

    for file_info in repo_files:
        lang = detect_language(file_info["path"])
        if lang is None:
            continue

        if lang == "python":
            # Python: Radon 사용 (radon.md 참조)
            ...
        else:
            # JS/TS/Java/Go: Lizard 사용
            lizard_result = analyze_with_lizard(
                file_info["content"], file_info["path"]
            )
            complexity_metrics["per_file"][file_info["path"]] = {
                "language": lang,
                "lizard": lizard_result,
            }
            for func in lizard_result["functions"]:
                all_cc.append(func["cyclomatic_complexity"])

    if all_cc:
        complexity_metrics["summary"]["avg_cc"] = sum(all_cc) / len(all_cc)
        complexity_metrics["summary"]["max_cc"] = max(all_cc)

    return {"complexity_metrics": complexity_metrics}
```

### pyproject.toml 의존성

```toml
lizard = ">=1.17.10"
```

## 관련 문서

- 상위: [[complexity-analysis/MOC]]
- 함께 사용: [[complexity-analysis/radon]] (Python CC/Halstead), [[complexity-analysis/sonarqube]] (코드스멜)
- 설계 원본: `plan/v5-design/phase2-infrastructure.md` §9.1 W7
