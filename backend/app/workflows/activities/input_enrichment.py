"""
backend/app/workflows/activities/input_enrichment.py
Smart Input Extraction — 입력 교차 추출 및 보강
"""
import re
import logging

from temporalio import activity

from app.core.observability import observe_activity
from app.exceptions import LinkedInFetchError

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="enrich_input", phase="input_enrichment")
async def enrich_input(input_data: dict) -> dict:
    """
    Phase 0: Smart Input Extraction

    모든 입력에서 URL/프로필 정보를 교차 추출하여 빈 필드를 자동으로 채움.

    Steps:
        1. PDF/DOCX 텍스트에서 URL 추출 (GitHub, LinkedIn)
        2. LinkedIn URL → Bright Data API → 프로필 수집
        3. GitHub username 자동 추론 (URL 패턴)
        4. 중복 제거 + EnrichedInput 생성
    """
    from app.services.document_parser import extract_text
    from app.services.linkedin_service import LinkedInService

    extracted_urls: dict[str, set] = {"github": set(), "linkedin": set()}
    extraction_sources: dict[str, list] = {}

    document_errors: list[dict] = []

    # 1. Resume에서 URL 추출
    if input_data.get("resume_path"):
        activity.heartbeat("Extracting URLs from resume...")
        try:
            text = await extract_text(input_data["resume_path"])
            found = _extract_urls(text)
            for url in found["github"]:
                extracted_urls["github"].add(url)
                extraction_sources.setdefault("github_urls", []).append("resume")
            for url in found["linkedin"]:
                extracted_urls["linkedin"].add(url)
                extraction_sources.setdefault("linkedin_url", []).append("resume")
        except Exception as e:
            logger.warning(f"Resume 파싱 실패 (계속 진행): {e}")
            document_errors.append({"source": "resume", "error": str(e)})

    # 2. Portfolio에서 URL 추출
    if input_data.get("portfolio_path"):
        activity.heartbeat("Extracting URLs from portfolio...")
        try:
            text = await extract_text(input_data["portfolio_path"])
            found = _extract_urls(text)
            for url in found["github"]:
                extracted_urls["github"].add(url)
                extraction_sources.setdefault("github_urls", []).append("portfolio")
        except Exception as e:
            logger.warning(f"Portfolio 파싱 실패 (계속 진행): {e}")
            document_errors.append({"source": "portfolio", "error": str(e)})

    # 3. Cover Letter에서 URL 추출
    if input_data.get("cover_letter_path"):
        activity.heartbeat("Extracting URLs from cover letter...")
        try:
            text = await extract_text(input_data["cover_letter_path"])
            found = _extract_urls(text)
            for url in found["github"]:
                extracted_urls["github"].add(url)
                extraction_sources.setdefault("github_urls", []).append("cover_letter")
        except Exception as e:
            logger.warning(f"Cover letter 파싱 실패 (계속 진행): {e}")
            document_errors.append({"source": "cover_letter", "error": str(e)})

    # 4. 직접 입력된 URL 병합
    for url in input_data.get("github_urls", []):
        extracted_urls["github"].add(str(url))
        extraction_sources.setdefault("github_urls", []).append("user_input")

    linkedin_url = (
        input_data.get("linkedin_url")
        or (list(extracted_urls["linkedin"])[0] if extracted_urls["linkedin"] else None)
    )

    # 5. LinkedIn → Bright Data API (실패 시 graceful fallback)
    linkedin_profile = None
    if linkedin_url:
        activity.heartbeat("Fetching LinkedIn profile via Bright Data...")
        try:
            linkedin_svc = LinkedInService()
            linkedin_profile = await linkedin_svc.get_profile(linkedin_url)
        except LinkedInFetchError:
            raise
        except Exception as e:
            logger.warning(f"Bright Data failed for {linkedin_url}: {e}")
            linkedin_profile = None

        # LinkedIn에서 GitHub URL 발견 시 추가
        if linkedin_profile and linkedin_profile.get("github_url"):
            extracted_urls["github"].add(linkedin_profile["github_url"])
            extraction_sources.setdefault("github_urls", []).append("linkedin")

    # 6. GitHub username 확인 (개인 계정만, Organization은 무시)
    github_urls = list(extracted_urls["github"])
    candidate_username = input_data.get("candidate_github_username")
    username_inference = None
    personal_github_urls = []  # code_analysis에 실제 사용할 URL

    if github_urls:
        activity.heartbeat("Validating GitHub URLs (User vs Organization)...")
        try:
            from app.services.github_service import GitHubService
            github_svc = GitHubService()

            username_inference = await github_svc.infer_candidate_username(
                github_urls=github_urls,
                candidate_name=linkedin_profile.get("full_name") if linkedin_profile else None,
            )

            # 개인 레포 URL만 사용
            personal_github_urls = username_inference.get("personal_repos", [])

            # username이 명시적으로 입력되지 않았으면 추론 결과 사용
            if not candidate_username:
                candidate_username = username_inference.get("username")

            # 건너뛴 조직 레포 로깅
            skipped = username_inference.get("skipped_org_repos", [])
            if skipped:
                logger.info(f"Skipped {len(skipped)} organization repos (no inference)")

        except Exception as e:
            logger.warning(f"GitHub URL validation failed: {e}")
            # 실패 시 URL 그대로 유지하되 username은 없음
            personal_github_urls = github_urls

    # 7. 사용 가능한 분석 목록
    available = ["jd_analysis"]  # JD는 항상
    if any(input_data.get(k) for k in ("resume_path", "portfolio_path", "cover_letter_path")) or linkedin_profile:
        available.append("document_analysis")
    # code_analysis는 개인 레포가 있을 때만 (조직 레포만 있으면 제외)
    if personal_github_urls:
        available.append("code_analysis")

    return {
        "raw_input": input_data,
        "github_urls": personal_github_urls,  # 개인 레포만 (조직 레포 제외)
        "all_extracted_github_urls": github_urls,  # 원본 전체 (로깅/디버깅용)
        "candidate_github_username": candidate_username,
        "github_validation": username_inference,  # 검증 상세 정보
        "linkedin_profile": linkedin_profile,
        "extraction_sources": extraction_sources,
        "available_analyses": available,
        "document_errors": document_errors,
    }


def _extract_urls(text: str) -> dict[str, list[str]]:
    """텍스트에서 GitHub/LinkedIn URL 추출"""
    github_pattern = r'https?://github\.com/[\w\-]+/[\w\-\.]+'
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+'
    return {
        "github": re.findall(github_pattern, text),
        "linkedin": re.findall(linkedin_pattern, text),
    }


def _extract_github_username(github_url: str) -> str | None:
    """GitHub URL에서 username 추출"""
    match = re.match(r'https?://github\.com/([\w\-]+)/[\w\-\.]+', github_url)
    return match.group(1) if match else None
