---
title: "Company 도메인"
type: moc
layer: domain
status: active
created: 2026-02-19
tags: [moc, domain, company, multi-tenant]
---

# Company 도메인

> 멀티테넌트 SaaS를 위한 회사(Organization) 관리 도메인.

## 핵심 모델

### Company

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| name | str | 회사 이름 |
| slug | str | URL-friendly 식별자 (unique) |
| logo_url | str? | 로고 URL |
| description | str? | 회사 소개 |
| auto_analyze | bool | 자동 분석 기본값 |
| plan_tier | str? | 요금제 (확장용, 초기 null) |
| created_at | datetime | 생성 시각 |

### CompanyMember

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| company_id | UUID | FK → Company |
| user_id | UUID | FK → User |
| role | str | "owner" / "admin" / "member" |
| invited_at | datetime | 초대 시각 |
| accepted_at | datetime? | 수락 시각 |

## 비즈니스 규칙

1. **slug 유일성**: 회사 slug는 시스템 전체에서 고유해야 함
2. **owner 필수**: 회사에 최소 1명의 owner가 존재해야 함
3. **slug 형식**: 소문자 + 하이픈만 허용 (a-z, 0-9, -)
4. **요금제 확장**: plan_tier 필드는 추후 요금제 추가 시 사용

## 연관 도메인

- **JobPosting** → 회사가 공고 생성
- **Application** → 회사의 공고에 지원
- **User** → CompanyMember를 통한 N:M 관계
