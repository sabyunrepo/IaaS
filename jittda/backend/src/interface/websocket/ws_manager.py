"""
WebSocket Manager — 실시간 분석 진행률 스트리밍.

Job별 WebSocket 연결을 관리하고, 그래프 실행 이벤트를 클라이언트에 브로드캐스트한다.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """Job별 WebSocket 연결 관리자."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        """WebSocket 연결을 등록한다."""
        await websocket.accept()
        self._connections.setdefault(job_id, []).append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        """WebSocket 연결을 제거한다."""
        if job_id in self._connections:
            self._connections[job_id] = [
                ws for ws in self._connections[job_id] if ws != websocket
            ]
            if not self._connections[job_id]:
                del self._connections[job_id]

    def has_connections(self, job_id: str) -> bool:
        """Job에 연결된 WebSocket이 있는지 확인한다."""
        return bool(self._connections.get(job_id))

    async def broadcast(self, job_id: str, event: dict[str, Any]) -> None:
        """Job에 연결된 모든 WebSocket에 이벤트를 전송한다."""
        if job_id not in self._connections:
            return

        message = json.dumps(event, default=str)
        disconnected = []

        for ws in self._connections[job_id]:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)

        # 끊어진 연결 정리
        for ws in disconnected:
            self.disconnect(job_id, ws)


# 싱글톤 인스턴스
ws_manager = WebSocketManager()
