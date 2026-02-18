---
title: "LinkedIn Profile"
type: moc
layer: domain
parent: "[[domain/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-124"]
---

# LinkedIn Profile

## 개요

LinkedIn Profile 도메인은 BrightData API를 통해 수집한 LinkedIn 프로필 데이터를 **순수 도메인 모델로 구조화**하는 레이어다.

### 책임 범위 (경계)

| 레이어 | 담당 |
|--------|------|
| **Domain (여기)** | 파싱된 데이터의 구조화, 모델 유효성 검증, 계산 프로퍼티 |
| Infrastructure (JIT-125) | BrightData API 호출, raw HTML/JSON 수집, 파싱 |

도메인 레이어는 어떻게 데이터를 가져오는지 알지 못한다. 구조화된 Pydantic 모델을 정의하고 검증하는 것만 책임진다.

### 모델 계층 구조

```
LinkedInProfile
  ├── experiences: list[LinkedInExperience]
  ├── educations:  list[LinkedInEducation]
  ├── skills:      list[LinkedInSkill]
  └── certifications: list[LinkedInCertification]
```

### 핵심 계산 프로퍼티

- `total_experience_months` — 전체 경력 월수 합산 (`sum(e.duration_months for e in experiences)`)
- `current_company` — 현재 재직 회사 (`is_current=True`인 경험 중 첫 번째)

---

## 구성 요소

- [[domain/linkedin-profile/profile-model]] — LinkedInProfile + 하위 Pydantic 모델 전체 정의

---

## Dataview

```dataview
TABLE type, status
FROM "docs/architecture/domain/linkedin-profile"
WHERE type = "component"
SORT file.name ASC
```
