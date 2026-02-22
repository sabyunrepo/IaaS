# Phase 12: Observability & Service Resilience

> Phase 11CR 코드 리뷰 완료 후, **빌드 오류 해결** + 운영 가시성 + 외부 서비스 복원력 + 테스트 확장.

## Context

- Phase 0~11 + 11CR: 아키텍처 갭 G1~G16, B1~B5, C1~C3, I1~I6 전부 해소
- **빌드 오류**: Frontend Docker 빌드 실패 (pnpm-lock.yaml 미동기화)
- 남은 갭: **관측성(Observability)** 최소 수준, **외부 서비스 circuit breaker** 없음, **E2E 테스트 커버리지** 미흡
- 코드베이스: 9,001 LOC, 705 tests, 13 files 수정된 Phase 11CR 반영 완료

## 범위

### 12-0: Docker Compose 빌드 오류 해결 (최우선)

**현재 빌드 상태**:
- Backend: ✅ 빌드 성공 + 정상 기동
- Worker: ✅ 빌드 성공 + 정상 기동 (11 Activities 등록)
- Frontend: ❌ **빌드 실패**

**Frontend 오류 상세**:
```
ERR_PNPM_OUTDATED_LOCKFILE: Cannot install with "frozen-lockfile"
because pnpm-lock.yaml is not up to date with <ROOT>/packages/admin-app/package.json

Failure reason:
specifiers in the lockfile don't match specifiers in package.json:
* 2 dependencies were added: @types/d3@^7.4.3, d3@^7.9.0
```

**근본 원인**: Phase 6에서 D3.js 차트 추가 시 `package.json`에 `d3`, `@types/d3`를 추가했으나 `pnpm-lock.yaml`이 갱신되지 않음. Docker 빌드 시 `--frozen-lockfile` 플래그가 lockfile 정합성을 강제하여 실패.

**수정 방법**:
1. 로컬에서 `pnpm install` 실행 → lockfile 갱신
2. Dockerfile 빌드 검증 (`docker compose build frontend`)
3. Frontend 컨테이너 정상 기동 확인 (nginx SPA serving)
4. 전체 `docker compose up` E2E 검증

**추가 점검**:
- Backend/Worker 런타임 import 오류 확인 (Phase 11CR 변경사항 반영)
- 환경변수 누락 경고 정리 (`LLM_API_KEY`, `JWT_SECRET`)
- `docker compose up` 전체 서비스 health check 통과

**파일**:
- `jittda/frontend/pnpm-lock.yaml` (갱신)
- `jittda/frontend/packages/admin-app/package.json` (확인)
- `jittda/docker-compose.yml` (필요 시 수정)

**성공 기준**: `docker compose build && docker compose up -d` 전 서비스 정상 기동

### 12-1: Langfuse Trace Hierarchy (관측성 핵심)

**현재**: Langfuse가 프롬프트 로딩/추적에만 사용. Activity 레벨 trace 없음.

**목표**: Temporal Workflow → Activity → LLM Call 3단 trace hierarchy 구축.

**구현 (2-tier)**:

**Tier 1 — Activity-level trace** (duration, error classification, heartbeat):
- `infrastructure/observability/trace_decorator.py` — Langfuse `@observe()` 기반 Activity 데코레이터
- 11개 Activity 전부 적용:
  1. `input_agent`
  2. `plan_agent`
  3. `collector_agent`
  4. `forensic_agent`
  5. `logic_agent`
  6. `stack_agent`
  7. `profile_agent`
  8. `question_orchestrator_agent`
  9. `enhancement_agent`
  10. `quality_gate_agent`
  11. `output_agent`
- Trace ID = Temporal Workflow ID (Job 단위 추적)

**Tier 2 — LLM-call-level trace** (token usage, model, per-call latency):
- `InstructorClient.create()` 수정: Langfuse trace context 전달 + 토큰 사용량 반환
- 각 LLM 호출이 부모 Activity trace의 child span으로 기록

> Langfuse SDK `>=2.57.0`의 `@observe()` 네이티브 데코레이터 활용. 커스텀 trace 구현 최소화.

**파일**:
- `jittda/backend/src/infrastructure/observability/trace_decorator.py` (신규)
- `jittda/backend/src/infrastructure/observability/__init__.py` (신규)
- `jittda/backend/src/application/temporal/activities.py` (수정)
- `jittda/backend/src/infrastructure/llm/instructor_client.py` (수정 — Tier 2)

