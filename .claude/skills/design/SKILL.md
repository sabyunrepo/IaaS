---
name: design
description: 시스템 아키텍처 설계. architecture, design, 설계, 구조, system design 관련 작업 시 사용.
allowed-tools: Read, Grep, Glob
---

# Architecture Design Skill

## 설계 절차
1. `docs/architecture/ARCHITECTURE.md` 전체 구조 확인
2. `docs/architecture/01-overview.md` 시스템 개요 확인
3. 관련 스킬 문서 (`docs/architecture/skills/`) 확인
4. 기존 패턴과 일관성 유지하며 설계
5. 트레이드오프 분석 포함

## 기술 스택 (변경 불가)
- Frontend: Next.js 14+, React, react-i18next
- Backend: FastAPI, Python 3.11+
- Orchestration: Temporal 1.22+
- Database: PostgreSQL 16+ (pgvector, 1536차원)
- Cache: Redis 7+
- Storage: LocalStack S3 → AWS S3
- LLM: OpenAI GPT-4o / Anthropic Claude
- Container: Docker Compose

## 참고 문서
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/01-overview.md`
- `docs/architecture/02-data-models.md`
- `docs/architecture/03-workflow.md`
- `docs/architecture/04-infrastructure.md`
- `docs/architecture/05-api-spec.md`
- `docs/architecture/06-output-spec.md`
- `docs/architecture/07-prompt-guide.md`
