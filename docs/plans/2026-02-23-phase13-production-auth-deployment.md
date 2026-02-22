# Phase 13: Production Auth & Deployment Hardening

> Phase 12 완료 후, **OAuth 인증 프로덕션 리다이렉트 수정** + 프록시 인식 + 프론트엔드 배포 검증.

## Context

- Phase 0~12 완료: 모든 아키텍처 갭 G1~G16, B1~B5, C1~C3, I1~I6 해소
- Phase 12 환경변수 감사 (JIT-338~341) 완료
- **사용자 보고 버그**: OAuth 로그인 시 `http://localhost:8000/api/auth/google`로 리다이렉트됨 (프로덕션에서 작동 불가)
- 코드베이스: ~9,766 LOC (backend src), 507 tests, 374 PRs merged

## 범위

### 13-0: OAuth 리다이렉트 프로덕션 수정 (최우선)

**현재 문제**:
- `AuthContext.tsx:50` → `window.location.href = \`${API_BASE}/api/auth/${provider}\``
- `api.ts:9` → `API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'`
- nginx가 `/api/` 프록시를 처리하므로 **절대 URL 불필요**, 상대 경로로 충분

**근본 원인**: 프론트엔드가 OAuth 리다이렉트에 절대 URL을 사용하지만, 프로덕션 Docker 환경에서는 nginx 리버스 프록시가 `/api/*` 요청을 백엔드로 전달. `VITE_API_BASE`가 빌드 시 미설정되면 `localhost:8000` 폴백.

**수정**:

1. `AuthContext.tsx` — OAuth 로그인을 상대 경로로 변경:
   ```tsx
   // Before: window.location.href = `${API_BASE}/api/auth/${provider}`
   // After:  window.location.href = `/api/auth/${provider}`
   ```
   - 이유: nginx가 `/api/*`를 프록시하므로 절대 URL 불필요
   - 로컬 개발: vite dev server의 proxy 설정이 `/api` → `http://localhost:8000` 처리
   - 프로덕션: nginx의 `location /api/` → `proxy_pass http://backend:8000` 처리

2. `AuthCallbackPage.tsx` — exchange 요청도 상대 경로:
   ```tsx
   // API_BASE 제거, 상대 경로 사용
   fetch(`/api/auth/exchange?code=${encodeURIComponent(code)}`, { method: 'POST' })
   ```

3. `api.ts` — `API_BASE` fallback 개선:
   ```ts
   // 빈 문자열 fallback (상대 경로 기본값)
   export const API_BASE: string = import.meta.env.VITE_API_BASE || '';
   ```
   - 기존 `apiFetch()` 호출은 `${API_BASE}${path}` → `"/api/..."` 형태로 작동
   - 로컬 개발에서도 vite proxy가 처리하므로 문제없음

**파일**:
- `jittda/frontend/packages/admin-app/src/contexts/AuthContext.tsx` (수정)
- `jittda/frontend/packages/admin-app/src/pages/AuthCallbackPage.tsx` (수정)
- `jittda/frontend/packages/admin-app/src/lib/api.ts` (수정)

### 13-1: FastAPI Proxy 인식 (Trusted Proxies)

**현재 문제**:
- `auth.py:66` → `redirect_uri = str(request.url_for("google_callback"))`
- Cloudflare Tunnel + nginx 뒤에서 `request.url_for()`가 `http://localhost:8000/...` 생성
- Google/GitHub OAuth callback URL이 잘못됨

**수정**:

1. `main.py` — `ProxyHeadersMiddleware` 추가 (uvicorn 기본 제공):
   ```python
   from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
   application.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
   ```
   - nginx가 이미 `X-Forwarded-For`, `X-Forwarded-Proto`, `Host` 헤더 전달 중
   - 이 미들웨어가 `request.url`을 올바른 외부 URL로 복원

2. `auth.py` — OAuth callback redirect_uri를 명시적으로 구성 (fallback):
   ```python
   def _get_callback_base(request: Request) -> str:
       """프록시 헤더 기반으로 외부 URL base를 결정."""
       proto = request.headers.get("x-forwarded-proto", request.url.scheme)
       host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
       return f"{proto}://{host}"
   ```

