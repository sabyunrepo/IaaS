# 이메일 알림 + 작업 상태 DB 동기화 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Job 완료 시 이메일 알림 발송 + 작업 리스트에서 실제 진행 상태 반영

**Architecture:** Temporal Activity 기반 — (1) `_update_status()` 호출 시 DB 즉시 동기화 Activity 추가, (2) `persist_result` 후 이메일 발송 Activity 추가. 프론트엔드에서 계정 레벨 알림 설정 모달 + 사용자 API 엔드포인트.

**Tech Stack:** Python smtplib (Gmail SMTP), Temporal Activity, FastAPI, SQLAlchemy, React 19, Tailwind CSS

**Linear:** JIT-126 (상태 동기화), JIT-127 (이메일 알림)

---

## Task 1: DB 마이그레이션 — `email_notification_enabled` 컬럼 추가

**Files:**
- Create: `backend/alembic/versions/004_add_email_notification.py`
- Modify: `backend/app/models/database.py:21-36`

**Step 1: Alembic 마이그레이션 파일 생성**

```python
# backend/alembic/versions/004_add_email_notification.py
"""Add email_notification_enabled to users table.

Revision ID: 004_email_notification
Revises: 003_analysis_logs
Create Date: 2026-02-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_email_notification"
down_revision: Union[str, None] = "003_analysis_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("email_notification_enabled", sa.Boolean(), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "email_notification_enabled")
```

**Step 2: UserDB 모델에 컬럼 추가**

`backend/app/models/database.py` — `UserDB` 클래스에 추가:

```python
email_notification_enabled = Column(Boolean, nullable=True)  # NULL=미설정, True=켜짐, False=꺼짐
```

`is_active` 컬럼 바로 아래(line 31 이후)에 추가.

**Step 3: 마이그레이션 실행**

Run: `cd /Users/sabyun/goinfre/IaaS/backend && docker compose exec backend alembic upgrade head`

또는 DB 직접:
```sql
ALTER TABLE users ADD COLUMN email_notification_enabled BOOLEAN DEFAULT NULL;
```

**Step 4: 커밋**

```bash
git add backend/alembic/versions/004_add_email_notification.py backend/app/models/database.py
git commit -m "feat: JIT-126 UserDB에 email_notification_enabled 컬럼 추가"
```

---

## Task 2: SMTP 설정 — `config.py`에 환경변수 추가

**Files:**
- Modify: `backend/app/core/config.py:80-94`

**Step 1: Settings 클래스에 SMTP 필드 추가**

`backend/app/core/config.py` — `# OAuth + JWT` 섹션 바로 위에 추가:

```python
    # Email Notification (Gmail SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "Jittda"
```

**Step 2: 커밋**

```bash
git add backend/app/core/config.py
git commit -m "feat: JIT-127 SMTP 환경변수 설정 추가"
```

---

## Task 3: `update_job_status` Activity 생성 (JIT-126 핵심)

**Files:**
- Create: `backend/app/workflows/activities/update_job_status.py`
- Test: `backend/tests/test_update_job_status.py`

**Step 1: 테스트 작성**

```python
# backend/tests/test_update_job_status.py
"""update_job_status Activity 단위 테스트"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


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
        # 에러 없이 정상 종료
        await update_job_status_activity(str(uuid.uuid4()), "enriching")

    mock_session.commit.assert_not_awaited()
```

**Step 2: 테스트 실패 확인**

Run: `cd /Users/sabyun/goinfre/IaaS/backend && .venv/bin/python -m pytest tests/test_update_job_status.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.workflows.activities.update_job_status'`

**Step 3: Activity 구현**

```python
# backend/app/workflows/activities/update_job_status.py
"""
backend/app/workflows/activities/update_job_status.py
워크플로우 Phase 변경 시 DB 상태를 즉시 동기화하는 Activity
"""
import logging
import uuid
from datetime import datetime, timezone

from temporalio import activity
from sqlalchemy import select

from app.core.database import async_session
from app.models.database import JobDB

logger = logging.getLogger(__name__)


@activity.defn
async def update_job_status_activity(job_id: str, status: str) -> None:
    """Job 상태를 DB에 즉시 반영.

    Args:
        job_id: Job UUID 문자열
        status: JobStatus enum 값 (e.g. "enriching", "planning")
    """
    async with async_session() as session:
        result = await session.execute(
            select(JobDB).where(JobDB.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job is None:
            logger.warning(f"Job {job_id} not found for status update")
            return

        job.status = status
        job.updated_at = datetime.now(timezone.utc)
        await session.commit()

    logger.info(f"Job {job_id} status updated to {status}")
```

