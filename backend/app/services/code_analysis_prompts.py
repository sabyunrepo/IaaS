"""
backend/app/services/code_analysis_prompts.py
HYBRID 3-Stage Multi-Agent 분석용 프롬프트 빌더

Extracted from code_analyzer.py for SRP compliance.

JIT-24: AST 청크 메타데이터 + 완전한 소스코드 입력 지원
"""


def build_overview_prompt(
    files: list[dict],
    commit_diffs: list[dict],
    ast_summary: dict,
    jd_tech_stack: list[str],
    ranked_chunks: list[dict] | None = None,
) -> str:
    """Stage 1: Overview Agent 프롬프트 생성

    Args:
        files: PyDriller로 추출한 파일 목록
        commit_diffs: 커밋별 diff 데이터
        ast_summary: AST 분석 결과
        jd_tech_stack: JD에서 추출한 기술 스택
        ranked_chunks: JD-Aware 랭킹된 청크 리스트 (JIT-24, optional)
    """
    file_summary = "\n".join([
        f"- {f.get('filename', 'unknown')}: {f.get('added', 0)} additions, complexity={f.get('complexity', 0)}"
        for f in files[:30]
    ])

    diff_summary = "\n".join([
        f"### {d.get('file_path', '')} ({d.get('commit_hash', '')})\n"
        f"```diff\n{d.get('diff', '')[:800]}\n```"
        for d in commit_diffs[:10]
    ])

    ast_info = (
        f"Functions: {len(ast_summary.get('functions', []))}, "
        f"Classes: {len(ast_summary.get('classes', []))}, "
        f"Parser: {ast_summary.get('parser_used', 'N/A')}"
    )

    # JIT-24: 청크 메타데이터 섹션 (AST 파이프라인 활성 시)
    chunk_section = ""
    if ranked_chunks:
        chunk_lines = []
        for c in ranked_chunks[:15]:
            score_info = c.get("relevance_score", {})
            total = score_info.get("total_score", 0) if isinstance(score_info, dict) else 0
            jd_score = score_info.get("jd_keyword_score", 0) if isinstance(score_info, dict) else 0
            chunk_lines.append(
                f"- **{c.get('name', '?')}** ({c.get('type', '?')}) "
                f"in `{c.get('file_path', '?')}` — "
                f"JD={jd_score:.2f}, Total={total:.2f}, "
                f"{c.get('char_count', 0)} chars"
            )
            # 식별자/import 힌트
            idents = c.get("identifiers", [])[:5]
            imps = c.get("imports", [])[:3]
            if idents:
                chunk_lines.append(f"  identifiers: {', '.join(idents)}")
            if imps:
                chunk_lines.append(f"  imports: {', '.join(imps)}")
        chunk_section = f"""
## JD-Ranked Code Chunks ({len(ranked_chunks)} selected)
{chr(10).join(chunk_lines)}
"""

    return f"""Analyze this repository to identify key files for technical interview preparation.

## Target Tech Stack (from Job Description)
{', '.join(jd_tech_stack) if jd_tech_stack else 'Not specified'}

## File Summary ({len(files)} files)
{file_summary}

## Recent Code Changes (Top Diffs)
{diff_summary}

## AST Summary
{ast_info}
{chunk_section}
## Your Task
1. Select 5-10 key files that best demonstrate the candidate's technical skills matching the JD tech stack
2. Provide a technical overview of the repository
3. Identify initial candidate strengths

Respond in JSON format:
{{
    "key_files": [
        {{"path": "...", "relevance_score": 0.0-1.0, "reason": "...", "language": "...", "complexity": 0}}
    ],
    "tech_overview": "Brief technical overview of the repository",
    "candidate_strengths": ["strength1", "strength2"],
    "primary_languages": ["Python", "JavaScript"],
    "frameworks_detected": ["FastAPI", "React"]
}}
"""


