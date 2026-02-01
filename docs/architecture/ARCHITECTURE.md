# Vantict Sniper v4.0 - Architecture Design Document

> **AI Technical Interview Script Generator**
> Local-First, Cloud-Ready Architecture

---

## 📋 Document Index

이 아키텍처 문서는 에이전트가 참조할 수 있도록 모듈화되어 있습니다.

### Core Documents
| 문서 | 설명 | 경로 |
|-----|------|------|
| **Overview** | 시스템 전체 개요 | [01-overview.md](./01-overview.md) |
| **Data Models** | 데이터 모델 정의 | [02-data-models.md](./02-data-models.md) |
| **Workflow** | Temporal 워크플로우 설계 | [03-workflow.md](./03-workflow.md) |
| **Infrastructure** | 인프라 및 배포 설정 | [04-infrastructure.md](./04-infrastructure.md) |
| **API Spec** | REST API 명세 | [05-api-spec.md](./05-api-spec.md) |
| **Output Spec** | 최종 출력 명세 (질문 구조, 뷰 설계, 레벨별 차별화) | [06-output-spec.md](./06-output-spec.md) |
| **Prompt Guide** | 질문 생성 프롬프트 엔지니어링 가이드 | [07-prompt-guide.md](./07-prompt-guide.md) |

### Agent Skills (에이전트 참조용)
| 스킬 | 역할 | 경로 |
|-----|------|------|
| **Planner** | 실행 계획 수립 | [skills/planner/SKILL.md](./skills/planner/SKILL.md) |
| **Document Manager** | 이력서/포트폴리오 분석 | [skills/document-manager/SKILL.md](./skills/document-manager/SKILL.md) |
| **Code Manager** | GitHub 코드 분석 | [skills/code-manager/SKILL.md](./skills/code-manager/SKILL.md) |
| **JD Manager** | 채용공고 분석 | [skills/jd-manager/SKILL.md](./skills/jd-manager/SKILL.md) |
| **Question Generator** | 면접 질문 생성 | [skills/question-generator/SKILL.md](./skills/question-generator/SKILL.md) |
| **Supervisor** | 최종 검증 및 출력 | [skills/supervisor/SKILL.md](./skills/supervisor/SKILL.md) |
| **Checkpoint Manager** | 파이프라인 내구성, LLM 캐싱, 단계별 복구 | [skills/checkpoint-manager/SKILL.md](./skills/checkpoint-manager/SKILL.md) |
| **Architecture Guide** | 구현 에이전트용 아키텍처 참조 가이드 | [skills/architecture-guide/SKILL.md](./skills/architecture-guide/SKILL.md) |
| **Common Tools** | 공통 도구 라이브러리 | [skills/common-tools/SKILL.md](./skills/common-tools/SKILL.md) |

---

## 🎯 Project Summary

### 목적
비개발자 면접관이 **그대로 읽기만 하면 되는** 기술 면접 스크립트 자동 생성

### 핵심 특징
- **입력**: 이력서(PDF), 포트폴리오(DOCX), GitHub URL, 채용공고(JD)
- **출력**: 10개 맞춤형 면접 질문 + 예상 답변 + 평가 시나리오 + 용어 설명
- **다국어**: 주 언어 생성, 다국어는 on-demand API 번역 (저장 X)
- **검증**: 코드 기반 "반박 불가능한" 질문 (Hallucination 방지)
- **내구성**: LLM 결과 캐싱 + 단계별 체크포인트 + 실패 지점 복구

