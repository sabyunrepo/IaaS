"""
backend/app/services/code_analyzer.py
PyDriller + AST + LLM 기반 코드 분석 파이프라인
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """코드 분석 4-Phase 파이프라인"""

    async def analyze_with_pydriller(
        self,
        repo_url: str,
        job_id: str,
        author: str | None = None,
        since_years: int = 3,
        file_types: list[str] | None = None,
    ) -> dict:
        """PyDriller로 레포 분석 (clone → 커밋 순회 → 메트릭 추출)"""
        logger.info(f"PyDriller analysis: {repo_url} (author={author})")

        # PyDriller import (heavy dependency, lazy load)
        from pydriller import Repository
        from datetime import datetime, timedelta, timezone

        since = datetime.now(timezone.utc) - timedelta(days=since_years * 365)
        commits = []
        files = {}
        total_additions = 0
        total_deletions = 0

        try:
            for commit in Repository(
                repo_url,
                since=since,
                only_authors=[author] if author else None,
                only_modifications_with_file_types=file_types,
            ).traverse_commits():
                commits.append({
                    "hash": commit.hash[:8],
                    "msg": commit.msg[:200],
                    "date": commit.committer_date.isoformat(),
                    "files_changed": len(commit.modified_files),
                })

                for mod in commit.modified_files:
                    if mod.filename not in files:
                        files[mod.filename] = {
                            "filename": mod.filename,
                            "complexity": mod.complexity or 0,
                            "nloc": mod.nloc or 0,
                            "methods": len(mod.methods) if mod.methods else 0,
                            "added": 0,
                            "deleted": 0,
                            "source": mod.source_code[:5000] if mod.source_code else "",
                        }
                    files[mod.filename]["added"] += mod.added_lines
                    files[mod.filename]["deleted"] += mod.deleted_lines
                    total_additions += mod.added_lines
                    total_deletions += mod.deleted_lines
        except Exception as e:
            logger.warning(f"PyDriller failed for {repo_url}: {e}")
            return {"commits": [], "files": [], "stats": {
                "total_commits": 0, "total_additions": 0,
                "total_deletions": 0, "avg_complexity": 0,
            }}

        file_list = list(files.values())
        avg_complexity = (
            sum(f["complexity"] for f in file_list) / len(file_list)
            if file_list else 0
        )

        return {
            "commits": commits[:100],
            "files": file_list,
            "stats": {
                "total_commits": len(commits),
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "avg_complexity": round(avg_complexity, 2),
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
        """AST 구조 분석 (Python: ast, JS/TS: tree-sitter, fallback)"""
        functions = []
        classes = []
        imports = []
        patterns = []
        parser_used = "fallback"

        if primary_language and primary_language.lower() == "python":
            parser_used = "ast"
            import ast as ast_mod
            for f in files:
                source = f.get("source", "")
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
                    source = f.get("source", "")
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
    ) -> dict:
        """LLM으로 코드 의미 분석"""
        if not ranked_files:
            return {"notable_implementations": [], "patterns": [], "quality_assessment": "N/A"}

        from app.services.cached_llm import CachedLLMService
        llm = CachedLLMService()

        context_parts = []
        for f in ranked_files[:10]:
            context_parts.append(f"## {f['filename']}\n```\n{f.get('source', '')[:3000]}\n```")

        prompt = (
            "Analyze the following code files and identify:\n"
            "1. Notable implementations (design patterns, algorithms)\n"
            "2. Code quality assessment\n"
            "3. Top question candidates for technical interview\n\n"
            + "\n\n".join(context_parts)
        )

        result = await llm.run(prompt)
        if isinstance(result, dict):
            return result
        return {"notable_implementations": [], "patterns": [], "quality_assessment": str(result)}
