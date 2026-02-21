"""
backend/app/workflows/activities/email_template.py
이메일 알림 HTML 템플릿
"""

EMAIL_TEXTS = {
    "ko": {
        "completed_subject": "[Jittda] 면접 스크립트가 준비되었습니다",
        "completed_title": "면접 스크립트가 준비되었습니다",
        "completed_message": "<b>{candidate_info}</b> 포지션의 면접 스크립트 생성이 완료되었습니다.",
        "completed_button": "결과 확인하기",
        "failed_subject": "[Jittda] 분석 중 문제가 발생했습니다",
        "failed_title": "분석 중 문제가 발생했습니다",
        "failed_message": "<b>{candidate_info}</b> 포지션의 면접 스크립트 생성 중 문제가 발생했습니다.",
        "failed_button": "다시 시도하기",
        "greeting": "{user_name}님, 안녕하세요.",
    },
    "en": {
        "completed_subject": "[Jittda] Your Interview Script is Ready",
        "completed_title": "Interview Script Ready",
        "completed_message": "The interview script for the <b>{candidate_info}</b> position has been generated.",
        "completed_button": "View Results",
        "failed_subject": "[Jittda] Analysis Issue Detected",
        "failed_title": "Analysis Issue Detected",
        "failed_message": "An issue occurred while generating the interview script for <b>{candidate_info}</b>.",
        "failed_button": "Try Again",
        "greeting": "Hello, {user_name}.",
    },
}


def render_email_template(
    status: str,
    user_name: str,
    job_id: str,
    candidate_info: str,
    frontend_url: str,
    lang: str = "ko",
) -> str:
    """이메일 HTML 템플릿 렌더링.

    Args:
        status: "completed" 또는 "failed"
        user_name: 수신자 이름
        job_id: Job UUID
        candidate_info: JD 요약 또는 후보자 정보
        frontend_url: 프론트엔드 도메인 URL
        lang: 이메일 언어 ("ko", "en")
    """
    texts = EMAIL_TEXTS.get(lang, EMAIL_TEXTS["en"])

    if status == "completed":
        title = texts["completed_title"]
        message = texts["completed_message"].format(candidate_info=candidate_info)
        button_text = texts["completed_button"]
        button_url = f"{frontend_url}/interview/{job_id}/result"
        button_color = "#10b981"
        icon = "&#9989;"
    else:
        title = texts["failed_title"]
        message = texts["failed_message"].format(candidate_info=candidate_info)
        button_text = texts["failed_button"]
        button_url = f"{frontend_url}/jobs"
        button_color = "#ef4444"
        icon = "&#10060;"

    greeting = texts["greeting"].format(user_name=user_name)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
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
          <p style="font-size:16px;color:#374151;margin:0 0 8px;">{greeting}</p>
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