### 12-2: Circuit Breaker — 외부 서비스 복원력

**현재**: GitHub, SonarQube, LinkedIn, LLM API 호출에 재시도/차단기 없음. 외부 서비스 장애 시 전체 파이프라인 실패.

**목표**: Circuit breaker 패턴 도입 + graceful degradation.

**구현**:
- `infrastructure/resilience/circuit_breaker.py` — 상태 머신 (Closed → Open → Half-Open)
- **상태 저장: Redis** (`cb:{service_name}:state`, `cb:{service_name}:failures`) — Temporal Worker 다중 프로세스 간 공유
- 설정: failure_threshold=5, recovery_timeout=60s, half_open_max_calls=2 (환경변수로 오버라이드 가능)
- 적용 대상: GitHubClient, SonarQubeAdapter, BrightDataClient, InstructorClient
- Fallback 전략:
  - GitHub API 실패 → 캐시된 repo 메타데이터 사용
  - SonarQube 실패 → Radon/Lizard 로컬 분석만 사용
  - LinkedIn 실패 → 빈 프로필 (기존 fallback 유지)
  - LLM 실패 → Temporal Activity 재시도 (기존 retry policy)

**파일**:
- `jittda/backend/src/infrastructure/resilience/circuit_breaker.py` (신규)
- `jittda/backend/src/infrastructure/resilience/__init__.py` (신규)
- `jittda/backend/src/infrastructure/github/github_client.py` (수정)
- `jittda/backend/src/infrastructure/analysis/sonarqube_adapter.py` (수정)
- `jittda/backend/src/infrastructure/linkedin/brightdata_client.py` (수정)

### 12-3: Health Check 고도화 + Metrics Endpoint

**현재**: `/api/health`가 DB/Redis/Temporal 상태만 반환. 메트릭 없음.

**목표**: Prometheus-compatible `/metrics` 엔드포인트 + 구조화된 health check.

**의존성 추가**: `prometheus-client>=0.21.0` → `pyproject.toml`

**구현**:
- `infrastructure/observability/metrics.py` — Prometheus client 래퍼
- 메트릭: `jittda_jobs_total`, `jittda_job_duration_seconds`, `jittda_llm_tokens_total`, `jittda_circuit_breaker_state`
- Health check 확장: pool stats, circuit breaker 상태, 최근 job 성공/실패율
- `/api/metrics` 엔드포인트 (Prometheus scrape 대상)

**파일**:
- `jittda/backend/src/infrastructure/observability/metrics.py` (수정 — 12-1에서 이미 생성)
- `jittda/backend/src/interface/api/main.py` (수정)
- `jittda/backend/pyproject.toml` (수정 — `prometheus-client` 추가)

### 12-4: 테스트 확장 (E2E + 단위)

**현재**: 6 E2E 시나리오 + 0 Playwright 테스트 (jittda/ 내). Phase 6 설계 대비 미흡.

**목표**: 핵심 워크플로우 10+ E2E + 신규 모듈 단위 테스트.

**테스트 인프라**: 기존 conftest.py mock 패턴 사용 (AsyncMock). Redis/DB 필요 시나리오는 `@pytest.mark.integration` 마크로 분리, Docker Compose 환경에서만 실행.

**E2E 시나리오**:
- OAuth 인증 플로우 (코드 교환 패턴 — Phase 11CR 신규)
- WebSocket 인증 + 실시간 이벤트 수신
- Rate limiter 동작 검증 (5/min 초과 시 429)
- Circuit breaker 동작 검증 (외부 서비스 장애 시 fallback)
- 동시 Job 격리 검증 (2 Job 병렬 실행, 데이터 교차 오염 없음)
- Job lifecycle: 생성 → 진행 → 완료 → 결과 조회
- 에러 시나리오: 빈 입력, 잘못된 UUID, 권한 없는 Job 접근

**단위 테스트 (신규 모듈)**:
- `test_trace_decorator.py` — trace hierarchy, span 생성, 에러 전파
- `test_circuit_breaker.py` — 상태 전이 (Closed→Open→Half-Open), 타이밍, Redis 연동
- `test_request_cache.py` — 캐시 hit/miss, TTL 만료, force_refresh
- `test_metrics.py` — 메트릭 등록, 카운터 증가, Prometheus 응답 포맷

