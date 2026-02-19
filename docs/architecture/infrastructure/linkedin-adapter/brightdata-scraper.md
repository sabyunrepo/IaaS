---
title: "BrightData Scraper"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [brightdata, linkedin, scraping, proxy, exponential-backoff]
parent: "[[linkedin-adapter/MOC]]"
linear: [JIT-125]
---

# BrightData Scraper

## 개요

> BrightData Scraping Browser API를 사용하여 LinkedIn 프로필 URL에서
> raw HTML/JSON을 수집하고 `LinkedInProfile` 도메인 모델로 변환한다.
> Rate limit(429), 비공개 프로필, 네트워크 오류에 대한 지수 백오프 재시도 전략을 포함한다.

## 상세 설계

### 핵심 개념

**BrightData Scraping Browser**:
- 프록시 + 실제 브라우저 렌더링을 결합한 스크레이핑 API
- LinkedIn 세션 관리 및 JavaScript 렌더링을 BrightData 인프라에서 처리
- `POST /scrape`에 URL + 원하는 포맷(json)을 전달하면 파싱된 데이터 반환
- 응답 형식: LinkedIn 프로필 구조화 JSON

**지수 백오프 재시도**:
- Rate limit(429): `2^attempt`초 대기 후 재시도 (최대 3회)
- 네트워크 오류: 동일 백오프 전략 적용
- 모든 시도 소진 시 `None` 반환 (Graceful Degradation — 분석 중단 없음)

**None 반환 시나리오**:
- `linkedin_url`이 빈 문자열/None
- 비공개 프로필 (LinkedIn 접근 제한)
- BrightData API 3회 연속 실패
- 응답에 프로필 데이터 없음

### 환경 변수

```bash
# .env
BRIGHTDATA_API_KEY=bd-...
BRIGHTDATA_SCRAPING_BROWSER_URL=https://api.brightdata.com/browser
```

### 코드 예시

#### BrightDataClient 구현

```python
# infrastructure/linkedin/brightdata_client.py
import asyncio
import httpx
from domain.identity.linkedin_models import LinkedInProfile
from domain.identity.linkedin_normalizer import normalize_linkedin_profile
from core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class BrightDataClient:
    """LinkedIn 프로필 스크레이핑 — BrightData Scraping Browser API"""

    def __init__(
        self,
        api_key: str = settings.BRIGHTDATA_API_KEY,
        scraping_browser_url: str = settings.BRIGHTDATA_SCRAPING_BROWSER_URL,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.base_url = scraping_browser_url
        self.max_retries = max_retries
        self.timeout = timeout

    async def scrape_profile(self, linkedin_url: str) -> LinkedInProfile | None:
        """LinkedIn 프로필 스크레이핑 → 도메인 모델 변환

        Returns None if:
        - linkedin_url이 빈 문자열/None
        - BrightData API 호출 실패 (모든 재시도 소진)
        - 프로필 비공개
        - 응답에 유효한 프로필 데이터 없음
        """
        if not linkedin_url or not linkedin_url.strip():
            logger.debug("linkedin_url이 비어있음 — 스킵")
            return None

        for attempt in range(self.max_retries):
            try:
                result = await self._attempt_scrape(linkedin_url, attempt)
                if result is not None:
                    return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_seconds = 2 ** attempt
                    logger.warning(
                        "BrightData Rate Limit",
                        attempt=attempt + 1,
                        wait_seconds=wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue
                elif e.response.status_code in (403, 404):
                    # 비공개 프로필 또는 존재하지 않는 URL
                    logger.info("LinkedIn 프로필 접근 불가", url=linkedin_url, status=e.response.status_code)
                    return None
                else:
                    logger.error("BrightData HTTP 오류", status=e.response.status_code, attempt=attempt + 1)
                    if attempt == self.max_retries - 1:
                        return None
                    await asyncio.sleep(2 ** attempt)

            except httpx.RequestError as e:
                logger.warning("BrightData 네트워크 오류", error=str(e), attempt=attempt + 1)
                if attempt == self.max_retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)

        return None

    async def _attempt_scrape(
        self, linkedin_url: str, attempt: int
    ) -> LinkedInProfile | None:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/scrape",
                json={
                    "url": linkedin_url,
                    "format": "json",
                    "render_js": True,  # LinkedIn SPA 렌더링
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            raw_data = response.json()

            # 빈 응답 또는 비공개 프로필 처리
            if not raw_data or raw_data.get("error") == "private_profile":
                logger.info("LinkedIn 비공개 프로필", url=linkedin_url)
                return None

            return normalize_linkedin_profile(raw_data)
```

#### LinkedInProfile 도메인 모델

