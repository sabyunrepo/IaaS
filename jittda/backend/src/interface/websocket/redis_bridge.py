"""
Redis PubSub → WebSocket Bridge.

Temporal Worker가 Redis에 발행한 이벤트를 수신하여
WebSocket 클라이언트에 브로드캐스트한다.

단일 리스너 태스크가 모든 채널의 메시지를 수신하고,
채널명에서 job_id를 추출하여 해당 WebSocket에 디스패치한다.
"""
from __future__ import annotations

import asyncio
import json
import logging

import redis.asyncio as aioredis

from interface.websocket.ws_manager import ws_manager

logger = logging.getLogger(__name__)


class RedisPubSubBridge:
    """Redis PubSub 구독 → WebSocket 브로드캐스트.

    단일 PubSub 연결 + 단일 리스너 태스크로 모든 job 채널을 처리한다.
    """

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._listener_task: asyncio.Task | None = None
        self._subscribed_jobs: set[str] = set()
        self._running = False

    @property
    def redis_client(self) -> aioredis.Redis | None:
        """Redis 클라이언트를 반환한다 (health check, rate limiter 용)."""
        return self._redis

    async def start(self) -> None:
        """Redis 연결을 초기화하고 리스너를 시작한다."""
        self._redis = aioredis.from_url(self._redis_url)
        self._pubsub = self._redis.pubsub()
        self._running = True
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("Redis PubSub bridge started")

    async def stop(self) -> None:
        """모든 구독을 해제하고 Redis 연결을 종료한다."""
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
        self._subscribed_jobs.clear()
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.aclose()
        if self._redis:
            await self._redis.aclose()
        logger.info("Redis PubSub bridge stopped")

    async def subscribe(self, job_id: str) -> None:
        """job_id에 대한 Redis 채널 구독을 추가한다."""
        if not self._pubsub or not self._running:
            return

        if job_id in self._subscribed_jobs:
            return

        channel = f"job:{job_id}:events"
        await self._pubsub.subscribe(channel)
        self._subscribed_jobs.add(job_id)
        logger.info("Subscribed to Redis channel: %s", channel)

    async def unsubscribe(self, job_id: str) -> None:
        """job_id에 대한 Redis 채널 구독을 해제한다."""
        if not self._pubsub:
            return

        channel = f"job:{job_id}:events"
        await self._pubsub.unsubscribe(channel)
        self._subscribed_jobs.discard(job_id)
        logger.info("Unsubscribed from Redis channel: %s", channel)

    async def _listen(self) -> None:
        """단일 리스너 — 모든 구독 채널의 메시지를 수신하여 디스패치한다.

        Redis 연결 실패 시 지수 백오프로 재연결을 시도한다.
        구독 채널이 없으면 polling 간격을 두어 CPU spin을 방지한다.
        """
        backoff = 1
        while self._running:
            try:
                if not self._pubsub:
                    break
                # 구독 채널이 없으면 대기 (pubsub.listen()이 즉시 반환되어 CPU spin 방지)
                if not self._subscribed_jobs:
                    await asyncio.sleep(0.1)
                    continue
                async for message in self._pubsub.listen():
                    if not self._running:
                        return
                    if message["type"] != "message":
                        continue

                    # 채널명에서 job_id 추출: "job:{job_id}:events"
                    channel = message.get("channel", b"")
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    parts = channel.split(":")
                    if len(parts) < 3 or parts[0] != "job":
                        continue
                    job_id = parts[1]

                    try:
                        event = json.loads(message["data"])
                    except json.JSONDecodeError as e:
                        logger.warning("Invalid JSON in Redis message: %s", e)
                        continue

                    try:
                        await ws_manager.broadcast(job_id, event)
                    except Exception as e:
                        logger.warning("Failed to broadcast event to %s: %s", job_id, e)

                    # 완료/에러 이벤트 시 자동 구독 해제
                    event_type = event.get("type", "") if isinstance(event, dict) else ""
                    if event_type in ("completed", "error"):
                        await self.unsubscribe(job_id)

                backoff = 1  # 정상 종료 시 백오프 리셋
            except asyncio.CancelledError:
                return
            except Exception as e:
                if not self._running:
                    return
                logger.error("Redis listener error (reconnecting in %ds): %s", backoff, e)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
