"""GitHub infrastructure 어댑터."""

__all__: list[str] = []

try:
    from infrastructure.github.github_client import GitHubClient
    __all__ += ["GitHubClient"]
except ImportError:
    pass