```python
# domain/identity/linkedin_models.py
from pydantic import BaseModel, ConfigDict

class LinkedInExperience(BaseModel):
    company: str
    title: str
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    is_current: bool = False

class LinkedInProfile(BaseModel):
    model_config = ConfigDict(strict=True)

    url: str
    name: str
    headline: str | None = None
    summary: str | None = None
    location: str | None = None
    connections_count: int | None = None
    experiences: list[LinkedInExperience] = []
    skills: list[str] = []
    education: list[dict] = []
    raw_data: dict = {}  # 원본 BrightData 응답 (감사 추적)
```

#### 정규화 함수

```python
# domain/identity/linkedin_normalizer.py
from domain.identity.linkedin_models import LinkedInProfile, LinkedInExperience

def normalize_linkedin_profile(raw_data: dict) -> LinkedInProfile | None:
    """BrightData raw JSON → LinkedInProfile 도메인 모델 변환"""
    try:
        experiences = [
            LinkedInExperience(
                company=exp.get("company", ""),
                title=exp.get("title", ""),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                description=exp.get("description"),
                is_current=exp.get("is_current", False),
            )
            for exp in raw_data.get("experience", [])
        ]
        return LinkedInProfile(
            url=raw_data.get("profile_url", ""),
            name=raw_data.get("name", ""),
            headline=raw_data.get("headline"),
            summary=raw_data.get("summary"),
            location=raw_data.get("location"),
            connections_count=raw_data.get("connections_count"),
            experiences=experiences,
            skills=raw_data.get("skills", []),
            education=raw_data.get("education", []),
            raw_data=raw_data,
        )
    except Exception as e:
        # 정규화 실패 — None 반환 (분석 파이프라인 중단 없음)
        import structlog
        structlog.get_logger(__name__).warning("LinkedIn 정규화 실패", error=str(e))
        return None
```

#### CollectorWorker 통합

```python
# application/nodes/collector_worker.py (LinkedIn 수집 부분)
async def collector_worker(state: ForensicState) -> dict:
    # ... GitHub 수집 로직 ...

    # LinkedIn 수집 (URL이 제공된 경우에만)
    linkedin_profile = None
    if state.get("linkedin_url"):
        linkedin_profile = await brightdata_client.scrape_profile(
            state["linkedin_url"]
        )

        if linkedin_profile:
            # 프로필 임베딩 저장 (벡터 검색에 활용)
            profile_text = f"{linkedin_profile.headline or ''}\n{linkedin_profile.summary or ''}"
            await pgvector_store.save_embedding(
                job_id=state["job_id"],
                kind="linkedin",
                content=profile_text,
                embedding=await embedder.embed(profile_text),
                metadata={
                    "name": linkedin_profile.name,
                    "headline": linkedin_profile.headline,
                    "skills": linkedin_profile.skills[:20],  # 상위 20개
                },
            )

    return {
        "collected_repos": repos,
        "linkedin_profile": (
            linkedin_profile.model_dump() if linkedin_profile else None
        ),
    }
```

### 테스트 케이스

```python
# tests/infrastructure/test_brightdata_client.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_scrape_profile_success():
    """정상 응답 → LinkedInProfile 반환"""
    mock_response = {"name": "김지수", "headline": "Backend Engineer", ...}
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = 200
        result = await BrightDataClient().scrape_profile("https://linkedin.com/in/test")
    assert result is not None
    assert result.name == "김지수"

@pytest.mark.asyncio
async def test_scrape_profile_no_url():
    """URL 미제공 → None 반환"""
    result = await BrightDataClient().scrape_profile("")
    assert result is None

@pytest.mark.asyncio
async def test_scrape_profile_rate_limit():
    """429 → 지수 백오프 후 재시도"""
    # 첫 시도 429, 두 번째 시도 성공
    ...

@pytest.mark.asyncio
async def test_scrape_profile_all_retries_failed():
    """3회 실패 → None (Graceful Degradation)"""
    with patch("httpx.AsyncClient.post", side_effect=httpx.RequestError("connection failed")):
        result = await BrightDataClient(max_retries=3).scrape_profile("https://linkedin.com/in/test")
    assert result is None

@pytest.mark.asyncio
async def test_scrape_profile_private():
    """비공개 프로필 (403) → None"""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403", request=None, response=Mock(status_code=403)
        )
        result = await BrightDataClient().scrape_profile("https://linkedin.com/in/private")
    assert result is None
```

## 관련 문서

- 상위: [[linkedin-adapter/MOC]]
- 연관: [[domain/linkedin-profile/profile-model]]
- 연관: [[vector-search/pgvector-setup]]
