"""LinkedIn 서비스 격리 테스트 — Temporal 없이 직접 호출

사용법:
  docker compose exec backend python tests/test_linkedin_isolated.py
"""
import asyncio
import json
import logging
import sys
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("linkedin_test")

sys.path.insert(0, "/app")
from app.services.linkedin_service import LinkedInService


async def test_linkedin_fetch():
    """LinkedIn 프로필 수집 전체 프로세스 격리 테스트"""
    url = "https://www.linkedin.com/in/byun-sanghoon-303918338/"

    svc = LinkedInService()
    logger.info(f"API Token: {svc.api_token[:10]}..." if svc.api_token else "NOT SET")
    logger.info(f"Target URL: {url}")
    logger.info("=" * 60)

    start = time.time()
    try:
        result = await svc.get_profile(url)
        elapsed = time.time() - start

        if result is None:
            logger.warning(f"결과: None (프로필 없음 또는 404) [{elapsed:.1f}s]")
            return

        logger.info(f"성공! [{elapsed:.1f}s]")
        logger.info("=" * 60)

        # 주요 필드 출력
        logger.info(f"  이름: {result.get('full_name')}")
        logger.info(f"  헤드라인: {result.get('headline')}")
        logger.info(f"  현재회사: {result.get('current_company')}")
        logger.info(f"  국가/도시: {result.get('country')} / {result.get('city')}")

        # 섹션별 카운트
        sections = {
            "경력": len(result.get("experiences") or []),
            "학력": len(result.get("education") or []),
            "스킬": len(result.get("skills") or []),
            "프로젝트": len(result.get("projects") or []),
            "수상": len(result.get("honors_and_awards") or []),
            "추천서": len(result.get("recommendations") or []),
            "봉사활동": len(result.get("volunteer_experience") or []),
            "자격증": len(result.get("certifications") or []),
            "활동": len(result.get("activity") or []),
        }
        logger.info("-" * 40)
        for name, count in sections.items():
            marker = "✅" if count > 0 else "⚠️ "
            logger.info(f"  {marker} {name}: {count}개")

        logger.info(f"  GitHub: {result.get('github_url') or '없음'}")
        logger.info("=" * 60)
        logger.info("LinkedIn 수집 테스트 완료")

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"실패 [{elapsed:.1f}s]: {type(e).__name__}: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_linkedin_fetch())
