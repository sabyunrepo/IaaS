"""Interface 테스트 공유 fixture.

Python 3.14에서 langfuse/pydantic_v1 호환 문제로 인해
infrastructure.observability.metrics 임포트 시 ConfigError가 발생한다.
log_requests 미들웨어의 except ImportError로는 잡히지 않으므로
모듈을 미리 mock하여 모든 interface 테스트에서 사용한다.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _mock_observability():
    """langfuse/pydantic_v1 호환 이슈 우회 — observability 모듈 mock."""
    mock_metrics = MagicMock()
    from unittest.mock import patch

    with patch.dict(sys.modules, {
        "infrastructure.observability": MagicMock(metrics=mock_metrics),
        "infrastructure.observability.metrics": mock_metrics,
    }):
        yield
