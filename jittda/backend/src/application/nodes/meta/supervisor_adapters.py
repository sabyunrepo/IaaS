"""
Supervisor Adapter 노드 — 서브그래프 ↔ MetaState 변환.

각 Supervisor 서브그래프는 자체 State를 사용하므로,
MetaState에서 입력을 추출하고 결과를 DB에 저장한 뒤 참조 ID를 반환한다.
Reference Passing: Load → Process → Save → Return Ref
"""
from __future__ import annotations

import os
from typing import Any

from application.graphs.forensic_graph import build_forensic_graph
from application.graphs.logic_graph import build_logic_graph
from application.graphs.stack_graph import build_stack_graph
from application.states.meta_state import MetaState
from infrastructure.persistence.repository import (
    AnalysisRepository,
    IdentityRepository,
    JobRepository,
)


async def forensic_supervisor_node(state: MetaState) -> dict[str, Any]:
    """ForensicSupervisor 서브그래프를 실행하고 결과를 DB에 저장한다."""
    job_id = state["job_id"]
    db_url = os.environ.get("DATABASE_URL", "")

    # 1. Load: MetaState → ForensicState 입력 구성
    job_repo = JobRepository(db_url)
    job = await job_repo.get(job_id)
    input_data = job.get("input_data", {}) if job else {}

    forensic_input = {
        "job_id": job_id,
        "github_urls": input_data.get("github_urls", []),
        "candidate_username": input_data.get("candidate_username"),
        "linkedin_url": input_data.get("linkedin_url"),
        "jd_languages": input_data.get("jd_languages", []),
        "jd_tech_stack": input_data.get("jd_tech_stack", []),
        "collected_repos": [],
        "repo_local_paths": [],
        "identity_cluster": None,
        "blame_attributions": [],
        "pure_contributions": [],
        "cleaned_diffs": [],
        "vibector_scores": [],
        "clave_fingerprint": None,
        "plagiarism_report": None,
        "forensic_summary": None,
        "authenticity_score": None,
    }

    # 2. Process: 서브그래프 실행
    graph = build_forensic_graph().compile()
    result = await graph.ainvoke(forensic_input)

    # 3. Save: DB에 저장
    analysis_repo = AnalysisRepository(db_url)
    result_id = await analysis_repo.save_result(
        job_id,
        "forensic_supervisor",
        "forensic",
        {
            "forensic_summary": result.get("forensic_summary"),
            "authenticity_score": result.get("authenticity_score"),
            "total_files_analyzed": len(result.get("pure_contributions", [])),
            "ai_detection": result.get("forensic_summary", {}).get("ai_detection"),
            "style_consistency": result.get("forensic_summary", {}).get("style_consistency"),
            "plagiarism": result.get("plagiarism_report"),
        },
    )

    # Identity Resolution도 저장
    identity = result.get("identity_cluster")
    identity_ref = None
    if identity:
        identity_repo = IdentityRepository(db_url)
        identity_ref = await identity_repo.save(
            job_id,
            identity.get("github_node_id", ""),
            identity.get("canonical_name", ""),
            identity.get("canonical_email", ""),
            identity.get("aliases", []),
            identity.get("total_commits", 0),
            identity.get("verified_commits", 0),
            sum(c.get("pure_logic_lines", 0) for c in result.get("pure_contributions", [])),
        )

    # 4. Return Ref
    return {
        "forensic_result_ref": result_id,
        "identity_cluster_ref": identity_ref,
    }


async def logic_supervisor_node(state: MetaState) -> dict[str, Any]:
    """LogicSupervisor 서브그래프를 실행하고 결과를 DB에 저장한다."""
    job_id = state["job_id"]
    db_url = os.environ.get("DATABASE_URL", "")

    # 1. Load: MetaState → LogicState 입력 구성
    job_repo = JobRepository(db_url)
    job = await job_repo.get(job_id)
    input_data = job.get("input_data", {}) if job else {}

    logic_input = {
        "job_id": job_id,
        "cleaned_diffs": [],  # ForensicSupervisor와 독립 — 직접 분석
        "repo_local_paths": input_data.get("repo_local_paths", []),
        "ast_analysis": [],
        "complexity_metrics": [],
        "quality_report": None,
        "logic_summary": None,
        "logic_score": None,
    }

    # 2. Process
    graph = build_logic_graph().compile()
    result = await graph.ainvoke(logic_input)

    # 3. Save
    analysis_repo = AnalysisRepository(db_url)
    result_id = await analysis_repo.save_result(
        job_id,
        "logic_supervisor",
        "logic",
        {
            "logic_summary": result.get("logic_summary"),
            "logic_score": result.get("logic_score"),
            "ast_analysis": result.get("ast_analysis"),
            "files_analyzed": len(result.get("ast_analysis", [])),
            "avg_cyclomatic_complexity": result.get("logic_summary", {}).get(
                "avg_cyclomatic_complexity", 0
            ),
            "avg_maintainability_index": result.get("logic_summary", {}).get(
                "avg_maintainability_index", 0
            ),
        },
    )

    # 4. Return Ref
    return {"logic_result_ref": result_id}


async def stack_supervisor_node(state: MetaState) -> dict[str, Any]:
    """StackSupervisor 서브그래프를 실행하고 결과를 DB에 저장한다."""
    job_id = state["job_id"]
    db_url = os.environ.get("DATABASE_URL", "")

    # 1. Load: LogicSupervisor의 AST 결과를 DB에서 로드
    analysis_repo = AnalysisRepository(db_url)
    logic_ref = state.get("logic_result_ref")
    logic_data = await analysis_repo.get_result(logic_ref) if logic_ref else None

    ast_analysis = []
    if logic_data:
        ast_analysis = logic_data.get("result_data", {}).get("ast_analysis", [])

    job_repo = JobRepository(db_url)
    job = await job_repo.get(job_id)
    input_data = job.get("input_data", {}) if job else {}

    stack_input = {
        "job_id": job_id,
        "ast_analysis": ast_analysis,
        "cleaned_diffs": [],
        "jd_tech_stack": input_data.get("jd_tech_stack", []),
        "skill_extraction": None,
        "api_depth_scores": [],
        "architecture_eval": None,
        "stack_summary": None,
        "mastery_score": None,
    }

    # 2. Process
    graph = build_stack_graph().compile()
    result = await graph.ainvoke(stack_input)

    # 3. Save
    result_id = await analysis_repo.save_result(
        job_id,
        "stack_supervisor",
        "stack",
        {
            "stack_summary": result.get("stack_summary"),
            "mastery_score": result.get("mastery_score"),
            "total_skills_detected": result.get("stack_summary", {}).get(
                "total_skills_detected", 0
            ),
            "avg_api_depth": result.get("stack_summary", {}).get("avg_api_depth", 0),
            "architecture_score": result.get("stack_summary", {}).get("architecture_score"),
        },
    )

    # 4. Return Ref
    return {"stack_result_ref": result_id}
