"""
Datasketch Worker (W5) — MinHash/LSH 기반 표절 탐지.

코드 청크 간 Jaccard 유사도로 표절 비율을 산출한다.
"""
from __future__ import annotations

from typing import Any

from application.states.forensic_state import ForensicState
from infrastructure.analysis.datasketch_adapter import DatasketchAdapter


async def datasketch_worker(state: ForensicState) -> dict[str, Any]:
    """코드 청크의 표절 비율을 MinHash/LSH로 분석한다."""
    cleaned_diffs = state.get("cleaned_diffs", [])

    if not cleaned_diffs:
        return {"plagiarism_report": None}

    adapter = DatasketchAdapter()

    # 후보자 코드 청크 수집
    candidate_chunks = []
    for diff in cleaned_diffs:
        for body in diff.get("function_bodies", []):
            if len(body.strip()) > 50:  # 최소 50자 이상
                candidate_chunks.append(body)

    if not candidate_chunks:
        return {"plagiarism_report": None}

    # LSH 인덱스에 등록하고 자기 유사도 검사 (코드 중복 탐지)
    pairwise_scores = []
    for i, chunk_a in enumerate(candidate_chunks[:30]):
        for chunk_b in candidate_chunks[i + 1 : min(i + 6, len(candidate_chunks))]:
            sim = adapter.compute_pairwise_similarity(chunk_a, chunk_b)
            if sim > 0.6:
                pairwise_scores.append({"chunk_a_idx": i, "similarity": sim})

    # 전체 표절 비율 (자기 중복 비율)
    plagiarism_ratio = adapter.compute_plagiarism_ratio(
        candidate_chunks[:30], candidate_chunks[:30]
    )

    report = {
        "total_chunks_analyzed": len(candidate_chunks[:30]),
        "high_similarity_pairs": len(pairwise_scores),
        "plagiarism_ratio": plagiarism_ratio,
        "suspicious_pairs": pairwise_scores[:10],
    }

    return {"plagiarism_report": report}