**Step 4: 테스트 통과 확인**

Run: `cd /Users/sabyun/goinfre/IaaS/backend && .venv/bin/python -m pytest tests/test_update_job_status.py -v`
Expected: 2 passed

**Step 5: 커밋**

```bash
git add backend/app/workflows/activities/update_job_status.py backend/tests/test_update_job_status.py
git commit -m "feat: JIT-126 update_job_status Activity 생성 + 테스트"
```

---

## Task 4: 워크플로우에 상태 동기화 Activity 연동

**Files:**
- Modify: `backend/app/workflows/interview_workflow.py:14-39` (import), `:662-666` (`_update_status`)
- Modify: `backend/app/worker.py:24-97` (Activity 등록)

**Step 1: interview_workflow.py — import 추가**

`with workflow.unsafe.imports_passed_through():` 블록 안에 추가 (line 38 이후):

```python
    from app.workflows.activities.update_job_status import update_job_status_activity
```

**Step 2: `_update_status()` 메서드 수정**

기존 (line 662-666):
```python
    def _update_status(self, status: JobStatus, phase: str, progress: int):
        self._status = status.value
        self._current_phase = phase
        self._progress = progress
        logger.info(f"Phase: {phase} ({progress}%)")
```

수정 — async로 변경하고 Activity 호출 추가:
```python
    async def _update_status(self, status: JobStatus, phase: str, progress: int):
        self._status = status.value
        self._current_phase = phase
        self._progress = progress
        logger.info(f"Phase: {phase} ({progress}%)")

        # DB 즉시 동기화
        job_id = getattr(self, "_job_id", None)
        if job_id:
            try:
                await workflow.execute_activity(
                    update_job_status_activity,
                    args=[job_id, status.value],
                    start_to_close_timeout=timedelta(seconds=10),
                    schedule_to_close_timeout=timedelta(seconds=15),
                )
            except Exception as e:
                logger.warning(f"DB status sync failed (non-fatal): {e}")
```

**Step 3: `_job_id` 필드 설정**

`interview_workflow.py`의 `run()` 메서드 시작 부분 (line ~65)에서 `self._job_id` 를 설정:

```python
        self._job_id = input_data.get("job_id")
```

기존에 `job_id = input_data.get("job_id")` 로컬 변수가 line 576에서 사용되는데, 워크플로우 시작 시점에 인스턴스 변수로도 저장해야 함.

**Step 4: 모든 `self._update_status()` 호출을 `await self._update_status()`로 변경**

`_update_status`가 async가 되었으므로 호출부를 모두 `await`로 변경. 해당 줄:
- line 85: `self._update_status(...)` → `await self._update_status(...)`
- line 95: 동일
- line 105: 동일
- line 200: 동일
- line 238: 동일
- line 322: 동일
- line 343: 동일
- line 410: 동일
- line 430: 동일
- line 578: 동일
- line 598: 동일

**Step 5: worker.py — Activity 등록**

`backend/app/worker.py`에 import 추가 (line 42 근처):

```python
from app.workflows.activities.update_job_status import update_job_status_activity
```

`ACTIVITIES` 리스트에 추가 (line 96 근처):

```python
    # Status sync
    update_job_status_activity,
```

**Step 6: 커밋**

```bash
git add backend/app/workflows/interview_workflow.py backend/app/worker.py
git commit -m "feat: JIT-126 _update_status()에서 DB 즉시 동기화 Activity 호출"
```

---

## Task 5: 이메일 템플릿 + 발송 Activity 생성 (JIT-127 핵심)

**Files:**
- Create: `backend/app/workflows/activities/email_template.py`
- Create: `backend/app/workflows/activities/send_email_notification.py`
- Test: `backend/tests/test_email_notification.py`

**Step 1: 테스트 작성**

```python
# backend/tests/test_email_notification.py
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
```

**Step 2: 테스트 실패 확인**

