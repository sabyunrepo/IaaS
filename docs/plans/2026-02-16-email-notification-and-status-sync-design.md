# 이메일 알림 + 작업 상태 DB 동기화 설계

> 2026-02-16 | 두 기능: (1) Job 완료 시 이메일 알림, (2) 작업 리스트 상태 실시간 반영

## 1. 작업 상태 DB 동기화

### 근본 원인

`interview_workflow.py`의 `_update_status()`가 **워크플로우 메모리만 변경**하고 DB는 건드리지 않음.
DB 업데이트는 95% 시점의 `persist_result` Activity에서만 발생 → 리스트 조회 시 항상 "pending".

| 시점 | 워크플로우 메모리 | DB `jobs.status` | 리스트 조회 |
|------|-------------------|------------------|-------------|
| 생성 | PENDING | pending | pending |
| Phase 0 | ENRICHING | **pending** | **pending** |
| Phase 1~4 | PLANNING~REVIEWING | **pending** | **pending** |
| 95% persist | REVIEWING | completed | completed |

### 해결: Activity 기반 즉시 동기화

각 Phase 진입 시 `update_job_status` Activity를 호출하여 DB를 즉시 업데이트.

**신규 파일:** `backend/app/workflows/activities/update_job_status.py`

```python
@activity.defn
async def update_job_status_activity(job_id: str, status: str) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(JobDB).where(JobDB.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job:
            job.status = status
            job.updated_at = datetime.now(timezone.utc)
            await session.commit()
```

**수정 파일:**
- `interview_workflow.py`: `_update_status()` → Activity 호출 추가
- `worker.py`: Activity 등록

## 2. 이메일 알림

### 아키텍처

```
Job 완료 → persist_result Activity → send_email_notification Activity → Gmail SMTP
```

### DB 마이그레이션

`UserDB` 테이블에 알림 설정 컬럼 추가:

```sql
ALTER TABLE users ADD COLUMN email_notification_enabled BOOLEAN DEFAULT NULL;
```

- `NULL`: 아직 선택하지 않음 → 프론트에서 모달 팝업
- `true`: 알림 켜짐 → 매 Job 완료 시 이메일 발송
- `false`: 알림 꺼짐 → 이메일 발송 안 함

### SMTP 설정

| 환경변수 | 값 |
|----------|-----|
| SMTP_HOST | smtp.gmail.com |
| SMTP_PORT | 587 |
| SMTP_USERNAME | (Gmail 계정) |
| SMTP_PASSWORD | (Gmail App Password) |
| SMTP_FROM_EMAIL | (발신자 이메일) |
| SMTP_FROM_NAME | Jittda |

### 이메일 Activity

**신규 파일:** `backend/app/workflows/activities/send_email_notification.py`

```python
@activity.defn
async def send_email_notification(job_id: str) -> dict:
    """Job 완료 시 이메일 알림 발송"""
    # 1. DB에서 Job + User 조회
    # 2. user.email_notification_enabled 확인
    # 3. True면 → SMTP로 이메일 발송
    # 4. 결과 반환 (sent/skipped/failed)
```

### HTML 이메일 템플릿

플레인 HTML + 인라인 CSS. 내용:
- 제목: `[Jittda] {후보자명} 면접 스크립트가 준비되었습니다`
- 본문: 후보자명, 포지션, 완료 시간
- CTA 버튼: "결과 확인하기" → `{FRONTEND_URL}/interview/{job_id}/result`
- 실패 시: "분석 중 문제가 발생했습니다" + "다시 시도하기" 버튼

### 프론트엔드 변경

**CreateJobPage.tsx 수정:**
1. Job 생성 전 사용자의 `email_notification_enabled` 확인
2. `null`이면 → 모달 팝업: "이메일 알림을 받으시겠습니까?"
3. 선택 시 → `PATCH /api/v1/users/me` 호출하여 설정 저장
4. 이미 `true`/`false`면 → 팝업 없이 바로 Job 생성

**설정 페이지 (기존 프로필):**
- 이메일 알림 토글 스위치 추가

### API 엔드포인트

**신규/수정:**
- `PATCH /api/v1/users/me` — `email_notification_enabled` 업데이트
- `GET /api/v1/users/me` — 현재 설정 포함하여 반환

### 워크플로우 통합

`interview_workflow.py`에서 `persist_result` 성공 후:

```python
# Phase 4 완료 후
await workflow.execute_activity(
    persist_result, args=[self.job_id, final_script], ...
)
# 이메일 알림 (실패해도 워크플로우 계속)
try:
    await workflow.execute_activity(
        send_email_notification, args=[self.job_id],
        start_to_close_timeout=timedelta(seconds=30),
    )
except Exception:
    logger.warning("Email notification failed, continuing...")
```

## 3. 변경 파일 요약

### 백엔드
| 파일 | 변경 |
|------|------|
| `app/core/config.py` | SMTP 환경변수 6개 추가 |
| `app/models/database.py` | `UserDB.email_notification_enabled` 컬럼 추가 |
| `app/workflows/activities/update_job_status.py` | **신규** — DB 상태 동기화 Activity |
| `app/workflows/activities/send_email_notification.py` | **신규** — 이메일 발송 Activity |
| `app/workflows/activities/email_template.py` | **신규** — HTML 이메일 템플릿 |
| `app/workflows/interview_workflow.py` | `_update_status()` + 이메일 Activity 호출 |
| `app/api/routes/users.py` | **신규** — `PATCH /users/me` 엔드포인트 |
| `app/api/routes/auth.py` | `GET /auth/me` 응답에 `email_notification_enabled` 포함 |
| `worker.py` | Activity 2개 등록 |

### 프론트엔드
| 파일 | 변경 |
|------|------|
| `src/pages/CreateJobPage.tsx` | 알림 설정 모달 팝업 |
| `src/components/EmailNotificationModal.tsx` | **신규** — 모달 컴포넌트 |
| `src/api/users.ts` | **신규** — 사용자 설정 API |

### 인프라
| 파일 | 변경 |
|------|------|
| `.env` | SMTP 환경변수 추가 (완료) |
| `.env.example` | SMTP 플레이스홀더 추가 (완료) |

### DB 마이그레이션
```sql
ALTER TABLE users ADD COLUMN email_notification_enabled BOOLEAN DEFAULT NULL;
```
