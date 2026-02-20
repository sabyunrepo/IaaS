---
title: "Domain Layer"
type: moc
layer: domain
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[MOC]]"
---

# Domain Layer

> 순수 비즈니스 로직 계층. 외부 의존성 0. Infrastructure import 금지.
> 코드 분석 결과의 의미 해석, 점수 산출, 질문 생성의 핵심 알고리즘을 담당한다.

## 하위 도메인

| 도메인 | 역할 | 핵심 모델 |
|--------|------|----------|
| [[identity-resolution/MOC\|Identity Resolution]] | Git 커밋 저자 식별 + 기여도 산출 | IdentityCluster, PureContribution |
| [[scoring-system/MOC\|Scoring System]] | 4대 지표(논리력/전문성/안정성/진정성) 계산 | MetricScore, ConfidenceLevel |
| [[funnel-selection/MOC\|Funnel Selection]] | JD 매칭 레포 선별 (3단계 퍼널) | HardFilter, RelevanceScore |
| [[question-generation/MOC\|Question Generation]] | 코드 기반 면접 질문 생성 (3전략) | QuestionDeck, Strategy |
| [[linkedin-profile/MOC\|LinkedIn Profile]] | LinkedIn 프로필 도메인 모델 | LinkedInProfile, Experience |
| [[domain/company/MOC\|Company]] | Company, CompanyMember | 멀티테넌트 회사 관리 |
| [[domain/application-flow/MOC\|Application Flow]] | JobPosting, Application | 공고 + 지원 + 분석 연동 |

## 문서 목록

```dataview
TABLE status, updated, tags
FROM "docs/architecture/domain"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 ADR

```dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
```