**파일**:
- `jittda/backend/tests/e2e/test_auth_flow.py` (신규)
- `jittda/backend/tests/e2e/test_websocket_auth.py` (신규)
- `jittda/backend/tests/e2e/test_rate_limiter.py` (신규)
- `jittda/backend/tests/e2e/test_circuit_breaker.py` (신규)
- `jittda/backend/tests/e2e/test_concurrent_jobs.py` (신규)
- `jittda/backend/tests/infrastructure/test_trace_decorator.py` (신규)
- `jittda/backend/tests/infrastructure/test_circuit_breaker.py` (신규)
- `jittda/backend/tests/infrastructure/test_request_cache.py` (신규)
- `jittda/backend/tests/infrastructure/test_metrics.py` (신규)

### 12-5: Request Caching Layer

**현재**: 동일 repo 분석 시 GitHub API + LLM 호출 중복. 캐싱 없음.

**목표**: Redis 기반 request-level 캐싱.

**구현**:
- `infrastructure/cache/request_cache.py` — Redis TTL 캐시 (decorator)
- GitHub API 결과: repo metadata (TTL 환경변수, 기본 1h), commit history (기본 30min)
- Embedding 결과: 동일 텍스트 → 캐시된 벡터 반환 (기본 24h)
- TTL 설정: `CACHE_TTL_GITHUB_META=3600`, `CACHE_TTL_GITHUB_COMMITS=1800`, `CACHE_TTL_EMBEDDINGS=86400` 환경변수로 조정 가능
- 캐시 키: `{service}:{hash(params)}` 패턴
- 캐시 무효화: Job 재실행 시 `force_refresh=True` 옵션

**파일**:
- `jittda/backend/src/infrastructure/cache/request_cache.py` (신규)
- `jittda/backend/src/infrastructure/cache/__init__.py` (신규)
- `jittda/backend/src/infrastructure/github/github_client.py` (수정)
- `jittda/backend/src/infrastructure/embedding/embedding_service.py` (수정)

### 12-6: Operational Runbook

**현재**: 운영 문서 없음.

**목표**: 핵심 장애 시나리오별 대응 가이드.

**구현** (Obsidian vault):
- `crosscutting/runbooks/slow-job-analysis.md` — 느린 Job 분석 트러블슈팅
- `crosscutting/runbooks/llm-quality-degradation.md` — LLM 품질 저하 대응
- `crosscutting/runbooks/pool-exhaustion.md` — DB 풀 고갈 대응
- `crosscutting/runbooks/temporal-worker-failure.md` — Worker 장애 복구
- `crosscutting/runbooks/circuit-breaker-alerts.md` — Circuit Breaker 상태 경보 대응

## 의존관계

```
12-0 (빌드 수정) ──→ 나머지 전체 (빌드 통과가 전제조건)
12-1 (Trace) ──→ 12-3 (Metrics)
12-2 (Circuit Breaker) ──→ 12-4 (테스트)
12-5 (Cache) ──→ 독립
12-6 (Runbook) ──→ 12-1, 12-2, 12-3 완료 후
```

## 파일 변경 요약

| 유형 | 파일 수 |
|------|--------|
| 빌드 수정 (lockfile 등) | 2 |
| 신규 (Python) | 7 |
| 신규 (테스트) | 9 |
| 수정 (Python) | 7 |
| 수정 (설정) | 1 |
| 신규 (Obsidian) | 5 |
| **합계** | **31** |

## 성공 기준

- [ ] `docker compose build` 전체 성공 (frontend + backend + worker)
- [ ] `docker compose up -d` 전 서비스 health check 통과
- [ ] 11개 Activity 전부 Langfuse trace에 나타남 (p50/p95 latency 확인 가능)
- [ ] LLM 호출별 토큰 사용량이 Langfuse child span으로 기록
- [ ] Circuit breaker: 외부 서비스 5회 실패 → Open 상태 → fallback 동작 (Redis 기반)
- [ ] `/api/metrics` Prometheus-compatible 응답
- [ ] E2E 테스트 10+ 시나리오 통과
- [ ] 신규 모듈 단위 테스트 4개 파일 전체 통과
- [ ] GitHub API 캐시 히트 시 응답 시간 90%+ 감소
- [ ] 운영 문서 5개 Obsidian vault에 존재
