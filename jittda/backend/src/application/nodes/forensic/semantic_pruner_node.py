"""
Semantic Pruner Worker (W3) — AST 기반 노이즈 제거.

import, 주석, 설정, 자동생성 코드를 제거하여 순수 로직 기여만 추출.
"""
from __future__ import annotations

from typing import Any

from application.states.forensic_state import ForensicState
from domain.identity.semantic_pruner import prune_contribution


async def semantic_pruner_worker(state: ForensicState) -> dict[str, Any]:
    """blame attribution의 코드 라인을 AST 기반으로 정제한다."""
    blame_attributions = state.get("blame_attributions", [])
    collected_repos = state.get("collected_repos", [])

    if not blame_attributions:
        return {
            "pure_contributions": [],
            "cleaned_diffs": [],
        }

    # 파일별로 그룹핑
    file_lines: dict[str, list[str]] = {}
    file_languages: dict[str, str] = {}

    for attr in blame_attributions:
        fp = attr.get("file_path", "")
        if not fp:
            continue
        file_lines.setdefault(fp, []).append(attr.get("content", ""))
        if fp not in file_languages:
            file_languages[fp] = _detect_language(fp)

    # 파일별 pruning
    pure_contributions = []
    cleaned_diffs = []

    for file_path, lines in file_lines.items():
        language = file_languages.get(file_path, "unknown")
        if language == "unknown":
            continue

        contribution = prune_contribution(file_path, language, lines)
        pure_contributions.append(contribution.model_dump())

        # 순수 로직 라인만 diff로 수집
        if contribution.function_bodies:
            cleaned_diffs.append({
                "file_path": file_path,
                "language": language,
                "pure_logic_lines": contribution.pure_logic_lines,
                "function_bodies": contribution.function_bodies,
            })

    return {
        "pure_contributions": pure_contributions,
        "cleaned_diffs": cleaned_diffs,
    }


def _detect_language(file_path: str) -> str:
    """파일 확장자에서 언어를 추론한다."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
    }
    for ext, lang in ext_map.items():
        if file_path.endswith(ext):
            return lang
    return "unknown"
