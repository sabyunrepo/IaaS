"""
Redis PubSub Bridge 테스트.

WebSocket Manager와 Redis PubSub 간 이벤트 전달을 검증한다.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRedisBridgeInit:
    """RedisPubSubBridge 초기화 테스트."""

    def test_bridge_creation(self) -> None:
        from interface.websocket.redis_bridge import RedisPubSubBridge

        bridge = RedisPubSubBridge("redis://localhost:6379")
        assert bridge._redis_url == "redis://localhost:6379"
        assert bridge._redis is None
        assert bridge._running is False


class TestWsManagerHasConnections:
    """WebSocketManager.has_connections() 테스트."""

    def test_no_connections(self) -> None:
        from interface.websocket.ws_manager import WebSocketManager

        mgr = WebSocketManager()
        assert mgr.has_connections("job-1") is False

    @pytest.mark.asyncio
    async def test_with_connection(self) -> None:
        from interface.websocket.ws_manager import WebSocketManager

        mgr = WebSocketManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        await mgr.connect("job-1", mock_ws)
        assert mgr.has_connections("job-1") is True

    @pytest.mark.asyncio
    async def test_after_disconnect(self) -> None:
        from interface.websocket.ws_manager import WebSocketManager

        mgr = WebSocketManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        await mgr.connect("job-1", mock_ws)
        mgr.disconnect("job-1", mock_ws)
        assert mgr.has_connections("job-1") is False