**파일**:
- `jittda/backend/src/interface/api/main.py` (수정)
- `jittda/backend/src/interface/api/routes/auth.py` (수정)

### 13-2: nginx OAuth 리다이렉트 경로 프록시

**현재**: nginx가 `/api/`만 프록시. OAuth 리다이렉트 (`/api/auth/google` → Google → `/api/auth/google/callback`)는 `/api/` 하위라 동작하지만, 정확한 동작을 확인.

**수정**:
- nginx.conf에 OAuth callback 경로가 정상 프록시되는지 확인
- 필요 시 `proxy_set_header X-Forwarded-Host $host;` 추가
- Cloudflare Tunnel 동작 E2E 테스트

**파일**:
- `jittda/frontend/nginx.conf` (필요 시 수정)

### 13-3: Docker Frontend 빌드 검증

**현재**: Dockerfile이 `VITE_API_BASE` ARG를 받아 빌드 시 주입. 하지만 13-0에서 상대 경로로 변경하면 이 ARG는 선택적이 됨.

**검증**:
1. `VITE_API_BASE` 없이 빌드 → 상대 경로로 정상 동작 확인
2. `VITE_API_BASE=https://dev.jittda.com` 설정 시에도 정상 동작 확인
3. `docker compose build frontend && docker compose up -d frontend` 전체 플로우 검증
4. `curl https://dev.jittda.com` → nginx SPA 응답 확인
5. OAuth 로그인 플로우 E2E 검증 (Google + GitHub)

**파일**:
- `jittda/docker-compose.yml` (확인)
- `jittda/frontend/Dockerfile` (확인)

### 13-4: OAuth E2E 테스트

**현재**: OAuth 관련 E2E 테스트 없음 (mock 기반 테스트만 존재).

**수정**:
- `tests/e2e/test_oauth_redirect.py` — OAuth 리다이렉트 URL 검증:
  - Google login endpoint가 올바른 redirect_uri 생성하는지
  - GitHub login endpoint가 올바른 redirect_uri 생성하는지
  - ProxyHeaders 미들웨어가 X-Forwarded-* 헤더를 올바르게 처리하는지
  - Exchange endpoint가 정상 동작하는지
- `tests/interface/test_auth_routes.py` 기존 테스트 보강

**파일**:
- `jittda/backend/tests/e2e/test_oauth_redirect.py` (신규)
- `jittda/backend/tests/interface/test_auth_routes.py` (수정)

### 13-5: Obsidian 동기화 + Linear 정리

- Phase 13 변경사항 Obsidian vault 반영
- Linear 이슈 상태 업데이트
- Phase 12 회고 정리

**파일**: Obsidian vault

## 의존관계

```
13-0 (OAuth 리다이렉트 수정) ──→ 13-3 (Docker 검증)
13-1 (Proxy 인식) ──→ 13-2 (nginx 확인) ──→ 13-3 (Docker 검증)
13-4 (테스트) ──→ 13-0, 13-1 완료 후
13-5 (동기화) ──→ 전체 완료 후
```

## 파일 변경 요약

| 유형 | 파일 수 |
|------|--------|
| 수정 (Frontend TSX/TS) | 3 |
| 수정 (Backend Python) | 2 |
| 수정 (nginx.conf, 필요 시) | 1 |
| 신규 (테스트) | 1 |
| 수정 (테스트) | 1 |
| **합계** | **~8** |

## 성공 기준

- [ ] `https://dev.jittda.com/login` → Google 로그인 클릭 → Google OAuth → callback → 토큰 발급 → 대시보드
- [ ] `https://dev.jittda.com/login` → GitHub 로그인 클릭 → GitHub OAuth → callback → 토큰 발급 → 대시보드
- [ ] `request.url_for()` 가 프록시 뒤에서 `https://dev.jittda.com/...` 올바른 URL 생성
- [ ] `VITE_API_BASE` 미설정 시에도 OAuth 플로우 정상 동작 (상대 경로)
- [ ] Docker 전체 빌드 + 기동 성공
- [ ] OAuth E2E 테스트 통과
