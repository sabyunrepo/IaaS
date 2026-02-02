"""
backend/app/core/temporal.py
Temporal 클라이언트 팩토리
"""
from temporalio.client import Client, TLSConfig

from .config import settings

_client: Client | None = None


async def get_temporal_client() -> Client:
    """Temporal 클라이언트 싱글톤"""
    global _client
    if _client is not None:
        return _client

    tls_config = None
    if settings.TEMPORAL_TLS_CERT and settings.TEMPORAL_TLS_KEY:
        tls_config = TLSConfig(
            client_cert=settings.TEMPORAL_TLS_CERT.encode(),
            client_private_key=settings.TEMPORAL_TLS_KEY.encode(),
        )

    target_host = settings.TEMPORAL_HOST
    namespace = settings.TEMPORAL_NAMESPACE

    if settings.TEMPORAL_CLOUD_NAMESPACE:
        namespace = settings.TEMPORAL_CLOUD_NAMESPACE

    _client = await Client.connect(
        target_host,
        namespace=namespace,
        tls=tls_config or False,
    )
    return _client
