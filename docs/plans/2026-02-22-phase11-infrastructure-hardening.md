# Phase 11: Infrastructure Hardening & Technical Debt Resolution

> Phase 10 코드 리뷰에서 발견된 기술 부채 B1~B5 해소 + 운영 안정성 강화.

## 배경

Phase 10 (PR #368) 코드 리뷰에서 Critical 0, Important 3, Suggestion 5건 도출.
Important 3건(B1~B3)과 Suggestion 중 실제 영향이 있는 B4~B5를 이번 Phase에서 해결.

## 이슈 목록

### [P11-1] DB 커넥션 풀링 도입 (B1) — 긴급

**현재 문제**: 매 HTTP 요청마다 `psycopg.AsyncConnection.connect()` 호출 → TCP 핸드셰이크 + TLS 협상 반복 → 부하 시 `max_connections` 소진.

**구현 계획**:
1. `psycopg_pool>=3.2.0` 패키지 추가 (`pyproject.toml`)
2. `infrastructure/persistence/pool.py` 생성:
   ```python
   from psycopg_pool import AsyncConnectionPool

   _pool: AsyncConnectionPool | None = None

   async def init_pool(conninfo: str, min_size: int = 2, max_size: int = 10) -> AsyncConnectionPool:
       global _pool
       _pool = AsyncConnectionPool(conninfo, min_size=min_size, max_size=max_size)
       await _pool.open()
       return _pool

   def get_pool() -> AsyncConnectionPool:
       if _pool is None:
           raise RuntimeError("DB pool not initialized")
       return _pool

   async def close_pool() -> None:
       if _pool:
           await _pool.close()
   ```
3. `main.py` lifespan에서 `init_pool()` / `close_pool()` 호출
4. **Repository 생성자 마이그레이션**: `conninfo: str` → 제거. Repository 내부에서 `get_pool()` 호출. Route handler에서 `JobRepository(db_url)` 인스턴스화 제거 → 모듈 레벨 또는 함수 내 `JobRepository()` (인자 없음) 사용.
5. Health check: DB pool 재사용 (`get_pool().getconn()`) + **Redis pool/bridge 재사용** (신규 연결 생성 금지)
6. Health check에 pool stats 노출: `pool.get_stats()` → `pool_size`, `pool_available`, `requests_waiting`
7. **Worker**: `main()` 함수에서 `Worker()` 생성 전 `init_pool()` 호출. Pool 사이즈: API `min=2, max=10`, Worker `min=1, max=5` (`max_concurrent_activities=3` 고려).

**롤백 전략**: 마이그레이션 중 `conninfo` 파라미터를 Optional로 유지. pool 미초기화 시 fallback으로 `connect()` 사용 가능. 문제 발생 시 `pool.py` 삭제 + Optional 분기 제거로 빠른 롤백.

**영향 범위**: `repository.py`, `main.py`, `worker.py`, `pool.py` (신규)
**의존**: 없음 (첫 번째로 구현)

### [P11-2] Repository 방어적 개선 (B2) — 중간

**현재 문제**: `list_recent(user_id=None)` → 전체 Job 반환. API에서 차단하지만 repository 레벨 노출.

**구현 계획**:
1. `list_recent()`: `user_id` 필수 파라미터로 변경 (기본값 제거)
2. 호출부 (`jobs.py`) 이미 `user["user_id"]` 전달 → 변경 불필요
3. Repository 모든 메서드 pool 사용으로 변경 (P11-1 이후)

**영향 범위**: `repository.py`
**의존**: P11-1

### [P11-3] 인증 정책 강화 + Rate Limit (B3) — 중간

**현재 문제**: 미인증 사용자가 Job 생성 가능 → `user_id=None` Job은 전역 접근.

**구현 계획**:
1. `create_job`에 `get_current_user` 적용 (인증 필수화)
2. Redis 기반 rate limit 미들웨어:
   - **알고리즘**: Sliding window counter (`INCR` + `EXPIRE`)
   - `POST /api/jobs`: 사용자당 분당 5회
   - `POST /api/auth/*`: IP당 분당 10회
   - **Redis 장애 시**: fail-open (요청 허용 + WARNING 로깅)
3. `infrastructure/security/rate_limiter.py` 생성
4. 429 응답 + `Retry-After` 헤더

**기존 `user_id=NULL` Job 처리**: 기존 NULL-owner Job은 `_check_job_access`에서 누구나 접근 가능 유지 (하위 호환).

**영향 범위**: `jobs.py`, `main.py`, `rate_limiter.py` (신규)
**의존**: 없음 (독립)

### [P11-4] Redis 싱글턴 Concurrency Safety (B4) — 중간

**현재 문제**: `_get_redis()` 전역 싱글턴이 concurrency-safe하지 않음. Temporal Worker에서 동시 async Activity 코루틴 실행 시 경합 → 복수 pool 인스턴스 생성 가능 (나머지 leak).

**구현 계획**:
1. `_get_redis()`에 `asyncio.Lock` 적용 (threading.Lock 아님 — async 컨텍스트)
2. Worker `main()`에서 startup 시 1회 초기화
3. `close_redis_pool()` Worker shutdown에서 보장

**영향 범위**: `activities.py`, `worker.py`
**의존**: P11-6 (shutdown과 연관)

### [P11-5] 공유 인프라 모듈 추출 (B5) — 낮음

**현재 문제**: `_configure_logging()` 이 `worker.py`와 `main.py`에 동일 코드 존재.

**구현 계획**:
1. `infrastructure/logging.py` 생성 — `configure_logging()` 공유
2. `worker.py`와 `main.py`에서 import 변경
3. Worker/Backend 동일 로깅 포맷 보장

**영향 범위**: `logging.py` (신규), `worker.py`, `main.py`
**의존**: 없음 (독립)

### [P11-6] Worker Graceful Shutdown — 중간

**현재 문제**: Worker 종료 시 진행 중인 Activity가 갑작스럽게 중단될 수 있음.

**구현 계획**:
1. `worker.py`에 SIGTERM/SIGINT 핸들러 추가
2. Temporal Worker의 `shutdown()` 호출 → 현재 Activity 완료 대기
3. Redis pool 정리 (`close_redis_pool()`)
4. DB pool 정리 (`close_pool()`)
5. `docker-compose.yml`: `stop_grace_period: 60s`

**영향 범위**: `worker.py`, `docker-compose.yml`
**의존**: P11-1 (DB pool), P11-4 (Redis pool)

### [P11-7] API 통합 테스트 보완 — 중간

**현재 문제**: IDOR 검증이 helper 함수 단위 테스트만 존재. FastAPI 의존성 주입 체인 미검증.

**구현 계획**:
1. `tests/interface/test_jobs_api.py` 생성
2. TestClient 기반 시나리오:
   - 인증 → create_job → get_job → get_job_result (정상 흐름)
   - 타 사용자 Job 접근 시도 → 403
   - 미인증 create_job → 401 (P11-3 이후)
   - Rate limit 초과 → 429 (P11-3 이후)
   - 잘못된 UUID → 400
   - limit 범위 초과 → 422
3. **AsyncMock 기반 Repository/Pool mock** (`psycopg3`는 PostgreSQL 전용, SQLite 비호환)
4. 향후 필요 시 `testcontainers-python`으로 실제 DB 통합 테스트 확장

**영향 범위**: `tests/interface/` (신규)
**의존**: P11-1, P11-3

### [P11-8] Phase 11 Obsidian 동기화 — 낮음

- `/phase-sync 11`로 자동 처리
- 커넥션 풀링 아키텍처를 infrastructure/MOC.md에 반영
- crosscutting/gaps-and-roadmap.md에서 B1~B5 해소 표시

## 배치 구성

| 배치 | 이슈 | 범위 |
|------|------|------|
| **Batch 1** | P11-1, P11-5 | 인프라 기반 (DB 풀링 + 공유 모듈) |
| **Batch 2** | P11-2, P11-4, P11-6 | 안정성 (Repository + Redis + Shutdown) |
| **Batch 3** | P11-3, P11-7, P11-8 | 정책 + 검증 (Rate limit + 통합 테스트 + 동기화) |

## 의존관계

```
P11-1 (DB pool)
  ├── P11-2 (Repository 개선)
  ├── P11-6 (Graceful shutdown)
  └── P11-7 (통합 테스트)

P11-4 (Redis concurrency)
  └── P11-6 (Graceful shutdown)

P11-3 (Rate limit)
  └── P11-7 (통합 테스트)

P11-5 (공유 모듈) — 독립
P11-8 (동기화) — 최종
```

## 성공 기준

- [ ] 691+ 기존 테스트 전체 통과 (회귀 없음)
- [ ] 신규 통합 테스트 추가
- [ ] DB 커넥션: 요청당 신규 연결 → pool 재사용
- [ ] Health check: pool stats 노출
- [ ] Rate limit: 초과 시 429 + fail-open on Redis failure
- [ ] Worker: SIGTERM → graceful shutdown (진행 중 Activity 완료)
- [ ] B1~B5 전부 해소
