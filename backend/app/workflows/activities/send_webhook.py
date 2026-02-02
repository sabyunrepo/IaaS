"""
backend/app/workflows/activities/send_webhook.py
Job 완료 시 callback_url로 결과를 POST하는 Activity
"""
import logging

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def send_webhook(job_id: str, callback_url: str, status: str, final_output: dict | None) -> dict:
    """callback_url로 job 결과를 POST 전송.

    Args:
        job_id: Job UUID
        callback_url: 외부 시스템의 webhook URL
        status: completed | failed
        final_output: 워크플로우 최종 결과 (또는 에러)

    Returns:
        {"sent": bool, "status_code": int | None}
    """
    import httpx

    payload = {
        "job_id": job_id,
        "status": status,
        "output": final_output,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                callback_url,
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": "Vantict-Sniper/4.0"},
            )
            logger.info(f"Webhook sent for job {job_id}: {response.status_code}")
            return {"sent": True, "status_code": response.status_code}
    except Exception as e:
        logger.warning(f"Webhook failed for job {job_id} → {callback_url}: {e}")
        return {"sent": False, "status_code": None}