def build_deep_analysis_prompt(
    file_info: dict,
    commit_history: list[dict],
    jd_tech_stack: list[str],
    token_budget: int = 8000,
) -> str:
    """Stage 2: Deep Analysis Agent 프롬프트 생성

    JIT-24: source_code 필드 우선 사용 (완전한 함수/클래스 코드).
    fallback: diff → diff_preview (기존 호환).

    Args:
        file_info: 분석할 파일 정보 (path, source_code, diff 등)
        commit_history: 해당 파일의 커밋 이력
        jd_tech_stack: JD에서 추출한 기술 스택
        token_budget: 소스코드 최대 문자 수 (20K~50K 범위, 기본 8000)
    """
    file_path = file_info.get("path", file_info.get("filename", "unknown"))

    # JIT-28: 토큰 예산 경계 클램핑 (최소 2000, 최대 50000)
    effective_budget = max(2000, min(50_000, token_budget))

    # JIT-24: 완전한 소스코드 우선, diff fallback
    source_code = file_info.get("source_code", "")
    if not source_code:
        source_code = file_info.get("diff", file_info.get("diff_preview", ""))
    # JIT-28: 동적 토큰 예산 적용 (기존 8000자 하드코딩 → 파라미터)
    source_code = source_code[:effective_budget] if source_code else ""

    commit_info = "\n".join([
        f"- {c.get('commit_hash', '')} ({c.get('date', '')}): {c.get('message', '')[:100]}"
        for c in commit_history[:5]
    ])

    # JIT-24: 청크 메타데이터 (identifiers, imports, decorators)
    metadata_section = ""
    identifiers = file_info.get("identifiers", [])
    imports = file_info.get("imports", [])
    decorators = file_info.get("decorators", [])
    relevance_score = file_info.get("relevance_score", {})

    if identifiers or imports or decorators:
        parts = []
        if identifiers:
            parts.append(f"Identifiers: {', '.join(identifiers[:20])}")
        if imports:
            parts.append(f"Imports: {', '.join(imports[:10])}")
        if decorators:
            parts.append(f"Decorators: {', '.join(decorators[:5])}")
        if isinstance(relevance_score, dict) and relevance_score:
            parts.append(
                f"JD Relevance: {relevance_score.get('jd_keyword_score', 0):.2f}, "
                f"Interview Potential: {relevance_score.get('interview_potential', 0):.2f}"
            )
        metadata_section = f"""
## Code Metadata (AST-extracted)
{chr(10).join(parts)}
"""

    # 코드 블록 라벨
    code_label = "Source Code" if file_info.get("source_code") else "Code/Diff Content"

    return f"""Perform deep analysis on this file for technical interview preparation.

## File: {file_path}

## Target Tech Stack
{', '.join(jd_tech_stack) if jd_tech_stack else 'Not specified'}
{metadata_section}
## {code_label}
```
{source_code}
```

## Commit History
{commit_info if commit_info else 'No commit history available'}

## Your Task
1. Identify design patterns used
2. Identify algorithms implemented
3. Assess code quality (0.0-1.0 scale)
4. Generate potential interview questions based on this specific code
5. Note any remarkable implementation aspects

Respond in JSON format:
{{
    "file_path": "{file_path}",
    "patterns_found": ["Singleton", "Factory"],
    "algorithms_used": ["Binary Search", "DFS"],
    "code_quality_score": 0.0-1.0,
    "quality_notes": "Notes about code quality",
    "question_candidates": ["How would you optimize...", "Explain your choice of..."],
    "notable_aspects": ["Efficient caching implementation", "Clean error handling"],
    "complexity_assessment": "Assessment of code complexity"
}}
"""


def build_synthesis_prompt(
    overview: dict,
    deep_analyses: list[dict],
    repo_info: dict,
    jd_tech_stack: list[str],
) -> str:
    """Stage 3: Synthesis Agent 프롬프트 생성"""
    repo_name = repo_info.get("name", "unknown")

    overview_summary = f"""
Tech Overview: {overview.get('tech_overview', 'N/A')}
Primary Languages: {', '.join(overview.get('primary_languages', []))}
Frameworks: {', '.join(overview.get('frameworks_detected', []))}
Key Files Analyzed: {len(overview.get('key_files', []))}
"""

    # JIT-28: Overview key_files에서 JD relevance 정보 추출
    jd_relevance_section = ""
    key_files = overview.get("key_files", [])
    if key_files:
        jd_lines = []
        for kf in key_files[:10]:
            path = kf.get("path", "unknown")
            score = kf.get("relevance_score", 0)
            reason = kf.get("reason", "")
            jd_lines.append(f"- `{path}`: relevance={score}, {reason}")
        jd_relevance_section = f"""
## JD Relevance Ranking
{chr(10).join(jd_lines)}
"""

    deep_summaries = []
    for i, da in enumerate(deep_analyses[:10], 1):
        # JIT-28: JD relevance score 반영
        relevance = da.get("relevance_score", {})
        jd_score_line = ""
        if isinstance(relevance, dict) and relevance:
            jd_kw = relevance.get("jd_keyword_score", 0)
            interview_pot = relevance.get("interview_potential", 0)
            confidence = relevance.get("confidence", "N/A")
            jd_score_line = f"\n- JD Relevance: keyword={jd_kw:.2f}, interview_potential={interview_pot:.2f}, confidence={confidence}"

        deep_summaries.append(f"""
### File {i}: {da.get('file_path', 'unknown')}
- Patterns: {', '.join(da.get('patterns_found', [])) or 'None'}
- Algorithms: {', '.join(da.get('algorithms_used', [])) or 'None'}
- Quality Score: {da.get('code_quality_score', 'N/A')}
- Notable: {', '.join(da.get('notable_aspects', [])[:3]) or 'None'}
- Questions: {len(da.get('question_candidates', []))} candidates{jd_score_line}
""")

    return f"""Synthesize all analysis results for repository: {repo_name}

## Target Tech Stack
{', '.join(jd_tech_stack) if jd_tech_stack else 'Not specified'}

## Overview Analysis
{overview_summary}
{jd_relevance_section}## Deep Analysis Results
{''.join(deep_summaries) if deep_summaries else 'No deep analysis results'}

## Your Task
1. Synthesize all findings into a coherent assessment
2. Rank notable implementations by interview question potential (prioritize higher JD relevance scores)
3. Deduplicate and prioritize patterns/algorithms
4. Generate top 10 interview questions (weight JD-relevant files higher)
5. Provide overall quality and candidate assessment

Respond in JSON format:
{{
    "notable_implementations": [
        {{
            "title": "Implementation title",
            "description": "What it does",
            "file_path": "path/to/file.py",
            "code_snippet": "The most relevant 2-10 lines of actual source code from this implementation",
            "why_notable": "Why this is interesting for interview",
            "question_potential": 0.0-1.0,
            "related_patterns": ["Pattern1"],
            "interview_angles": ["Performance", "Design decisions"]
        }}
    ],
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
    "patterns": ["Singleton", "Factory", "Repository"],
    "algorithms": ["Binary Search", "BFS"],
    "quality_score": 0.0-1.0,
    "quality_summary": "Overall code quality assessment",
    "candidate_assessment": "Assessment of candidate's technical abilities",
    "top_interview_questions": ["Question 1", "Question 2"]
}}
"""
