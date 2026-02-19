"""
ComplexityMeter Worker (W7) — Radon/Lizard 복잡도 측정.

Python → Radon, 다국어 → Lizard.
"""
from __future__ import annotations

from typing import Any

from application.states.logic_state import LogicState
from infrastructure.analysis.complexity_adapter import LizardAdapter, RadonAdapter


async def complexity_meter_worker(state: LogicState) -> dict[str, Any]:
    """코드 복잡도 메트릭을 산출한다."""
    cleaned_diffs = state.get("cleaned_diffs", [])

    radon = RadonAdapter()
    lizard = LizardAdapter()
    results = []

    for diff in cleaned_diffs:
        language = diff.get("language", "")
        bodies = diff.get("function_bodies", [])
        code = "\n\n".join(bodies)
        if not code.strip():
            continue

        try:
            if language == "python":
                metrics = radon.analyze(code)
            else:
                filename = LizardAdapter.filename_for_language(language)
                metrics = lizard.analyze(code, language=language, filename=filename)

            results.append({
                "file_path": diff.get("file_path", ""),
                "language": language,
                **metrics.model_dump(),
            })
        except Exception:
            continue

    return {"complexity_metrics": results}
