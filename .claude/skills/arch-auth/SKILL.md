---
name: arch-auth
description: OAuth 인증 시스템 구현. OAuth, JWT, API Key, 로그인, 인증, 세션, 토큰 관련 구현 시 사용.
argument-hint: [component] (예: oauth-flow, jwt-middleware, api-key)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Authentication Architecture Skill

OAuth + JWT + API Key 이중 인증 시스템 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/05-api-spec.md` — Section 2: 인증 시스템 전체 설계
2. `docs/architecture/04-infrastructure.md` — 환경 변수 및 Settings 클래스

## 인증 구조 요약

```
React SPA (Vite, port 5173)
  → FastAPI OAuth endpoint (/auth/{provider}/login)
    → Google/GitHub OAuth (httpx-oauth)
      → Callback → JWT 발급
        → Redirect: {FRONTEND_URL}/#token={jwt}
          → React: extractTokenFromCallback()
            → memory 저장 (localStorage 금지)
```

## 핵심 구현 사항

### OAuth Flow (Google, GitHub)
- **라이브러리**: `httpx-oauth` (FastAPI 전용)
- **CSRF 보호**: `state` 파라미터 + `SessionMiddleware` 필수
- **세션**: `starlette.middleware.sessions.SessionMiddleware`
- **access_token 저장**: Fernet 암호화 후 DB 저장 (평문 금지)
- **JWT 발급**: HS256, 24h 만료, claims: sub/email/plan

### JWT Middleware
- `Authorization: Bearer <token>` 헤더에서 추출
- `get_current_user()` 의존성 함수로 주입
- 만료/변조 시 `401 Unauthorized`

### API Key
- 접두사: `vnt_` + 32바이트 hex
- DB 저장: SHA-256 해시 (원문 저장 금지)
- `X-API-Key` 헤더로 전달
- Rate Limit: 100 req/min (Redis 기반)

### 프론트엔드 (React)
- URL fragment `#token=` 에서 JWT 추출
- `history.replaceState()` 로 URL 정리 (히스토리 노출 방지)
- JWT는 **메모리만** 저장 (변수/Context, localStorage 사용 금지)
- `Authorization: Bearer` 헤더에 포함

## 파일 배치
```
backend/app/main.py              — SessionMiddleware 등록
backend/app/api/routes/auth.py   — OAuth 라우트
backend/app/api/deps.py          — get_current_user 의존성
backend/app/core/config.py       — Settings (OAuth/JWT 환경변수)
frontend/src/hooks/useAuth.ts    — JWT 관리 훅
frontend/src/utils/auth.ts       — extractTokenFromCallback
```

## 환경 변수
```
JWT_SECRET, JWT_ALGORITHM=HS256, JWT_EXPIRE_HOURS=24
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
OAUTH_TOKEN_ENCRYPTION_KEY (Fernet)
SESSION_SECRET
FRONTEND_URL=http://localhost:5173
```

## 보안 체크리스트
- [ ] state 파라미터로 CSRF 방지
- [ ] access_token Fernet 암호화 저장
- [ ] JWT URL fragment → history.replaceState 정리
- [ ] datetime.now(UTC) 사용 (utcnow 금지)
- [ ] CORS: 개발/프로덕션 origin 분리
- [ ] Rate limiting (slowapi)
