"""이메일 알림 Activity 단위 테스트"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_send_email_skipped_when_disabled():
    """알림 비활성화 시 이메일 전송 안 함"""
    from app.workflows.activities.send_email_notification import send_email_notification

    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.email_notification_enabled = False

    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.status = "completed"
    mock_job.input_data = {"jd_text": "Test JD"}

    mock_result_job = MagicMock()
    mock_result_job.scalar_one_or_none.return_value = mock_job
    mock_result_user = MagicMock()
    mock_result_user.scalar_one_or_none.return_value = mock_user

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=[mock_result_job, mock_result_user])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workflows.activities.send_email_notification.async_session", return_value=mock_session):
        result = await send_email_notification(str(uuid.uuid4()))

    assert result["status"] == "skipped"


@pytest.mark.asyncio
async def test_send_email_skipped_when_null():
    """알림 미설정(NULL) 시 이메일 전송 안 함"""
    from app.workflows.activities.send_email_notification import send_email_notification

    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.email_notification_enabled = None

    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.status = "completed"
    mock_job.input_data = {"jd_text": "Test JD"}

    mock_result_job = MagicMock()
    mock_result_job.scalar_one_or_none.return_value = mock_job
    mock_result_user = MagicMock()
    mock_result_user.scalar_one_or_none.return_value = mock_user

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=[mock_result_job, mock_result_user])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workflows.activities.send_email_notification.async_session", return_value=mock_session):
        result = await send_email_notification(str(uuid.uuid4()))

    assert result["status"] == "skipped"


@pytest.mark.asyncio
async def test_send_email_sent_when_enabled():
    """알림 활성화 시 이메일 전송"""
    from app.workflows.activities.send_email_notification import send_email_notification

    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.email_notification_enabled = True
    mock_user.name = "테스트 유저"

    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.status = "completed"
    mock_job.input_data = {"jd_text": "Frontend Developer"}
    mock_job.id = uuid.uuid4()

    mock_result_job = MagicMock()
    mock_result_job.scalar_one_or_none.return_value = mock_job
    mock_result_user = MagicMock()
    mock_result_user.scalar_one_or_none.return_value = mock_user

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=[mock_result_job, mock_result_user])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workflows.activities.send_email_notification.async_session", return_value=mock_session), \
         patch("app.workflows.activities.send_email_notification._send_smtp_email", return_value=True) as mock_smtp:
        result = await send_email_notification(str(mock_job.id))

    assert result["status"] == "sent"
    mock_smtp.assert_called_once()


def test_email_template_completed():
    """완료 템플릿 렌더링 확인"""
    from app.workflows.activities.email_template import render_email_template

    html = render_email_template(
        status="completed",
        user_name="홍길동",
        job_id="abc-123",
        candidate_info="Frontend Developer",
        frontend_url="https://dev.jittda.com",
    )
    assert "홍길동" in html
    assert "abc-123" in html
    assert "https://dev.jittda.com" in html
    assert "결과 확인하기" in html


def test_email_template_failed():
    """실패 템플릿 렌더링 확인"""
    from app.workflows.activities.email_template import render_email_template

    html = render_email_template(
        status="failed",
        user_name="홍길동",
        job_id="abc-123",
        candidate_info="Backend Developer",
        frontend_url="https://dev.jittda.com",
    )
    assert "문제가 발생" in html
    assert "다시 시도" in html


def test_email_template_completed_english():
    """영어 완료 템플릿 렌더링 확인"""
    from app.workflows.activities.email_template import render_email_template

    html = render_email_template(
        status="completed",
        user_name="John",
        job_id="abc-123",
        candidate_info="Frontend Developer",
        frontend_url="https://dev.jittda.com",
        lang="en",
    )
    assert "Hello, John." in html
    assert "View Results" in html
    assert "Interview Script Ready" in html
    assert 'lang="en"' in html


def test_email_template_failed_english():
    """영어 실패 템플릿 렌더링 확인"""
    from app.workflows.activities.email_template import render_email_template

    html = render_email_template(
        status="failed",
        user_name="John",
        job_id="abc-123",
        candidate_info="Backend Developer",
        frontend_url="https://dev.jittda.com",
        lang="en",
    )
    assert "Analysis Issue Detected" in html
    assert "Try Again" in html


def test_email_template_unsupported_lang_falls_back_to_english():
    """미지원 언어는 영어로 폴백"""
    from app.workflows.activities.email_template import render_email_template

    html = render_email_template(
        status="completed",
        user_name="Tanaka",
        job_id="abc-123",
        candidate_info="Backend Developer",
        frontend_url="https://dev.jittda.com",
        lang="ja",
    )
    assert "Hello, Tanaka." in html
    assert "View Results" in html


@pytest.mark.asyncio
async def test_send_email_english_subject_and_template():
    """영어 output_language 시 영어 제목과 템플릿 사용"""
    from app.workflows.activities.send_email_notification import send_email_notification

    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.email_notification_enabled = True
    mock_user.name = "John"

    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.status = "completed"
    mock_job.input_data = {
        "jd_text": "Frontend Developer",
        "language_config": {"output_language": "en"},
    }
    mock_job.id = uuid.uuid4()

    mock_result_job = MagicMock()
    mock_result_job.scalar_one_or_none.return_value = mock_job
    mock_result_user = MagicMock()
    mock_result_user.scalar_one_or_none.return_value = mock_user

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=[mock_result_job, mock_result_user])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workflows.activities.send_email_notification.async_session", return_value=mock_session), \
         patch("app.workflows.activities.send_email_notification._send_smtp_email", return_value=True) as mock_smtp:
        result = await send_email_notification(str(mock_job.id))

    assert result["status"] == "sent"
    call_args = mock_smtp.call_args
    subject = call_args[0][1]
    html_body = call_args[0][2]
    assert subject == "[Jittda] Your Interview Script is Ready"
    assert "Hello, John." in html_body
    assert "View Results" in html_body
