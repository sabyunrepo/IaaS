"""Infrastructure Analysis 어댑터 — 외부 분석 도구 래퍼."""

__all__: list[str] = []

# SonarQube (httpx만 필요)
try:
    from infrastructure.analysis.sonarqube_adapter import QualityReport, SonarQubeAdapter
    __all__ += ["SonarQubeAdapter", "QualityReport"]
except ImportError:
    pass

# Tree-sitter (tree-sitter 0.25.x 필요)
try:
    from infrastructure.analysis.tree_sitter_adapter import TreeSitterAdapter
    __all__ += ["TreeSitterAdapter"]
except ImportError:
    pass

# Datasketch (datasketch 필요)
try:
    from infrastructure.analysis.datasketch_adapter import DatasketchAdapter, SimilarityResult
    __all__ += ["DatasketchAdapter", "SimilarityResult"]
except ImportError:
    pass

# Radon/Lizard (radon, lizard 필요)
try:
    from infrastructure.analysis.complexity_adapter import LizardAdapter, RadonAdapter
    __all__ += ["RadonAdapter", "LizardAdapter"]
except ImportError:
    pass
