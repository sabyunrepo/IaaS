---
title: "Application Flow 도메인"
type: moc
layer: domain
status: active
created: 2026-02-19
tags: [moc, domain, application, candidate]
---

# Application Flow 도메인

> 지원자가 공고에 지원하고, 분석이 실행되어 결과가 생성되는 전체 흐름.

## 핵심 모델

### JobPosting

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| company_id | UUID | FK → Company |
| title | str | 공고 제목 |
| description | str | JD (Markdown) |
| required_skills | list[str] | 요구 기술 스택 |
| experience_level | str | "junior" / "mid" / "senior" |
| status | str | "draft" / "open" / "closed" |
| auto_analyze | bool | 자동 분석 여부 |
| created_at | datetime | 생성 시각 |

### Application

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| company_id | UUID | FK → Company |
| job_posting_id | UUID | FK → JobPosting |
| candidate_name | str | 지원자 이름 |
| candidate_email | str | 지원자 이메일 |
| github_url | str? | GitHub URL |
| linkedin_url | str? | LinkedIn URL |
| resume_path | str | 이력서 파일 경로 |
| portfolio_path | str? | 포트폴리오 파일 경로 |
| cover_letter_path | str? | 커버레터 파일 경로 |
| consent_given | bool | 제3자 정보 제공 동의 |
| email_confirmed | bool | 이메일 확인 여부 |
| status | str | "pending" → "confirmed" → "analyzing" → "completed" |
| analysis_job_id | UUID? | FK → HMAS Job (분석 시작 시 생성) |
| created_at | datetime | 생성 시각 |

## 상태 머신

```
pending → (이메일 확인) → confirmed → (분석 시작) → analyzing → (분석 완료) → completed
                                    ↑
                            관리자 직접 등록 (email_confirmed=true)
```

## HMAS 연동

Application이 분석 시작 시:
1. Application 데이터로 Job 생성 (기존 HMAS 파이프라인)
2. `analysis_job_id`에 생성된 Job ID 저장
3. MetaAgent → Supervisors → Workers 실행 (기존 그대로)
4. WebSocket으로 진행률 스트리밍
5. 완료 시 Application.status = "completed"

## 연관 도메인

- **Company** → 회사의 공고에 지원
- **HMAS Graph** → [[application/hmas-graph/MOC|HMAS Graph]]를 통한 분석 실행
- **Identity Resolution** → [[domain/identity-resolution/MOC]] 분석
- **Scoring System** → [[domain/scoring-system/MOC]] 점수 산출
