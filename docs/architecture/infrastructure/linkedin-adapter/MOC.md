---
title: "LinkedIn Adapter"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
tags: [linkedin, brightdata, scraping, profile]
---

# LinkedIn Adapter

> BrightData Scraping Browser API를 통해 LinkedIn 프로필을 수집하고
> Domain 모델(`LinkedInProfile`)로 변환하는 어댑터 계층.

## 역할

- CollectorWorker(W1)에서 호출되어 LinkedIn URL → `LinkedInProfile` 변환
- BrightData 프록시 + 지수 백오프 재시도 (max 3회)
- Rate limit(429) 자동 처리
- 프로필 임베딩을 pgvector에 저장 (`kind="linkedin"`)

## 문서 목록

| 문서 | 내용 |
|------|------|
| [[linkedin-adapter/brightdata-scraper\|BrightData Scraper]] | BrightData 클라이언트, 프록시 관리, 재시도 전략 |

## 아키텍처 위치

```
infrastructure/linkedin/
└── brightdata_client.py     # BrightData 스크레이핑 클라이언트

domain/identity/
├── linkedin_models.py       # LinkedInProfile 도메인 모델
└── linkedin_normalizer.py   # raw HTML/JSON → LinkedInProfile 변환
```

## 데이터 흐름

```
linkedin_url (입력)
      │
      ▼
BrightDataClient.scrape_profile(url)
      │  ← BrightData Scraping Browser API
      ▼
raw HTML/JSON
      │
      ▼
normalize_linkedin_profile(raw_data)   ← domain/identity/linkedin_normalizer.py
      │
      ▼
LinkedInProfile (도메인 모델)
      │
      ├──→ pgvector_store.save_embedding(kind="linkedin")
      └──→ ForensicState.linkedin_profile
```

## 관련 Linear 티켓

- JIT-125: LinkedIn 어댑터 (BrightData 클라이언트 + 프로필 스크레이핑)

## 관련 문서

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure/linkedin-adapter"
WHERE file.name != "MOC"
SORT file.name ASC
```
