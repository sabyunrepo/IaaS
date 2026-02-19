"""
QualityScanner Worker (W8) — SonarQube 정적 분석.

SonarQube API를 통해 코드 품질 리포트를 조회한다.
SonarQube 프로젝트가 등록되어 있어야 동작.
미등록 시 빈 리포트 반환.
"""
from __future__ import annotations

import os
from typing import Any

from application.states.logic_state import LogicState
from infrastructure.analysis.sonarqube_adapter import SonarQubeAdapter


async def quality_scanner_worker(state: LogicState) -> dict[str, Any]:
    """SonarQube 정적 분석 결과를 조회한다."""
    job_id = state.get("job_id", "")

    sonarqube_url = os.environ.get("SONARQUBE_URL", "http://sonarqube:9000")
    sonarqube_token = os.environ.get("SONARQUBE_TOKEN", "")

    if not sonarqube_token:
        return {"quality_report": {"status": "skipped", "reason": "no_sonarqube_token"}}

    adapter = SonarQubeAdapter(base_url=sonarqube_url, token=sonarqube_token)

    # SonarQube 프로젝트 키는 job_id 기반
    project_key = f"jittda-{job_id[:8]}"

    try:
        report = await adapter.get_quality_report(project_key)
        return {"quality_report": report.model_dump() if hasattr(report, "model_dump") else report}
    except Exception:
        return {"quality_report": {"status": "unavailable", "reason": "sonarqube_error"}}
