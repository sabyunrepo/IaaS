"""
backend/app/workflows/activities/send_email_notification.py
Job 완료/실패 시 이메일 알림 발송 Activity
"""
import logging
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from temporalio import activity
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.database import JobDB, UserDB
from app.workflows.activities.email_template import EMAIL_TEXTS, render_email_template

logger = logging.getLogger(__name__)


def _send_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
    """SMTP로 이메일 발송. SSL(465) / STARTTLS(587) 자동 분기."""
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    security = (settings.SMTP_SECURITY or "").upper()
    if security == "SSL":
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

    return True


@activity.defn
async def send_email_notification(job_id: str) -> dict:
    """Job 완료/실패 시 이메일 알림 발송.

    Args:
        job_id: Job UUID 문자열

    Returns:
        {"status": "sent" | "skipped" | "failed", "reason": str}
    """
    async with async_session() as session:
        # Job 조회
        result = await session.execute(
            select(JobDB).where(JobDB.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job:
            return {"status": "skipped", "reason": "job_not_found"}

        # User 조회
        result = await session.execute(
            select(UserDB).where(UserDB.id == job.user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return {"status": "skipped", "reason": "user_not_found"}

    # 알림 설정 확인
    if user.email_notification_enabled is not True:
        return {"status": "skipped", "reason": "notification_disabled"}

    # JD에서 후보자/포지션 정보 추출
    input_data = job.input_data or {}
    candidate_info = input_data.get("jd_text", "")[:80]

    # output_language 추출
    output_language = input_data.get("language_config", {}).get("output_language", "ko")

    if not candidate_info:
        candidate_info = "면접 스크립트" if output_language == "ko" else "Interview Script"

    user_name = user.name or user.email.split("@")[0]

    # 이메일 제목 (언어별)
    texts = EMAIL_TEXTS.get(output_language, EMAIL_TEXTS["en"])
    if job.status == "completed":
        subject = texts["completed_subject"]
    else:
        subject = texts["failed_subject"]

    # HTML 렌더링
    html = render_email_template(
        status=job.status,
        user_name=user_name,
        job_id=job_id,
        candidate_info=candidate_info,
        frontend_url=settings.FRONTEND_URL,
        lang=output_language,
    )

    # 발송
    try:
        sent = _send_smtp_email(user.email, subject, html)
        if sent:
            logger.info(f"Email notification sent to {user.email} for job {job_id}")
            return {"status": "sent", "reason": "ok"}
        else:
            return {"status": "skipped", "reason": "smtp_not_configured"}
    except Exception as e:
        logger.error(f"Email send failed for job {job_id}: {e}")
        return {"status": "failed", "reason": str(e)}
