"""
backend/app/services/chunk_scorer.py
JD-Aware Chunk Relevance Scoring Engine [JIT-22]

청크(함수/클래스) 수준의 JD 관련성 스코어링.
analyze_directory() (JIT-21)가 추출한 청크 메타데이터를 활용.

Score = JD키워드매칭(40%) + 구조적복잡도(25%) + 면접잠재력(20%) + 후보자기여(15%)
"""
from __future__ import annotations

import logging
import math

from app.services.scoring_formulas import _fuzzy_skill_match

logger = logging.getLogger(__name__)

# 스코어 가중치
WEIGHT_JD_KEYWORD = 0.40
WEIGHT_COMPLEXITY = 0.25
WEIGHT_INTERVIEW = 0.20
WEIGHT_CONTRIBUTOR = 0.15

# 면접 잠재력 감지 패턴 (키워드 → 점수 기여)
_INTERVIEW_PATTERNS: dict[str, float] = {
    # 에러 핸들링
    "try": 0.15,
    "except": 0.15,
    "catch": 0.15,
    "finally": 0.10,
    # 비동기
    "async": 0.20,
    "await": 0.15,
    # API 데코레이터
    "app.get": 0.20,
    "app.post": 0.20,
    "app.put": 0.15,
    "app.delete": 0.15,
    "router.get": 0.20,
    "router.post": 0.20,
    # 디자인 패턴 키워드
    "singleton": 0.25,
    "factory": 0.20,
    "observer": 0.20,
    "strategy": 0.20,
    "decorator": 0.15,
    "repository": 0.15,
    # 제어 흐름 복잡성
    "yield": 0.15,
    "generator": 0.15,
    "recursion": 0.15,
    # 테스트 관련
    "pytest": 0.10,
    "unittest": 0.10,
    "mock": 0.10,
}

# CC 정규화 범위
_CC_MIN = 1.0
_CC_MAX = 30.0


def _calculate_jd_keyword_score(
    chunk: dict,
    jd_tech_stack: list[str],
) -> tuple[float, list[str]]:
    """JD 키워드 매칭 점수 (0.0-1.0)

    chunk의 identifiers, imports, decorators를 jd_tech_stack과 퍼지 매칭.

    Returns:
        (score, evidence_list)
    """
    if not jd_tech_stack:
        return 0.0, []

    identifiers = set(chunk.get("identifiers", []))
    imports = set(chunk.get("imports", []))
    decorators = set(chunk.get("decorators", []))

    # 모든 청크 토큰을 하나의 집합으로 합침
    all_tokens: set[str] = set()
    for ident in identifiers:
        all_tokens.add(ident.lower())
    for imp in imports:
        # import 문에서 모듈명 추출 (예: "from fastapi import ..." → "fastapi")
        for part in imp.lower().replace("from ", "").replace("import ", "").split():
            all_tokens.add(part.strip(",").strip())
    for dec in decorators:
        for part in dec.lower().split("."):
            all_tokens.add(part.strip())

    matched_count = 0
    evidence: list[str] = []

    for jd_skill in jd_tech_stack:
        best_score = 0.0
        best_token = ""

        for token in all_tokens:
            score = _fuzzy_skill_match(jd_skill, token)
            if score > best_score:
                best_score = score
                best_token = token
                if score >= 1.0:
                    break

        if best_score >= 0.6:
            matched_count += 1
            evidence.append(f"JD '{jd_skill}' ↔ '{best_token}' ({best_score:.1f})")

    score = matched_count / max(len(jd_tech_stack), 1)
    return min(1.0, score), evidence


def _calculate_complexity_score(
    chunk: dict,
) -> tuple[float, list[str]]:
    """구조적 복잡도 점수 (0.0-1.0)

    Lizard CC 사용 가능 시 정규화, 아니면 라인수 휴리스틱.

    Returns:
        (score, evidence_list)
    """
    source_code = chunk.get("source_code", "")
    evidence: list[str] = []

    # Lizard CC 계산 시도
    cc_value = _get_lizard_cc(source_code)
    if cc_value is not None and cc_value > 0:
        # CC 1~30 → 0.0~1.0 정규화
        normalized = min(1.0, max(0.0, (cc_value - _CC_MIN) / (_CC_MAX - _CC_MIN)))
        evidence.append(f"Lizard CC={cc_value:.1f} → {normalized:.2f}")
        return normalized, evidence

    # Fallback: 라인수 휴리스틱
    line_count = len(source_code.splitlines()) if source_code else 0
    if line_count <= 0:
        return 0.0, ["source 없음"]

    # 5~100줄 → 0.0~1.0 (log scale)
    normalized = min(1.0, max(0.0, math.log10(max(line_count, 1)) / math.log10(100)))
    evidence.append(f"라인수 휴리스틱: {line_count}줄 → {normalized:.2f}")
    return normalized, evidence


def _get_lizard_cc(source_code: str) -> float | None:
    """Lizard로 소스 코드의 평균 CC를 계산. 실패 시 None."""
    if not source_code or len(source_code) < 10:
        return None

    try:
        import lizard
        analysis = lizard.analyze_file.analyze_source_code("chunk.py", source_code)
        if analysis.function_list:
            avg_cc = sum(f.cyclomatic_complexity for f in analysis.function_list) / len(analysis.function_list)
            return avg_cc
    except Exception:
        pass

    return None


