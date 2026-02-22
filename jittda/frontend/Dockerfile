# jittda/frontend/Dockerfile
# ARG로 빌드 대상 선택
ARG APP=admin-app

# Stage 1: Build
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json tsconfig.base.json ./
COPY packages/ packages/
RUN pnpm install --frozen-lockfile
ARG APP
ARG VITE_API_BASE=""
ENV VITE_API_BASE=${VITE_API_BASE}
RUN pnpm --filter "./packages/${APP}" build

# Stage 2: Serve
FROM nginx:alpine
ARG APP
COPY --from=builder /app/packages/${APP}/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
