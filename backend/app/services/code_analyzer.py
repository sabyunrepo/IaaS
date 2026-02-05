"""
backend/app/services/code_analyzer.py
PyDriller + AST + LLM 기반 코드 분석 파이프라인

4-Channel GitHub Analysis의 Channel A (본인 레포 분석) 담당
- diff 기반 코드 추출 (토큰 효율적)
- 분석 기간: GITHUB_ANALYSIS_YEARS 환경변수 (기본 1년)
- HYBRID 3-Stage Multi-Agent 분석 지원 (GLM 모델 비용 최적화)
"""
import logging
from typing import Any

from app.core.config import settings
from app.models.analysis import (
    OverviewAnalysisResult,
    DeepAnalysisResult,
    SynthesisAnalysisResult,
)

logger = logging.getLogger(__name__)

# GLM 모델 설정 (비용 최적화)
# Z.AI GLM 모델 사용 (glm-4.7: 코드 분석용 플래그십)
# settings.GLM_CODER_MODEL 사용 (기본값: zai/glm-4.7)
GLM_MODEL = settings.GLM_CODER_MODEL


class CodeAnalyzer:
    """코드 분석 4-Phase 파이프라인 (Channel A)"""

    async def analyze_with_pydriller(
        self,
        repo_url: str,
        job_id: str,
        author: str | None = None,
        since_years: int | None = None,
        file_types: list[str] | None = None,
        extract_diff: bool = True,  # diff 기반 추출 (기본값)
    ) -> dict:
        """
        PyDriller로 레포 분석 (clone → 커밋 순회 → 메트릭 추출)

        Args:
            repo_url: GitHub 레포 URL
            job_id: Job ID (로깅용)
            author: 후보자 username (커밋 필터)
            since_years: 분석 기간 (None이면 GITHUB_ANALYSIS_YEARS 환경변수 사용)
            file_types: 분석 대상 파일 확장자
            extract_diff: True면 diff만, False면 source_code 추출 (기존 호환)

        Returns:
            {
                "commits": [{hash, msg, date, files_changed}],
                "files": [{filename, diff, complexity, nloc, methods, added, deleted}],
                "commit_diffs": [{commit_hash, file_path, diff, additions, deletions}],
                "stats": {total_commits, total_additions, total_deletions, avg_complexity}
            }
        """
        # 환경변수에서 분석 기간 가져오기 (기본 1년)
        if since_years is None:
            since_years = settings.GITHUB_ANALYSIS_YEARS

        logger.info(f"PyDriller analysis: {repo_url} (author={author}, years={since_years}, diff={extract_diff})")

        # PyDriller import (heavy dependency, lazy load)
        from pydriller import Repository
        from datetime import datetime, timedelta, timezone

        since = datetime.now(timezone.utc) - timedelta(days=since_years * 365)
        commits = []
        files = {}
        commit_diffs = []  # diff 기반 데이터
        total_additions = 0
        total_deletions = 0

        try:
            # Heartbeat helper (Activity 컨텍스트에서만 동작)
            def _heartbeat(msg: str):
                try:
                    from temporalio import activity
                    activity.heartbeat(msg)
                except Exception:
                    pass  # Activity 외부 호출 시 무시

            commit_count = 0
            for commit in Repository(
                repo_url,
                since=since,
                only_authors=[author] if author else None,
                only_modifications_with_file_types=file_types,
            ).traverse_commits():
                # 20개 커밋마다 heartbeat (Temporal 타임아웃 방지)
                commit_count += 1
                if commit_count % 20 == 0:
                    _heartbeat(f"PyDriller: processed {commit_count} commits...")

                commits.append({
                    "hash": commit.hash[:8],
                    "msg": commit.msg[:200],
                    "date": commit.committer_date.isoformat(),
                    "files_changed": len(commit.modified_files),
                })

                for mod in commit.modified_files:
                    # diff 기반 추출 (토큰 효율적)
                    if extract_diff:
                        diff_content = mod.diff[:2000] if mod.diff else ""
                        commit_diffs.append({
                            "commit_hash": commit.hash[:8],
                            "message": commit.msg[:100],
                            "date": commit.committer_date.isoformat(),
                            "file_path": mod.filename,
                            "diff": diff_content,
                            "additions": mod.added_lines,
                            "deletions": mod.deleted_lines,
                            "complexity": mod.complexity or 0,
                        })

                    # 파일별 집계 (AST 분석용)
                    if mod.filename not in files:
                        files[mod.filename] = {
                            "filename": mod.filename,
                            "complexity": mod.complexity or 0,
                            "nloc": mod.nloc or 0,
                            "methods": len(mod.methods) if mod.methods else 0,
                            "added": 0,
                            "deleted": 0,
                        }
                        # diff 모드가 아닐 때만 source_code 추출 (기존 호환)
                        if not extract_diff:
                            files[mod.filename]["source"] = (
                                mod.source_code[:5000] if mod.source_code else ""
                            )
                        else:
                            # diff 모드: 가장 최근 diff만 저장 (AST 분석용)
                            files[mod.filename]["diff"] = (
                                mod.diff[:3000] if mod.diff else ""
                            )

                    files[mod.filename]["added"] += mod.added_lines
                    files[mod.filename]["deleted"] += mod.deleted_lines
                    total_additions += mod.added_lines
                    total_deletions += mod.deleted_lines

        except Exception as e:
            logger.warning(f"PyDriller failed for {repo_url}: {e}")
            return {
                "commits": [],
                "files": [],
                "commit_diffs": [],
                "stats": {
                    "total_commits": 0,
                    "total_additions": 0,
                    "total_deletions": 0,
                    "avg_complexity": 0,
                },
            }

        file_list = list(files.values())
        avg_complexity = (
            sum(f["complexity"] for f in file_list) / len(file_list)
            if file_list else 0
        )

        # diff 기반 정렬: 복잡도 × 변경량 기준
        commit_diffs.sort(
            key=lambda x: x["complexity"] * (x["additions"] + x["deletions"]),
            reverse=True
        )

        return {
            "commits": commits[:100],
            "files": file_list,
            "commit_diffs": commit_diffs[:200],  # 상위 200개 diff
            "stats": {
                "total_commits": len(commits),
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "avg_complexity": round(avg_complexity, 2),
                "analysis_period_years": since_years,
            },
        }

    def select_top_files(
        self,
        files: list[dict],
        jd_tech_stack: list[str],
        max_files: int = 20,
    ) -> list[dict]:
        """복잡도 × JD 매칭 기준 상위 파일 선정"""
        scored = []
        for f in files:
            score = f.get("complexity", 0) * (1 + f.get("methods", 0) * 0.1)
            scored.append((score, f))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:max_files]]

    async def analyze_ast(
        self,
        files: list[dict],
        primary_language: str | None = None,
    ) -> dict:
        """AST 구조 분석 (Python: ast, JS/TS: tree-sitter, fallback)

        Note: diff 모드에서는 source 대신 diff 필드 사용 시도
        """
        functions = []
        classes = []
        imports = []
        patterns = []
        parser_used = "fallback"

        if primary_language and primary_language.lower() == "python":
            parser_used = "ast"
            import ast as ast_mod
            for f in files:
                # diff 모드 호환: source 없으면 diff에서 추출 시도
                source = f.get("source", "") or f.get("diff", "")
                if not source:
                    continue
                try:
                    tree = ast_mod.parse(source)
                    for node in ast_mod.walk(tree):
                        if isinstance(node, ast_mod.FunctionDef):
                            functions.append({
                                "name": node.name,
                                "params": [a.arg for a in node.args.args],
                                "decorators": [
                                    d.id if isinstance(d, ast_mod.Name) else str(d)
                                    for d in node.decorator_list
                                ],
                                "complexity": f.get("complexity", 0),
                            })
                        elif isinstance(node, ast_mod.ClassDef):
                            classes.append({
                                "name": node.name,
                                "bases": [
                                    b.id if isinstance(b, ast_mod.Name) else str(b)
                                    for b in node.bases
                                ],
                                "methods": [
                                    n.name for n in node.body
                                    if isinstance(n, ast_mod.FunctionDef)
                                ],
                            })
                        elif isinstance(node, ast_mod.Import):
                            for alias in node.names:
                                imports.append({"module": alias.name, "alias": alias.asname})
                        elif isinstance(node, ast_mod.ImportFrom):
                            imports.append({"module": node.module, "alias": None})
                except SyntaxError:
                    continue

        elif primary_language and primary_language.lower() in ("javascript", "typescript"):
            try:
                import tree_sitter_javascript as ts_js
                import tree_sitter_typescript as ts_ts
                from tree_sitter import Language, Parser

                if primary_language.lower() == "typescript":
                    language = Language(ts_ts.language_typescript())
                else:
                    language = Language(ts_js.language())

                ts_parser = Parser(language)
                parser_used = "tree_sitter"

                for f in files:
                    # diff 모드 호환: source 없으면 diff에서 추출 시도
                    source = f.get("source", "") or f.get("diff", "")
                    if not source:
                        continue
                    try:
                        tree = ts_parser.parse(source.encode("utf-8"))
                        self._walk_ts_node(tree.root_node, functions, classes, imports, f)
                    except Exception:
                        continue
            except ImportError:
                logger.warning("tree-sitter JS/TS bindings not installed, using fallback")

        return {
            "functions": functions[:50],
            "classes": classes[:30],
            "patterns": patterns,
            "imports": imports[:50],
            "parser_used": parser_used,
        }

    def _walk_ts_node(
        self,
        node,
        functions: list,
        classes: list,
        imports: list,
        file_info: dict,
    ) -> None:
        """tree-sitter 노드를 순회하며 함수, 클래스, import 추출"""
        ntype = node.type

        if ntype in ("function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            params = []
            if params_node:
                for child in params_node.children:
                    if child.type in ("identifier", "required_parameter", "optional_parameter"):
                        params.append(child.text.decode("utf-8"))
            functions.append({
                "name": name_node.text.decode("utf-8") if name_node else "<anonymous>",
                "params": params,
                "decorators": [],
                "complexity": file_info.get("complexity", 0),
            })

        elif ntype == "arrow_function":
            parent = node.parent
            name = "<arrow>"
            if parent and parent.type == "variable_declarator":
                name_node = parent.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
            params_node = node.child_by_field_name("parameters")
            params = []
            if params_node:
                for child in params_node.children:
                    if child.type in ("identifier", "required_parameter", "optional_parameter"):
                        params.append(child.text.decode("utf-8"))
            functions.append({
                "name": name,
                "params": params,
                "decorators": [],
                "complexity": file_info.get("complexity", 0),
            })

        elif ntype == "class_declaration":
            name_node = node.child_by_field_name("name")
            methods = []
            body = node.child_by_field_name("body")
            if body:
                for child in body.children:
                    if child.type == "method_definition":
                        m_name = child.child_by_field_name("name")
                        if m_name:
                            methods.append(m_name.text.decode("utf-8"))
            classes.append({
                "name": name_node.text.decode("utf-8") if name_node else "<anonymous>",
                "bases": [],
                "methods": methods,
            })

        elif ntype == "import_statement":
            source_node = node.child_by_field_name("source")
            imports.append({
                "module": source_node.text.decode("utf-8").strip("'\"") if source_node else "",
                "alias": None,
            })

        for child in node.children:
            self._walk_ts_node(child, functions, classes, imports, file_info)

    def rank_files_for_llm(
        self,
        files: list[dict],
        jd_tech_stack: list[str],
        token_budget: int = 30_000,
    ) -> list[dict]:
        """토큰 예산 내 파일 랭킹"""
        top = self.select_top_files(files, jd_tech_stack, max_files=50)
        selected = []
        total_tokens = 0
        for f in top:
            source = f.get("source", "")
            est_tokens = len(source) // 4  # rough estimate
            if total_tokens + est_tokens > token_budget:
                break
            selected.append(f)
            total_tokens += est_tokens
        return selected

    async def llm_analyze_code(
        self,
        ranked_files: list[dict],
        ast_context: dict | None = None,
        commit_diffs: list[dict] | None = None,
    ) -> dict:
        """LLM으로 코드 의미 분석

        Args:
            ranked_files: 분석 대상 파일 (토큰 예산 내)
            ast_context: AST 분석 결과
            commit_diffs: diff 기반 커밋 데이터 (선택)
        """
        if not ranked_files and not commit_diffs:
            return {"notable_implementations": [], "patterns": [], "quality_assessment": "N/A"}

        from app.services.cached_llm import CachedLLMService
        llm = CachedLLMService()

        context_parts = []

        # diff 기반 컨텍스트 (우선)
        if commit_diffs:
            context_parts.append("## Recent Code Changes (Diffs)\n")
            for d in commit_diffs[:15]:  # 상위 15개 diff
                context_parts.append(
                    f"### {d['file_path']} ({d['commit_hash']})\n"
                    f"Message: {d.get('message', '')}\n"
                    f"```diff\n{d.get('diff', '')[:1500]}\n```"
                )

        # 파일 기반 컨텍스트 (fallback 또는 추가)
        for f in ranked_files[:10]:
            code_content = f.get("source", "") or f.get("diff", "")
            if code_content:
                context_parts.append(f"## {f['filename']}\n```\n{code_content[:3000]}\n```")

        # AST 컨텍스트 추가
        if ast_context:
            context_parts.append(
                f"\n## Code Structure Summary\n"
                f"Functions: {len(ast_context.get('functions', []))}\n"
                f"Classes: {len(ast_context.get('classes', []))}\n"
                f"Parser: {ast_context.get('parser_used', 'N/A')}"
            )

        prompt = (
            "Analyze the following code changes and files to identify:\n"
            "1. Notable implementations (design patterns, algorithms)\n"
            "2. Code quality assessment\n"
            "3. Top question candidates for technical interview\n\n"
            + "\n\n".join(context_parts)
        )

        # Heartbeat before LLM call (long-running operation)
        try:
            from temporalio import activity
            activity.heartbeat("LLM analyze_code starting...")
        except Exception:
            pass

        result = await llm.run(prompt, activity_name="analyze_code")
        if isinstance(result, dict):
            return result
        return {"notable_implementations": [], "patterns": [], "quality_assessment": str(result)}

    # =========================================================================
    # HYBRID 3-Stage Multi-Agent 분석 메서드
    # =========================================================================

    def _build_overview_prompt(
        self,
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

    def _build_deep_analysis_prompt(
        self,
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

    def _build_synthesis_prompt(
        self,
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

    async def llm_overview_analysis(
        self,
        files: list[dict],
        commit_diffs: list[dict],
        ast_summary: dict,
        jd_tech_stack: list[str],
        model: str | None = None,
    ) -> dict:
        """Stage 1: Overview Agent - 전체 diff 분석, 핵심 파일 선별

        Args:
            files: PyDriller로 추출한 파일 목록
            commit_diffs: 커밋별 diff 데이터
            ast_summary: AST 분석 결과
            jd_tech_stack: JD에서 추출한 기술 스택
            model: 사용할 LLM 모델 (기본: GLM)

        Returns:
            OverviewAnalysisResult 형식의 딕셔너리
        """
        model = model or GLM_MODEL
        prompt = self._build_overview_prompt(files, commit_diffs, ast_summary, jd_tech_stack)

        from app.services.cached_llm import CachedLLMService
        llm = CachedLLMService()

        try:
            result = await llm.run(
                prompt=prompt,
                model=model,
                activity_name="code_overview_analysis",
                result_type=OverviewAnalysisResult,
            )
            if isinstance(result, dict):
                return result
            if hasattr(result, "model_dump"):
                return result.model_dump()
            return {"key_files": [], "tech_overview": str(result), "candidate_strengths": []}
        except Exception as e:
            logger.warning(f"Overview analysis failed: {e}")
            return {
                "key_files": [],
                "tech_overview": f"Analysis failed: {e}",
                "candidate_strengths": [],
                "primary_languages": [],
                "frameworks_detected": [],
            }

    async def llm_deep_file_analysis(
        self,
        file_info: dict,
        commit_history: list[dict],
        jd_tech_stack: list[str],
        model: str | None = None,
    ) -> dict:
        """Stage 2: Deep Analysis Agent - 단일 파일 심층 분석

        Args:
            file_info: 분석할 파일 정보 (path, diff 등)
            commit_history: 해당 파일의 커밋 이력
            jd_tech_stack: JD에서 추출한 기술 스택
            model: 사용할 LLM 모델 (기본: GLM)

        Returns:
            DeepAnalysisResult 형식의 딕셔너리
        """
        model = model or GLM_MODEL
        prompt = self._build_deep_analysis_prompt(file_info, commit_history, jd_tech_stack)

        from app.services.cached_llm import CachedLLMService
        llm = CachedLLMService()

        file_path = file_info.get("path", file_info.get("filename", "unknown"))

        try:
            result = await llm.run(
                prompt=prompt,
                model=model,
                activity_name=f"code_deep_analysis_{file_path[:30]}",
                result_type=DeepAnalysisResult,
            )
            if isinstance(result, dict):
                return result
            if hasattr(result, "model_dump"):
                return result.model_dump()
            return {
                "file_path": file_path,
                "patterns_found": [],
                "algorithms_used": [],
                "code_quality_score": 0.5,
                "quality_notes": str(result),
                "question_candidates": [],
                "notable_aspects": [],
                "complexity_assessment": "",
            }
        except Exception as e:
            logger.warning(f"Deep analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "patterns_found": [],
                "algorithms_used": [],
                "code_quality_score": 0.0,
                "quality_notes": f"Analysis failed: {e}",
                "question_candidates": [],
                "notable_aspects": [],
                "complexity_assessment": "Failed",
            }

    async def llm_synthesize_analysis(
        self,
        overview: dict,
        deep_analyses: list[dict],
        repo_info: dict,
        jd_tech_stack: list[str],
        model: str | None = None,
    ) -> dict:
        """Stage 3: Synthesis Agent - 분석 결과 종합

        Args:
            overview: Stage 1 Overview 분석 결과
            deep_analyses: Stage 2 Deep Analysis 결과 리스트
            repo_info: 레포지토리 정보
            jd_tech_stack: JD에서 추출한 기술 스택
            model: 사용할 LLM 모델 (기본: GLM)

        Returns:
            SynthesisAnalysisResult 형식의 딕셔너리
        """
        model = model or GLM_MODEL
        prompt = self._build_synthesis_prompt(overview, deep_analyses, repo_info, jd_tech_stack)

        from app.services.cached_llm import CachedLLMService
        llm = CachedLLMService()

        try:
            result = await llm.run(
                prompt=prompt,
                model=model,
                activity_name="code_synthesis_analysis",
                result_type=SynthesisAnalysisResult,
            )
            if isinstance(result, dict):
                return result
            if hasattr(result, "model_dump"):
                return result.model_dump()
            return {
                "notable_implementations": [],
                "tech_stack": [],
                "patterns": [],
                "algorithms": [],
                "quality_score": 0.0,
                "quality_summary": str(result),
                "candidate_assessment": "",
                "top_interview_questions": [],
            }
        except Exception as e:
            logger.warning(f"Synthesis analysis failed: {e}")
            return {
                "notable_implementations": [],
                "tech_stack": [],
                "patterns": [],
                "algorithms": [],
                "quality_score": 0.0,
                "quality_summary": f"Synthesis failed: {e}",
                "candidate_assessment": "",
                "top_interview_questions": [],
            }