Run: `cd /Users/sabyun/goinfre/IaaS/backend && .venv/bin/python -m pytest tests/test_email_notification.py -v`
Expected: FAIL

**Step 3: 이메일 템플릿 구현**

```python
# backend/app/workflows/activities/email_template.py
"""
backend/app/workflows/activities/email_template.py
이메일 알림 HTML 템플릿
"""


def render_email_template(
    status: str,
    user_name: str,
    job_id: str,
    candidate_info: str,
    frontend_url: str,
) -> str:
    """이메일 HTML 템플릿 렌더링.

    Args:
        status: "completed" 또는 "failed"
        user_name: 수신자 이름
        job_id: Job UUID
        candidate_info: JD 요약 또는 후보자 정보
        frontend_url: 프론트엔드 도메인 URL
    """
    if status == "completed":
        title = "면접 스크립트가 준비되었습니다"
        message = f"<b>{candidate_info}</b> 포지션의 면접 스크립트 생성이 완료되었습니다."
        button_text = "결과 확인하기"
        button_url = f"{frontend_url}/interview/{job_id}/result"
        button_color = "#10b981"
        icon = "&#9989;"
    else:
        title = "분석 중 문제가 발생했습니다"
        message = f"<b>{candidate_info}</b> 포지션의 면접 스크립트 생성에 실패했습니다."
        button_text = "다시 시도하기"
        button_url = f"{frontend_url}/jobs"
        button_color = "#ef4444"
        icon = "&#10060;"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px 40px;text-align:center;">
          <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:700;">Jittda</h1>
          <p style="color:#e0e7ff;margin:8px 0 0;font-size:14px;">AI Interview Script Generator</p>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:40px;">
          <p style="font-size:16px;color:#374151;margin:0 0 8px;">{user_name}님, 안녕하세요.</p>
          <h2 style="font-size:20px;color:#111827;margin:16px 0;">{icon} {title}</h2>
          <p style="font-size:15px;color:#4b5563;line-height:1.6;margin:0 0 32px;">{message}</p>
          <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
            <tr><td style="background:{button_color};border-radius:8px;padding:14px 32px;">
              <a href="{button_url}" style="color:#ffffff;text-decoration:none;font-size:16px;font-weight:600;">{button_text}</a>
            </td></tr>
          </table>
        </td></tr>
        <!-- Footer -->
        <tr><td style="padding:24px 40px;background:#f9fafb;border-top:1px solid #e5e7eb;text-align:center;">
          <p style="font-size:12px;color:#9ca3af;margin:0;">&copy; 2026 Jittda. All rights reserved.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
```

**Step 4: 이메일 발송 Activity 구현**

```python
# backend/app/workflows/activities/send_email_notification.py
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
from app.workflows.activities.email_template import render_email_template

logger = logging.getLogger(__name__)


def _send_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
    """Gmail SMTP로 이메일 발송."""
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

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
    if not candidate_info:
        candidate_info = "면접 스크립트"

    user_name = user.name or user.email.split("@")[0]

    # 이메일 제목
    if job.status == "completed":
        subject = f"[Jittda] 면접 스크립트가 준비되었습니다"
    else:
        subject = f"[Jittda] 분석 중 문제가 발생했습니다"

    # HTML 렌더링
    html = render_email_template(
        status=job.status,
        user_name=user_name,
        job_id=job_id,
        candidate_info=candidate_info,
        frontend_url=settings.FRONTEND_URL,
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
```

**Step 5: 테스트 통과 확인**

Run: `cd /Users/sabyun/goinfre/IaaS/backend && .venv/bin/python -m pytest tests/test_email_notification.py -v`
Expected: 5 passed

**Step 6: 커밋**

```bash
git add backend/app/workflows/activities/email_template.py backend/app/workflows/activities/send_email_notification.py backend/tests/test_email_notification.py
git commit -m "feat: JIT-127 이메일 알림 Activity + 템플릿 + 테스트"
```

---

## Task 6: 워크플로우에 이메일 알림 Activity 연동

**Files:**
- Modify: `backend/app/workflows/interview_workflow.py:14-39` (import), `:579-598` (persist_result 후)
- Modify: `backend/app/worker.py`

**Step 1: interview_workflow.py — import 추가**

`with workflow.unsafe.imports_passed_through():` 블록 안에 추가:

