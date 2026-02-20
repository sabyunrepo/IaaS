# Frontend + Landing Page Production Dockerfile
# Multi-stage build: Landing page + Frontend SPA → single Nginx container

# ============================================
# Stage 1: Landing Page Build
# ============================================
FROM node:20-alpine AS landing-builder

WORKDIR /app

COPY jittda-landingpage/package.json jittda-landingpage/package-lock.json* ./
RUN npm ci || npm install

COPY jittda-landingpage/ .
RUN npm run build

# ============================================
# Stage 2: Frontend App Build
# ============================================
FROM node:20-alpine AS app-builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* frontend/yarn.lock* frontend/pnpm-lock.yaml* ./
RUN npm ci || npm install

COPY frontend/ .
RUN npm run build

# ============================================
# Stage 3: Production (Nginx)
# ============================================
FROM nginx:alpine

# Landing page → html 루트 (jittda.com/)
COPY --from=landing-builder /app/dist /usr/share/nginx/html

# Frontend app → /demo 서브디렉토리 (jittda.com/demo)
COPY --from=app-builder /app/dist /usr/share/nginx/html/demo

# Nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
