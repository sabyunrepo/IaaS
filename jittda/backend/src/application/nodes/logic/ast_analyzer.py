"""
ASTAnalyzer Worker (W6) — Tree-sitter AST 구조 분석.

소스 파일을 파싱하여 함수/클래스 구조, import 의존성, 코드 패턴을 추출한다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from application.states.logic_state import LogicState
from infrastructure.analysis.tree_sitter_adapter import TreeSitterAdapter


async def ast_analyzer_worker(state: LogicState) -> dict[str, Any]:
    """Tree-sitter로 AST 분석을 수행한다."""
    repo_paths = state.get("repo_local_paths", [])
    cleaned_diffs = state.get("cleaned_diffs", [])

    adapter = TreeSitterAdapter()
    results = []

    # cleaned_diffs 기반 분석 (이미 정제된 코드)
    for diff in cleaned_diffs:
        language = diff.get("language", "")
        if language not in adapter.SUPPORTED_LANGUAGES:
            continue

        bodies = diff.get("function_bodies", [])
        code = "\n\n".join(bodies)
        if not code.strip():
            continue

        try:
            tree = adapter.parse_code(code, language)
            root = tree.root_node

            functions = adapter.extract_functions(root, language)
            classes = adapter.extract_classes(root, language)
            imports = adapter.extract_imports(root, language)

            results.append({
                "file_path": diff.get("file_path", ""),
                "language": language,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "total_functions": len(functions),
                "total_classes": len(classes),
                "total_imports": len(imports),
            })
        except Exception:
            continue

    # 리포 디렉토리 기반 추가 분석
    for repo_path_str in repo_paths:
        repo_path = Path(repo_path_str)
        if not repo_path.exists():
            continue

        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
        }

        for ext, lang in ext_map.items():
            for src_file in list(repo_path.rglob(f"*{ext}"))[:20]:
                if ".git" in str(src_file) or "node_modules" in str(src_file):
                    continue
                # 이미 cleaned_diffs에서 분석한 파일은 스킵
                rel = str(src_file.relative_to(repo_path))
                if any(d.get("file_path", "").endswith(rel) for d in cleaned_diffs):
                    continue
                try:
                    code = src_file.read_text(errors="replace")[:50000]
                    tree = adapter.parse_code(code, lang)
                    root = tree.root_node
                    functions = adapter.extract_functions(root, lang)
                    if functions:
                        results.append({
                            "file_path": rel,
                            "language": lang,
                            "functions": functions,
                            "classes": adapter.extract_classes(root, lang),
                            "imports": adapter.extract_imports(root, lang),
                            "total_functions": len(functions),
                            "total_classes": len(adapter.extract_classes(root, lang)),
                            "total_imports": len(adapter.extract_imports(root, lang)),
                        })
                except Exception:
                    continue

    return {"ast_analysis": results}