### 기술 스택 (MVP)
```
Frontend     : Next.js + React
Backend      : FastAPI + Python 3.11
Orchestration: Temporal.io (로컬/클라우드 동일 코드)
LLM SDK      : Pydantic AI (오케스트레이션) + LiteLLM (게이트웨이/캐싱/fallback)
               + Instructor (복잡 구조화 추출 보완)
LLM 관측     : Langfuse (self-host, 프롬프트 관리 + 토큰/비용 추적)
Document     : Docling (IBM, PDF/DOCX 구조화 파싱) + pymupdf4llm (경량 fallback)
Database     : PostgreSQL + pgvector
Cache        : Redis (LiteLLM 캐시 + 세션 상태)
Storage      : obstore (Local 기본 → Cloudflare R2 프로덕션 / AWS S3)
Code Analysis: PyGithub + PyDriller + tree-sitter (AST)
LLM Provider : OpenAI GPT-4o / Anthropic Claude (LiteLLM fallback 체인)
Container    : Docker Compose → AWS Copilot
```

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                    │
│  ┌─────────────┐                                                        │
│  │  Frontend   │ Next.js + React                                       │
│  │  :3000      │                                                        │
│  └──────┬──────┘                                                        │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ REST API
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API LAYER                                       │
│  ┌─────────────┐     ┌─────────────┐                                   │
│  │  FastAPI    │────▶│  Temporal   │ Workflow Orchestration            │
│  │  :8000      │     │  Client     │                                   │
│  └─────────────┘     └──────┬──────┘                                   │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │ Task Queue
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKER LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Temporal Worker                               │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │   │
│  │  │ Input  │ │Planner │ │Document│ │  Code  │ │   JD   │ │Question│  │   │
│  │  │ Enrich │ │Activity│ │Activity│ │Activity│ │Activity│ │Activity│  │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │   │
│  │        + Supervisor Activity + Checkpoint Activities                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│  │ PostgreSQL  │     │   Redis     │     │ LocalStack  │               │
│  │ + pgvector  │     │   Cache     │     │     S3      │               │
│  │   :5432     │     │   :6379     │     │   :4566     │               │
│  └─────────────┘     └─────────────┘     └─────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
vantict-sniper/
├── docker-compose.yml          # 로컬 개발 환경
├── docker-compose.prod.yml     # 프로덕션 오버라이드
├── .env.local                  # 로컬 환경 변수
├── .env.production             # 프로덕션 환경 변수 (gitignore, secrets는 Copilot/vault)
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py             # FastAPI 엔트리포인트
│   │   ├── exceptions.py       # VantictBaseError 예외 계층
│   │   ├── core/               # 핵심 설정
│   │   │   ├── config.py       # Settings (환경 기반 설정)
│   │   │   ├── temporal.py     # Temporal 클라이언트 팩토리
│   │   │   └── database.py     # DB 세션 관리
│   │   ├── api/                # REST API 라우터
│   │   │   ├── routes/
│   │   │   ├── deps.py
│   │   │   └── health.py       # 헬스체크 엔드포인트
│   │   ├── workflows/          # Temporal 워크플로우
│   │   │   ├── interview_workflow.py
│   │   │   └── activities/
│   │   │       ├── input_enrichment.py   # Phase 0: Smart Input Extraction
│   │   │       ├── planning.py
│   │   │       ├── document_analysis.py
│   │   │       ├── code_analysis.py
│   │   │       ├── jd_analysis.py
│   │   │       ├── question_generation.py
│   │   │       ├── quality_review.py
│   │   │       ├── finalization.py
│   │   │       └── checkpoint_activities.py
│   │   ├── services/           # 비즈니스 로직
│   │   │   ├── llm_config.py       # Pydantic AI Agent 설정 + LiteLLM 초기화
│   │   │   ├── checkpoint_store.py # 단계별 스냅샷 저장소
│   │   │   ├── github_service.py
│   │   │   └── vector_store.py
│   │   ├── models/             # 데이터 모델
│   │   │   ├── job.py
│   │   │   ├── question.py
│   │   │   └── analysis.py
│   │   ├── prompts/            # LLM 프롬프트 (Jinja2 템플릿 → Langfuse Phase 2)
│   │   │   └── *.j2
│   │   └── worker.py           # Temporal Worker 엔트리
│   └── tests/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── i18n/
│   │   └── hooks/
│   └── public/
│       └── locales/            # i18n 번역 파일
│           ├── ko/
│           ├── en/
│           └── ...
│
├── docs/
│   └── architecture/           # 이 문서들
│       ├── ARCHITECTURE.md
│       ├── 01-overview.md
│       ├── 02-data-models.md
│       ├── 03-workflow.md
│       ├── 04-infrastructure.md
│       ├── 05-api-spec.md
│       ├── 06-output-spec.md
│       ├── 07-prompt-guide.md
│       └── skills/
│           ├── planner/
│           ├── document-manager/
│           ├── code-manager/
│           ├── jd-manager/
│           ├── question-generator/
│           ├── supervisor/
│           ├── checkpoint-manager/
│           ├── architecture-guide/
│           └── common-tools/
│
└── scripts/
    ├── setup.sh                # 로컬 환경 설정
    └── deploy.sh               # 클라우드 배포
```

---

## 🚀 Quick Start

### 로컬 개발 환경 실행
```bash
# 1. 환경 변수 설정
cp .env.example .env.local

# 2. 전체 환경 시작
docker compose up -d

# 3. 접속 URL
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Temporal UI: http://localhost:8080
# - Langfuse: http://localhost:3100
# - API Docs: http://localhost:8000/docs
```

### 클라우드 배포 (나중에)
```bash
# AWS Copilot으로 원클릭 배포
copilot deploy --env production
```

---

## 📚 Related Documents

각 문서의 상세 내용은 해당 파일을 참조하세요.

- 전체 개요: [01-overview.md](./01-overview.md)
- 데이터 모델: [02-data-models.md](./02-data-models.md)
- 워크플로우: [03-workflow.md](./03-workflow.md)
- 인프라: [04-infrastructure.md](./04-infrastructure.md)
- API 명세: [05-api-spec.md](./05-api-spec.md)
- 출력 명세: [06-output-spec.md](./06-output-spec.md)
- 프롬프트 가이드: [07-prompt-guide.md](./07-prompt-guide.md)

---

## 🔄 Version History

| 버전 | 날짜 | 변경 내용 |
|-----|------|----------|
| 4.2 | 2026-01-31 | 아키텍처 리뷰: on-demand i18n, Storage 추상화(local/R2/S3), Phase 0, user_id 소유자 모델, 예외 계층 |
| 4.1 | 2026-01-29 | 체크포인트/복구 시스템 추가 (LLM 캐시, 단계별 스냅샷, 재시작 API) |
| 4.0 | 2025-01-28 | Local-First 아키텍처로 재설계 |
| 3.0 | - | 클라우드 우선 설계 (폐기) |

---

*이 문서는 Vantict Sniper v4.0의 마스터 아키텍처 문서입니다.*