def _calculate_interview_potential(
    chunk: dict,
) -> tuple[float, list[str]]:
    """면접 잠재력 점수 (0.0-1.0)

    패턴 감지: try/except, async, API decorator, 디자인 패턴 키워드 등.

    Returns:
        (score, evidence_list)
    """
    source_code = (chunk.get("source_code", "") or "").lower()
    decorators = [d.lower() for d in chunk.get("decorators", [])]
    identifiers = [i.lower() for i in chunk.get("identifiers", [])]
    evidence: list[str] = []

    raw_score = 0.0

    # 소스 코드 기반 패턴 검색
    for pattern, weight in _INTERVIEW_PATTERNS.items():
        if pattern in source_code:
            raw_score += weight
            evidence.append(f"패턴 '{pattern}' 감지 (+{weight:.2f})")

    # 데코레이터 기반 추가 점수
    for dec in decorators:
        for pattern, weight in _INTERVIEW_PATTERNS.items():
            if pattern in dec:
                raw_score += weight * 0.5  # 데코레이터 중복 방지용 0.5배
                break

    # 중첩 제어 흐름 (들여쓰기 깊이 휴리스틱)
    lines = (chunk.get("source_code", "") or "").splitlines()
    max_indent = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped:
            indent = len(line) - len(stripped)
            max_indent = max(max_indent, indent)
    if max_indent >= 16:  # 4단계 이상 중첩 (4스페이스 기준)
        raw_score += 0.15
        evidence.append(f"깊은 중첩 (indent={max_indent})")

    # 0.0~1.0 클램핑 (raw가 1.0 초과 가능)
    score = min(1.0, max(0.0, raw_score))
    return score, evidence


def calculate_chunk_score(
    chunk: dict,
    jd_tech_stack: list[str],
    contributor_ratio: float | None = None,
) -> ChunkRelevanceScore:
    """단일 청크의 JD-Aware 관련성 점수 계산

    Args:
        chunk: analyze_directory() 반환 청크 dict
            keys: name, type, identifiers, imports, decorators, source_code, char_count, file_path
        jd_tech_stack: JD에서 추출한 기술 스택 키워드
        contributor_ratio: 후보자 기여 비율 (0.0-1.0). None이면 기본값 0.5

    Returns:
        ChunkRelevanceScore
    """
    # 1. JD 키워드 매칭 (40%)
    jd_score, jd_evidence = _calculate_jd_keyword_score(chunk, jd_tech_stack)

    # 2. 구조적 복잡도 (25%)
    cx_score, cx_evidence = _calculate_complexity_score(chunk)

    # 3. 면접 잠재력 (20%)
    ip_score, ip_evidence = _calculate_interview_potential(chunk)

    # 4. 후보자 기여 (15%)
    ct_score = contributor_ratio if contributor_ratio is not None else 0.5
    ct_score = min(1.0, max(0.0, ct_score))
    ct_evidence = [f"기여율: {ct_score:.2f}" + (" (기본값)" if contributor_ratio is None else "")]

    # 가중 합산
    total = (
        jd_score * WEIGHT_JD_KEYWORD
        + cx_score * WEIGHT_COMPLEXITY
        + ip_score * WEIGHT_INTERVIEW
        + ct_score * WEIGHT_CONTRIBUTOR
    )
    total = min(1.0, max(0.0, total))

    all_evidence = jd_evidence + cx_evidence + ip_evidence + ct_evidence

    from app.models.analysis import ChunkRelevanceScore
    return ChunkRelevanceScore(
        chunk_name=chunk.get("name", ""),
        chunk_type=chunk.get("type", "function"),
        file_path=chunk.get("file_path", ""),
        jd_keyword_score=round(jd_score, 4),
        complexity_score=round(cx_score, 4),
        interview_potential=round(ip_score, 4),
        contributor_score=round(ct_score, 4),
        total_score=round(total, 4),
        char_count=chunk.get("char_count", 0),
        evidence=all_evidence,
    )


def rank_chunks_by_relevance(
    chunks: list[dict],
    jd_tech_stack: list[str],
    token_budget: int = 50_000,
    contributor_ratio: float | None = None,
) -> list[dict]:
    """청크를 JD 관련성 기준으로 랭킹 + 토큰 예산 내 선택

    Knapsack 방식: 큰 청크 스킵 후에도 작은 고점수 청크 포함 가능.

    Args:
        chunks: analyze_directory() 반환 청크 리스트
        jd_tech_stack: JD 기술 스택
        token_budget: 토큰 예산 (char_count // 4 ≈ tokens)
        contributor_ratio: 후보자 기여 비율

    Returns:
        원본 chunk dict + "relevance_score" 키 추가된 리스트 (점수 내림차순)
    """
    if not chunks:
        return []

    # 1. 모든 청크에 점수 계산
    scored: list[tuple[ChunkRelevanceScore, dict]] = []
    for chunk in chunks:
        score = calculate_chunk_score(chunk, jd_tech_stack, contributor_ratio)
        scored.append((score, chunk))

    # 2. 점수 내림차순 정렬
    scored.sort(key=lambda x: x[0].total_score, reverse=True)

    # 3. 토큰 예산 내 선택 (Knapsack: 큰 청크 스킵 후 작은 것 계속 시도)
    selected: list[dict] = []
    used_tokens = 0

    for score, chunk in scored:
        est_tokens = chunk.get("char_count", 0) // 4
        if est_tokens <= 0:
            continue

        if used_tokens + est_tokens > token_budget:
            # 예산 초과하지만 계속 순회 (작은 청크가 뒤에 있을 수 있음)
            continue

        enriched = {
            **chunk,
            "relevance_score": score.model_dump(),
        }
        selected.append(enriched)
        used_tokens += est_tokens

    logger.info(
        f"rank_chunks: {len(selected)}/{len(chunks)} chunks selected "
        f"({used_tokens} est tokens, budget={token_budget})"
    )
    return selected
