"""
backend/app/services/code_analysis_prompts.py
HYBRID 3-Stage Multi-Agent 분석용 프롬프트 빌더

Extracted from code_analyzer.py for SRP compliance.
"""


def build_overview_prompt(
    files: list[dict],
    commit_diffs: list[dict],
    ast_summary: dict,
    jd_tech_stack: list[str],
) -> str:
    """Stage 1: Overview Agent 프롬프트 생성"""
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

    return f"""Analyze this repository to identify key files for technical interview preparation.

## Target Tech Stack (from Job Description)
{', '.join(jd_tech_stack) if jd_tech_stack else 'Not specified'}

## File Summary ({len(files)} files)
{file_summary}

## Recent Code Changes (Top Diffs)
{diff_summary}

## AST Summary
{ast_info}

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
) -> str:
    """Stage 2: Deep Analysis Agent 프롬프트 생성"""
    file_path = file_info.get("path", file_info.get("filename", "unknown"))
    diff_content = file_info.get("diff", file_info.get("diff_preview", ""))[:2000]

    commit_info = "\n".join([
        f"- {c.get('commit_hash', '')} ({c.get('date', '')}): {c.get('message', '')[:100]}"
        for c in commit_history[:5]
    ])

    return f"""Perform deep analysis on this file for technical interview preparation.

## File: {file_path}

## Target Tech Stack
{', '.join(jd_tech_stack) if jd_tech_stack else 'Not specified'}

## Code/Diff Content
```
{diff_content}
```

## Commit History
{commit_info if commit_info else 'No commit history available'}

## Your Task
1. Identify design patterns used
2. Identify algorithms implemented
3. Assess code quality (0.0-1.0 scale)
4. Generate potential interview questions
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

    deep_summaries = []
    for i, da in enumerate(deep_analyses[:10], 1):
        deep_summaries.append(f"""
### File {i}: {da.get('file_path', 'unknown')}
- Patterns: {', '.join(da.get('patterns_found', [])) or 'None'}
- Algorithms: {', '.join(da.get('algorithms_used', [])) or 'None'}
- Quality Score: {da.get('code_quality_score', 'N/A')}
- Notable: {', '.join(da.get('notable_aspects', [])[:3]) or 'None'}
- Questions: {len(da.get('question_candidates', []))} candidates
""")

    return f"""Synthesize all analysis results for repository: {repo_name}

## Target Tech Stack
{', '.join(jd_tech_stack) if jd_tech_stack else 'Not specified'}

## Overview Analysis
{overview_summary}

## Deep Analysis Results
{''.join(deep_summaries) if deep_summaries else 'No deep analysis results'}

## Your Task
1. Synthesize all findings into a coherent assessment
2. Rank notable implementations by interview question potential
3. Deduplicate and prioritize patterns/algorithms
4. Generate top 10 interview questions
5. Provide overall quality and candidate assessment

Respond in JSON format:
{{
    "notable_implementations": [
        {{
            "title": "Implementation title",
            "description": "What it does",
            "file_path": "path/to/file.py",
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
