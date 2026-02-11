# Project Context & Tech Stack

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React 19 + Tailwind CSS 4, react-i18next |
| Backend | FastAPI, Python 3.11 |
| Orchestration | Temporal.io |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7 |
| Storage | LocalStack S3 → AWS S3 |
| LLM | Kimi K2.5 (moonshot-v1-auto) — Langfuse-first, fallback: GPT-4o / Claude |
| Container | Docker Compose |
| Git Analysis | PyGithub (API), PyDriller (로컬), ast (Python), tree-sitter (JS/TS) |
| LinkedIn | Proxycurl API |
| Testing | Playwright (E2E) + pytest (Backend, 474 passed) |

## Architecture Documents
| Document | Path |
|----------|------|
| Master | `docs/architecture/ARCHITECTURE.md` |
| Overview | `docs/architecture/01-overview.md` |
| Data Models | `docs/architecture/02-data-models.md` |
| Workflow | `docs/architecture/03-workflow.md` |
| Infrastructure | `docs/architecture/04-infrastructure.md` |
| API Spec | `docs/architecture/05-api-spec.md` |
| LLM Activity Flow | `docs/architecture/06-llm-activity-flow.md` |
| Prompt Guide | `docs/architecture/07-prompt-guide.md` |
| Human Process | `docs/humanprocess/` |

## Available MCP Servers
| Server | Purpose | Status |
|--------|---------|--------|
| `context7` | 라이브러리 공식 문서 | ✅ |
| `sequential` | 복잡한 분석/추론 | ✅ |
| `magic` | UI 컴포넌트 생성 | ✅ |
| `brave-search` | 웹 검색 | ✅ |
| `playwright` | 브라우저 테스트/자동화 + 스크린샷 | ✅ |
| `claude-mem` | 대화 메모리/검색 | ✅ |
| `linear` | Linear 이슈 관리 | ✅ |
| `db` | PostgreSQL + pgvector | ⚠️ 연결 문자열 필요 |
| `github` | GitHub API 통합 | ⚠️ 재인증 필요 |

## Project-Specific Skills
`/temporal-dev` `/vantict-activity` `/implement` `/test` `/design` `/document` `/troubleshoot` `/research` `/analyze` `/improve` `/linear-ops`
