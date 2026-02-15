"""update_job_status Activity 단위 테스트"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_update_job_status_activity_updates_db():
    """DB에서 Job을 찾아 상태를 업데이트하는지 확인"""
    from app.workflows.activities.update_job_status import update_job_status_activity

    mock_job = MagicMock()
    mock_job.status = "pending"
    mock_job.updated_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_job

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workflows.activities.update_job_status.async_session", return_value=mock_session):
        await update_job_status_activity(str(uuid.uuid4()), "enriching")

    assert mock_job.status == "enriching"
    assert mock_job.updated_at is not None
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_job_status_activity_job_not_found():
    """Job이 없으면 조용히 넘어감"""
    from app.workflows.activities.update_job_status import update_job_status_activity

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workflows.activities.update_job_status.async_session", return_value=mock_session):
        await update_job_status_activity(str(uuid.uuid4()), "enriching")

    mock_session.commit.assert_not_awaited()
