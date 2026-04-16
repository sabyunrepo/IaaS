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

    def test_initial_subscribed_jobs_empty(self) -> None:
        """초기 상태에서 구독된 Job이 없다."""
        from interface.websocket.redis_bridge import RedisPubSubBridge

        bridge = RedisPubSubBridge("redis://localhost:6379")
        assert len(bridge._subscribed_jobs) == 0


class TestRedisBridgeListenGuard:
    """_listen() CPU spin 방지 가드 테스트."""

    @pytest.mark.asyncio
    async def test_listen_skips_when_no_subscriptions(self) -> None:
        """구독 채널이 없으면 _listen이 sleep 후 continue한다."""
        import asyncio

        from interface.websocket.redis_bridge import RedisPubSubBridge

        bridge = RedisPubSubBridge("redis://localhost:6379")
        bridge._running = True
        bridge._pubsub = MagicMock()

        # _listen을 짧게 실행 후 취소하여 spin하지 않는지 확인
        iterations = 0
        original_sleep = asyncio.sleep

        async def counting_sleep(duration):
            nonlocal iterations
            iterations += 1
            if iterations >= 3:
                bridge._running = False
            await original_sleep(0)  # 즉시 반환

        with patch("asyncio.sleep", side_effect=counting_sleep):
            await bridge._listen()

        # 3번 sleep 후 종료 (spin이 아닌 sleep 기반)
        assert iterations >= 3


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
