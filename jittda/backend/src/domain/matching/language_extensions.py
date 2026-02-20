"""
JD 언어 → 파일 확장자 매핑.

jd_languages 기반으로 분석 대상 확장자를 결정하는 순수 도메인 로직.
외부 의존성 없음.
"""
from __future__ import annotations

# 언어명 → (확장자 목록, tree-sitter 언어명)
_LANGUAGE_MAP: dict[str, tuple[list[str], str]] = {
    "python": ([".py"], "python"),
    "javascript": ([".js", ".jsx"], "javascript"),
    "typescript": ([".ts", ".tsx"], "typescript"),
    "java": ([".java"], "java"),
    "go": ([".go"], "go"),
    "rust": ([".rs"], "rust"),
    "kotlin": ([".kt", ".kts"], "kotlin"),
    "swift": ([".swift"], "swift"),
    "ruby": ([".rb"], "ruby"),
    "php": ([".php"], "php"),
    "c": ([".c", ".h"], "c"),
    "cpp": ([".cpp", ".cc", ".cxx", ".hpp", ".hxx"], "cpp"),
    "c++": ([".cpp", ".cc", ".cxx", ".hpp", ".hxx"], "cpp"),
    "csharp": ([".cs"], "c_sharp"),
    "c#": ([".cs"], "c_sharp"),
    "scala": ([".scala"], "scala"),
}

# 확장자 → tree-sitter 언어 역매핑 (런타임에 한 번만 계산)
_EXT_TO_LANGUAGE: dict[str, str] | None = None

# tree-sitter가 현재 지원하는 언어 (파서가 존재하는 것만)
TREE_SITTER_SUPPORTED = frozenset({"python", "javascript", "typescript", "java", "go"})


def _build_ext_map() -> dict[str, str]:
    global _EXT_TO_LANGUAGE
    if _EXT_TO_LANGUAGE is None:
        _EXT_TO_LANGUAGE = {}
        for _lang, (exts, ts_lang) in _LANGUAGE_MAP.items():
            for ext in exts:
                if ext not in _EXT_TO_LANGUAGE:
                    _EXT_TO_LANGUAGE[ext] = ts_lang
    return _EXT_TO_LANGUAGE


def get_extensions_for_languages(jd_languages: list[str]) -> dict[str, str]:
    """JD 언어 목록에서 분석 대상 {확장자: tree-sitter 언어} 매핑을 반환한다.

    Args:
        jd_languages: JD에서 요구하는 언어 목록 (예: ["python", "typescript"])

    Returns:
        {".py": "python", ".ts": "typescript", ".tsx": "typescript"} 형태.
        jd_languages가 비어 있으면 기본 5개 언어 전체를 반환한다 (하위 호환).
    """
    if not jd_languages:
        return _default_ext_map()

    result: dict[str, str] = {}
    for lang in jd_languages:
        lang_lower = lang.lower().strip()
        entry = _LANGUAGE_MAP.get(lang_lower)
        if entry:
            exts, ts_lang = entry
            for ext in exts:
                result[ext] = ts_lang

    return result if result else _default_ext_map()


def _default_ext_map() -> dict[str, str]:
    """기본 5개 언어 확장자 맵 (하위 호환)."""
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
    }


def get_sparse_checkout_patterns(jd_languages: list[str]) -> list[str]:
    """JD 언어 기반 sparse checkout 패턴 목록을 반환한다.

    Args:
        jd_languages: JD에서 요구하는 언어 목록.

    Returns:
        ["*.py", "*.ts", "*.tsx", ...] 형태의 glob 패턴.
        빈 목록이면 sparse checkout을 적용하지 않는다는 의미.
    """
    if not jd_languages:
        return []

    patterns: set[str] = set()
    for lang in jd_languages:
        lang_lower = lang.lower().strip()
        entry = _LANGUAGE_MAP.get(lang_lower)
        if entry:
            for ext in entry[0]:
                patterns.add(f"*{ext}")

    # 공통 디렉토리도 포함 (패키지 설정, 설정 파일 등)
    patterns.update([
        "*.json",
        "*.yaml",
        "*.yml",
        "*.toml",
        "*.md",
        "*.txt",
    ])

    return sorted(patterns)


def ext_to_tree_sitter_language(ext: str) -> str | None:
    """확장자에서 tree-sitter 언어명을 반환한다.

    Returns:
        tree-sitter 언어명. 미지원 확장자면 None.
    """
    ext_map = _build_ext_map()
    return ext_map.get(ext)


def is_tree_sitter_supported(ts_language: str) -> bool:
    """해당 tree-sitter 언어가 현재 파서에서 지원되는지 확인한다."""
    return ts_language in TREE_SITTER_SUPPORTED
