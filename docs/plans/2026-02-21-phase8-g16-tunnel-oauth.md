# Phase 8 G16: Cloudflare Tunnel + OAuth 연동 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** jittda v5 프론트/백엔드를 Cloudflare 터널을 통해 `dev.jittda.com`으로 외부 접근 가능하게 하고, OAuth + JWT + CORS를 정상 동작시킨다.

**Architecture:** `infra-tunnel/`의 cloudflared가 사용하는 `jittda-public` 네트워크에 `jittda/` 컨테이너를 연결. nginx에 `/auth/`, `/ws/` 프록시 추가. 환경변수에 OAuth 실제값 설정.

**Tech Stack:** Docker Compose (external networks), Nginx (reverse proxy), Cloudflare Tunnel, OAuth 2.0 (Google+GitHub), JWT

**Linear:** JIT-302, JIT-303

---

## 사전 조건

- `infra-tunnel/docker-compose.yml`에 `jittda-public` 네트워크 이미 정의됨
- `jittda/backend/src/interface/api/routes/auth.py`에 OAuth 엔드포인트 이미 구현됨
- `jittda/backend/src/interface/api/routes/jobs.py`에 WebSocket 엔드포인트 이미 구현됨

---

### Task 1: docker-compose.yml에 외부 네트워크 추가 (JIT-302)

`jittda/docker-compose.yml`에 `jittda-public` 외부 네트워크를 추가하여 cloudflared와 통신 가능하게 한다.

**Files:**
- Modify: `jittda/docker-compose.yml`

**Step 1: 현재 docker-compose.yml 읽기**

```bash
cat jittda/docker-compose.yml
```

**Step 2: networks 섹션에 외부 네트워크 추가**

`networks:` 섹션 끝에 추가:
```yaml
networks:
  internal_net:
    driver: bridge
  jittda-public:
    external: true
```

**Step 3: frontend 서비스에 jittda-public 네트워크 추가**

frontend 서비스의 `networks:` 배열에 `jittda-public` 추가:
```yaml
  frontend:
    networks:
      - internal_net
      - jittda-public
```

**Step 4: backend 서비스에 jittda-public 네트워크 추가**

backend 서비스의 `networks:` 배열에 `jittda-public` 추가:
```yaml
  backend:
    networks:
      - internal_net
      - jittda-public
```

**Verification:**
```bash
cd jittda && docker compose config --quiet && echo "VALID"
```

Expected: VALID (설정 문법 검증)

---

### Task 2: nginx.conf에 /auth/ 및 /ws/ 프록시 추가 (JIT-302)

nginx 리버스 프록시에 OAuth 콜백과 WebSocket 경로를 추가한다.

**Files:**
- Modify: `jittda/frontend/nginx.conf`

**Step 1: 현재 nginx.conf 읽기**

```bash
cat jittda/frontend/nginx.conf
```

**Step 2: /auth/ 프록시 블록 추가**

`/api/` location 블록 아래에 추가:
```nginx
    location /auth/ {
        proxy_pass http://backend:8000/auth/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

**Step 3: /ws/ WebSocket 프록시 블록 추가**

```nginx
    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
```

**Step 4: 기존 /api/ 블록에 X-Forwarded-* 헤더 추가**

기존 `/api/` location 블록에 누락된 헤더 추가:
```nginx
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

**Verification:**
```bash
docker run --rm -v $(pwd)/jittda/frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t
```

Expected: syntax is ok, test is successful

---

### Task 3: Frontend Dockerfile에 VITE_API_BASE 빌드 인자 추가 (JIT-303)

프론트엔드 빌드 시 API base URL을 주입할 수 있게 한다.

**Files:**
- Modify: `jittda/frontend/Dockerfile`

**Step 1: 현재 Dockerfile 읽기**

```bash
cat jittda/frontend/Dockerfile
```

**Step 2: VITE_API_BASE ARG + ENV 추가**

기존 `ARG APP=admin-app` 다음에 추가:
```dockerfile
ARG VITE_API_BASE=""
ENV VITE_API_BASE=${VITE_API_BASE}
```

**Step 3: docker-compose.yml에서 빌드 인자 전달**

`jittda/docker-compose.yml`의 frontend build args에 추가:
```yaml
  frontend:
    build:
      args:
        APP: admin-app
        VITE_API_BASE: ${VITE_API_BASE:-}
```

**Verification:**
```bash
cd jittda && docker compose config --quiet && echo "VALID"
```

---

### Task 4: .env.example 업데이트 + .env 터널 변수 추가 (JIT-303)

Cloudflare 터널 관련 환경변수를 .env.example에 문서화하고, .env에 필요한 변수를 추가한다.

**Files:**
- Modify: `jittda/.env.example`
- Modify: `jittda/.env` (보안 값은 플레이스홀더)

**Step 1: .env.example에 터널 관련 변수 추가**

```bash
cat jittda/.env.example
```

기존 Auth 섹션 아래에 추가:
```env
# --- Tunnel/External Access ---
VITE_API_BASE=https://dev.jittda.com
FRONTEND_URL=https://dev.jittda.com
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3000,https://dev.jittda.com
```

**Step 2: .env에 ALLOWED_ORIGINS 업데이트**

`.env`의 기존 환경변수에 추가 (OAuth 실제값은 사용자가 별도 설정):
```env
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3000,https://dev.jittda.com
FRONTEND_URL=https://dev.jittda.com
```

**Verification:**
```bash
grep -c "ALLOWED_ORIGINS\|FRONTEND_URL\|VITE_API_BASE" jittda/.env.example
```

Expected: 3 (3개 변수 존재)

---

### Task 5: Docker 설정 통합 검증 + Linear 업데이트

전체 설정이 올바른지 검증하고 Linear 이슈를 Done으로 변경한다.

**Files:** (변경 없음 - 검증만)

**Step 1: docker compose config 검증**

```bash
cd jittda && docker compose config --quiet && echo "CONFIG VALID"
```

**Step 2: nginx 설정 검증**

```bash
docker run --rm -v $(pwd)/jittda/frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t
```

**Step 3: .env.example 완전성 검증**

```bash
# .env.example의 모든 변수가 .env에도 있는지 확인
diff <(grep -oP '^[A-Z_]+=' jittda/.env.example | sort) <(grep -oP '^[A-Z_]+=' jittda/.env | sort)
```

**Step 4: Linear 이슈 상태 업데이트**

```bash
source .claude/skills/linear-ops/linear-api.sh
linear_update_status "JIT-302" "done"
linear_update_status "JIT-303" "done"
```

**Step 5: pipeline-state.json 업데이트**

```json
{
  "current_phase": 8,
  "step": "sync_completed",
  "sync_completed_at": "2026-02-21T..."
}
```