```python
    from app.workflows.activities.send_email_notification import send_email_notification
```

**Step 2: persist_result 후 이메일 발송 (성공 경로)**

`persist_result` 호출 후 (line 584 이후), webhook 전에 추가:

```python
                # 이메일 알림 (실패해도 워크플로우 계속)
                try:
                    await workflow.execute_activity(
                        send_email_notification,
                        args=[job_id],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception as email_err:
                    logger.warning(f"Email notification failed (non-fatal): {email_err}")
```

**Step 3: 실패 경로에도 이메일 발송 추가**

`persist_result` 실패 경로 (line 628-635) 후에도 동일하게 추가:

```python
                    # 실패 이메일 알림
                    try:
                        await workflow.execute_activity(
                            send_email_notification,
                            args=[job_id],
                            start_to_close_timeout=timedelta(seconds=30),
                        )
                    except Exception:
                        logger.warning("Email notification for failure failed (non-fatal)")
```

**Step 4: worker.py — Activity 등록**

import 추가:
```python
from app.workflows.activities.send_email_notification import send_email_notification
```

ACTIVITIES 리스트에 추가:
```python
    # Email notification
    send_email_notification,
```

**Step 5: 커밋**

```bash
git add backend/app/workflows/interview_workflow.py backend/app/worker.py
git commit -m "feat: JIT-127 워크플로우에 이메일 알림 Activity 연동"
```

---

## Task 7: 사용자 설정 API — `/auth/me` 수정 + `PATCH /auth/notification`

**Files:**
- Modify: `backend/app/api/routes/auth.py:249-269`

**Step 1: GET /auth/me 응답에 email_notification_enabled 추가**

`backend/app/api/routes/auth.py` — `get_me()` 함수의 반환값 (line 260-269)에 추가:

```python
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "image": user.image,
        "plan": user.plan,
        "role": user.role,
        "github_username": user.github_username,
        "providers": providers,
        "email_notification_enabled": user.email_notification_enabled,
    }
```

**Step 2: PATCH /auth/notification 엔드포인트 추가**

`auth.py` 파일의 `set_role` 엔드포인트 근처에 추가:

```python
class NotificationRequest(BaseModel):
    email_notification_enabled: bool


@router.patch("/notification")
async def update_notification_setting(
    body: NotificationRequest,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """이메일 알림 설정 변경"""
    user.email_notification_enabled = body.email_notification_enabled
    await db.flush()
    return {"email_notification_enabled": user.email_notification_enabled}
```

**Step 3: 커밋**

```bash
git add backend/app/api/routes/auth.py
git commit -m "feat: JIT-127 이메일 알림 설정 API 엔드포인트 추가"
```

---

## Task 8: 프론트엔드 — useAuth 수정 + 알림 설정 API

**Files:**
- Modify: `frontend/src/hooks/useAuth.ts`

**Step 1: User 인터페이스에 필드 추가**

```typescript
interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
  role?: string | null
  github_username?: string | null
  providers?: string[]
  email_notification_enabled?: boolean | null  // 추가
}
```

**Step 2: fetchUser에서 필드 매핑**

`setUser()` 호출 (line 30-38)에 추가:

```typescript
        email_notification_enabled: data.email_notification_enabled,
```

**Step 3: updateNotification 함수 추가**

`useAuth` 훅에 추가:

```typescript
  const updateNotification = useCallback(async (enabled: boolean) => {
    const token = getToken()
    if (!token) return
    const res = await fetch('/auth/notification', {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_notification_enabled: enabled }),
    })
    if (res.ok) {
      setUser(prev => prev ? { ...prev, email_notification_enabled: enabled } : null)
    }
  }, [])
```

return에 `updateNotification` 추가:

```typescript
  return { user, loading, logout, isAuthenticated: !!user, updateRole, updateProfile, updateNotification }
```

**Step 4: 커밋**

```bash
git add frontend/src/hooks/useAuth.ts
git commit -m "feat: JIT-127 useAuth에 알림 설정 API 연동"
```

---

## Task 9: 프론트엔드 — CreateJobPage 알림 모달

**Files:**
- Create: `frontend/src/components/EmailNotificationModal.tsx`
- Modify: `frontend/src/pages/CreateJobPage.tsx`
- Modify: `frontend/src/i18n.ts`

