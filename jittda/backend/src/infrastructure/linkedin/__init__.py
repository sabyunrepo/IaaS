"""LinkedIn infrastructure 어댑터."""

__all__: list[str] = []

try:
    from infrastructure.linkedin.brightdata_client import BrightDataClient
    __all__ += ["BrightDataClient"]
except ImportError:
    pass
