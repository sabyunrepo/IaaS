"""
backend/app/services/code_analyzer.py
PyDriller + AST + LLM 기반 코드 분석 파이프라인

4-Channel GitHub Analysis의 Channel A (본인 레포 분석) 담당
- diff 기반 코드 추출 (토큰 효율적)
- 분석 기간: GITHUB_ANALYSIS_YEARS 환경변수 (기본 1년)
- HYBRID 3-Stage Multi-Agent 분석 지원 (Kimi K2.5 비용 최적화)
- shallow clone 소스 fallback: PyDriller diff가 0일 때 clone 소스 기반 분석
"""
import logging
import os
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.analysis import (
    OverviewAnalysisResult,
    DeepAnalysisResult,
    SynthesisAnalysisResult,
)
from app.services.llm_config import KIMI_CODER_MODEL
from app.services.ast_analyzer import analyze_ast as _analyze_ast_standalone
from app.services.ast_analyzer import analyze_directory as _analyze_directory
from app.services.chunk_scorer import rank_chunks_by_relevance
from app.services.code_analysis_prompts import (
    build_overview_prompt,
    build_deep_analysis_prompt,
    build_synthesis_prompt,
)

logger = logging.getLogger(__name__)


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

        # Monthly contribution tracking (last 12 months)
        from collections import defaultdict
        monthly_counts = defaultdict(int)

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

                # Track monthly contributions
                month_key = commit.committer_date.strftime("%Y-%m")
                monthly_counts[month_key] += 1

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

        # diff 기반 정렬: 복잡도 × 변경량 기준 (secondary key로 안정 정렬 보장)
        commit_diffs.sort(
            key=lambda x: (
                x["complexity"] * (x["additions"] + x["deletions"]),
                x.get("file_path", ""),
            ),
            reverse=True,
        )

        # Build monthly_contributions array (last 12 months, oldest → newest)
        now = datetime.now(timezone.utc)
        monthly_contributions = []
        for i in range(11, -1, -1):
            # Calculate month offset
            target_month = now.month - i
            target_year = now.year
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            month_key = f"{target_year}-{target_month:02d}"
            monthly_contributions.append(monthly_counts.get(month_key, 0))

        return {
            "commits": commits[:100],
            "files": file_list,
            "commit_diffs": commit_diffs[:200],  # 상위 200개 diff
            "monthly_contributions": monthly_contributions,
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
        scored.sort(key=lambda x: (x[0], x[1].get("filename", "")), reverse=True)
        return [f for _, f in scored[:max_files]]

    def read_source_files_from_clone(
        self,
        clone_dir: str,
        file_types: list[str] | None = None,
        max_files: int = 30,
        token_budget: int = 50_000,
    ) -> list[dict]:
        """shallow clone 디렉토리에서 소스 파일 읽기 (PyDriller fallback)

        PyDriller diff가 0개일 때 clone 소스 기반 분석용.
        PyDriller files 형식과 동일한 구조로 반환.

        Args:
            clone_dir: shallow clone 디렉토리 경로
            file_types: 분석 대상 파일 확장자 (예: [".py", ".js"])
            max_files: 최대 파일 수
            token_budget: 총 토큰 예산 (char//4 추정)

        Returns:
            [{filename, source, complexity, nloc, methods, added, deleted}]
        """
        if not file_types:
            file_types = [".py"]

        ext_set = set(file_types)
        candidates: list[tuple[int, str, str]] = []  # (file_size, rel_path, abs_path)

        for root, dirs, filenames in os.walk(clone_dir):
            # .git, __pycache__, node_modules 등 제외
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                if ext not in ext_set:
                    continue
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, clone_dir)
                try:
                    file_size = os.path.getsize(abs_path)
                except OSError:
                    continue
                # 빈 파일이나 너무 큰 파일(>100KB) 제외
                if file_size == 0 or file_size > 100_000:
                    continue
                candidates.append((file_size, rel_path, abs_path))

        # 파일 크기 역순 정렬 (큰 파일 = 더 많은 로직)
        candidates.sort(key=lambda x: x[0], reverse=True)

        files: list[dict] = []
        total_tokens = 0
        for file_size, rel_path, abs_path in candidates[:max_files * 2]:
            est_tokens = file_size // 4
            if total_tokens + est_tokens > token_budget:
                break
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as fh:
                    source = fh.read()
            except OSError:
                continue
            nloc = sum(1 for line in source.splitlines() if line.strip())
            files.append({
                "filename": rel_path,
                "source": source[:5000],  # 토큰 절약: 상위 5000자
                "complexity": 0,
                "nloc": nloc,
                "methods": 0,
                "added": nloc,
                "deleted": 0,
            })
            total_tokens += est_tokens
            if len(files) >= max_files:
                break

        logger.info(f"Read {len(files)} source files from clone ({total_tokens} est tokens)")
        return files

    async def analyze_ast(
        self,
        files: list[dict],
        primary_language: str | None = None,
    ) -> dict:
        """AST 구조 분석 — ast_analyzer 모듈에 위임"""
        return await _analyze_ast_standalone(files, primary_language)

    def rank_files_for_llm(
        self,
        files: list[dict],
        jd_tech_stack: list[str],
        token_budget: int = 30_000,
    ) -> list[dict]:
        """토큰 예산 내 파일 랭킹 (레거시 — USE_AST_PIPELINE=False 시 사용)"""
        top = self.select_top_files(files, jd_tech_stack, max_files=50)
        selected = []
        total_tokens = 0
        for f in top:
            content = f.get("source", "") or f.get("diff", "")
            est_tokens = len(content) // 4  # rough estimate
            if total_tokens + est_tokens > token_budget:
                break
            selected.append(f)
            total_tokens += est_tokens
        return selected

    def select_top_chunks(
        self,
        chunks: list[dict],
        jd_tech_stack: list[str],
        token_budget: int = 50_000,
        contributor_ratio: float | None = None,
    ) -> list[dict]:
        """JD-Aware 청크 선별 (JIT-22 rank_chunks_by_relevance 위임)"""
        return rank_chunks_by_relevance(
            chunks=chunks,
            jd_tech_stack=jd_tech_stack,
            token_budget=token_budget,
            contributor_ratio=contributor_ratio,
        )

    def analyze_directory(
        self,
        clone_dir: str,
        file_types: list[str] | None = None,
        max_files: int = 50,
    ) -> list[dict]:
        """clone_dir에서 AST 파싱 + 청크 메타데이터 추출 (JIT-21)"""
        return _analyze_directory(
            clone_dir=clone_dir,
            file_types=file_types,
            max_files=max_files,
        )

    @staticmethod
    def calculate_dynamic_token_budget(total_nloc: int) -> int:
        """레포 크기에 비례한 동적 토큰 예산 (20K~50K)"""
        budget = max(20_000, min(50_000, total_nloc * 5))
        return budget

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
        empty_result = {"notable_implementations": [], "patterns": [], "tech_stack": [], "quality_assessment": "N/A"}
        if not ranked_files and not commit_diffs:
            return empty_result

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
            ast_funcs = ast_context.get("functions", [])
            ast_classes = ast_context.get("classes", [])
            ast_detail = f"Functions: {len(ast_funcs)}, Classes: {len(ast_classes)}, Parser: {ast_context.get('parser_used', 'N/A')}"
            if ast_funcs:
                func_names = ", ".join(f.get("name", "") for f in ast_funcs[:20])
                ast_detail += f"\nKey functions: {func_names}"
            if ast_classes:
                class_names = ", ".join(c.get("name", "") for c in ast_classes[:10])
                ast_detail += f"\nKey classes: {class_names}"
            context_parts.append(f"\n## Code Structure Summary\n{ast_detail}")

        code_context = "\n\n".join(context_parts)

        prompt = f"""Analyze the following code changes and files for a technical interview preparation.

{code_context}

Based on the code above, respond ONLY with a valid JSON object (no markdown, no extra text):
{{
    "notable_implementations": [
        {{
            "title": "Brief title of the implementation",
            "description": "What it does and why it's notable",
            "file_path": "path/to/file",
            "code_snippet": "The most relevant 2-10 lines of actual code from this implementation",
            "why_notable": "Why this is interesting for interview",
            "question_potential": 0.8
        }}
    ],
    "patterns": ["Design patterns found, e.g. Singleton, Repository, Factory"],
    "tech_stack": ["Technologies and frameworks detected"],
    "quality_assessment": "Brief overall code quality assessment",
    "quality_score": 0.7,
    "candidate_strengths": ["Strength 1", "Strength 2"],
    "top_interview_questions": ["Question 1", "Question 2"]
}}"""

        # Heartbeat before LLM call (long-running operation)
        try:
            from temporalio import activity
            activity.heartbeat("LLM analyze_code starting...")
        except Exception:
            pass

        # Retry up to 2 times on empty/unparseable response
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                result = await llm.run(prompt, activity_name="analyze_code")
                if isinstance(result, dict) and result:
                    return result
                # Non-dict or empty dict — retry if attempts remain
                if attempt < max_retries:
                    logger.warning(
                        f"llm_analyze_code: attempt {attempt + 1} returned non-dict "
                        f"(type={type(result).__name__}, preview={str(result)[:200]}), retrying..."
                    )
                    try:
                        from temporalio import activity
                        activity.heartbeat(f"LLM analyze_code retry {attempt + 2}...")
                    except Exception:
                        pass
                    continue
                # Final attempt — use fallback
                logger.warning(
                    f"llm_analyze_code: all {max_retries + 1} attempts returned non-dict "
                    f"(type={type(result).__name__}, preview={str(result)[:200]})"
                )
                return {**empty_result, "quality_assessment": str(result)[:500] if result else "N/A"}
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"llm_analyze_code: attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                logger.warning(f"llm_analyze_code: all attempts failed: {e}")
                return {**empty_result, "quality_assessment": f"Analysis failed: {e}"}

        return empty_result

    # =========================================================================
    # HYBRID 3-Stage Multi-Agent 분석 메서드
    # — 프롬프트 빌더는 code_analysis_prompts 모듈로 분리됨
    # =========================================================================

    async def llm_overview_analysis(
        self,
        files: list[dict],
        commit_diffs: list[dict],
        ast_summary: dict,
        jd_tech_stack: list[str],
        model: str | None = None,
        ranked_chunks: list[dict] | None = None,
    ) -> dict:
        """Stage 1: Overview Agent - 전체 diff 분석, 핵심 파일 선별

        Args:
            files: PyDriller로 추출한 파일 목록
            commit_diffs: 커밋별 diff 데이터
            ast_summary: AST 분석 결과
            jd_tech_stack: JD에서 추출한 기술 스택
            model: 사용할 LLM 모델 (기본: GLM)
            ranked_chunks: JD-Aware 랭킹된 청크 리스트 (JIT-24, optional)

        Returns:
            OverviewAnalysisResult 형식의 딕셔너리
        """
        model = model or KIMI_CODER_MODEL
        prompt = build_overview_prompt(files, commit_diffs, ast_summary, jd_tech_stack, ranked_chunks)

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
        model = model or KIMI_CODER_MODEL
        prompt = build_deep_analysis_prompt(file_info, commit_history, jd_tech_stack)

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
        model = model or KIMI_CODER_MODEL
        prompt = build_synthesis_prompt(overview, deep_analyses, repo_info, jd_tech_stack)

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