**Step 1: i18n 키 추가**

`frontend/src/i18n.ts` — ko 번역에 추가:

```typescript
      email_notification_title: '이메일 알림 설정',
      email_notification_desc: '작업이 완료되면 이메일로 알림을 받으시겠습니까?',
      email_notification_yes: '네, 알림 받기',
      email_notification_no: '아니요',
```

en 번역에 추가:

```typescript
      email_notification_title: 'Email Notification',
      email_notification_desc: 'Would you like to receive email notifications when jobs are completed?',
      email_notification_yes: 'Yes, notify me',
      email_notification_no: 'No thanks',
```

**Step 2: 모달 컴포넌트 생성**

```tsx
// frontend/src/components/EmailNotificationModal.tsx
import { useTranslation } from 'react-i18next'

interface Props {
  onAccept: () => void
  onDecline: () => void
}

export function EmailNotificationModal({ onAccept, onDecline }: Props) {
  const { t } = useTranslation()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-sm mx-4 animate-in fade-in zoom-in">
        <div className="text-center">
          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {t('email_notification_title')}
          </h3>
          <p className="text-sm text-gray-600 mb-6">
            {t('email_notification_desc')}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={onDecline}
            className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            {t('email_notification_no')}
          </button>
          <button
            onClick={onAccept}
            className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            {t('email_notification_yes')}
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 3: CreateJobPage에 모달 통합**

`frontend/src/pages/CreateJobPage.tsx` 수정:

import 추가:
```typescript
import { useAuth } from '../hooks/useAuth'
import { EmailNotificationModal } from '../components/EmailNotificationModal'
```

컴포넌트 내부에 상태 추가:
```typescript
  const { user, updateNotification } = useAuth()
  const [showNotificationModal, setShowNotificationModal] = useState(false)
  const [pendingSubmit, setPendingSubmit] = useState(false)
```

`handleSubmit` 함수 수정 — submit 시작 시 알림 설정 체크:

```typescript
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!jdText.trim()) return

    // 알림 미설정 시 모달 표시
    if (user?.email_notification_enabled === null || user?.email_notification_enabled === undefined) {
      setPendingSubmit(true)
      setShowNotificationModal(true)
      return
    }

    await submitJob()
  }

  const submitJob = async () => {
    setSubmitting(true)
    setError(null)
    // ... 기존 try/catch 로직 그대로
  }

  const handleNotificationAccept = async () => {
    await updateNotification(true)
    setShowNotificationModal(false)
    if (pendingSubmit) {
      setPendingSubmit(false)
      await submitJob()
    }
  }

  const handleNotificationDecline = async () => {
    await updateNotification(false)
    setShowNotificationModal(false)
    if (pendingSubmit) {
      setPendingSubmit(false)
      await submitJob()
    }
  }
```

JSX에 모달 추가 (return 최하단):
```tsx
      {showNotificationModal && (
        <EmailNotificationModal
          onAccept={handleNotificationAccept}
          onDecline={handleNotificationDecline}
        />
      )}
```

**Step 4: 커밋**

```bash
git add frontend/src/components/EmailNotificationModal.tsx frontend/src/pages/CreateJobPage.tsx frontend/src/i18n.ts
git commit -m "feat: JIT-127 CreateJobPage 이메일 알림 설정 모달"
```

---

## Task 10: 최종 검증 + PR 생성

**Step 1: 백엔드 테스트 실행**

Run: `cd /Users/sabyun/goinfre/IaaS/backend && .venv/bin/python -m pytest tests/test_update_job_status.py tests/test_email_notification.py -v`
Expected: 7 passed

**Step 2: 프론트엔드 타입 체크**

Run: `cd /Users/sabyun/goinfre/IaaS/frontend && npx tsc --noEmit`
Expected: 에러 없음

**Step 3: DB 마이그레이션 적용**

```sql
ALTER TABLE users ADD COLUMN email_notification_enabled BOOLEAN DEFAULT NULL;
```

**Step 4: 최종 커밋 + PR 생성**

```bash
git checkout -b feat/JIT-126-127-email-notification-status-sync
git push -u origin feat/JIT-126-127-email-notification-status-sync
gh pr create --title "feat: JIT-126,127 이메일 알림 + 작업 상태 DB 동기화" --body "..."
```
