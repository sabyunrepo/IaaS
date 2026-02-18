---
title: "Infrastructure Tech Stack"
type: component
layer: crosscutting
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[tech-stack/MOC]]"
depends-on: []
affects: []
linear: JIT-83
tags: [infrastructure, docker, postgres, redis, cloudflare, tech-stack]
---

# Infrastructure Tech Stack

> Docker Compose + PostgreSQL 16 + Redis 7 + Cloudflare Tunnel.
> Clean Slate: Temporal이 존재하지 않는 순수 인프라.

## 핵심 인프라

| 영역 | 기술 | 버전 | 선정 근거 |
|------|------|------|----------|
| **Container** | Docker Compose | v2 | 개발 환경 통일 |
| **DB** | PostgreSQL | 16-alpine | pgvector + LangGraph Checkpoint |
| **Vector Extension** | pgvector | 0.3.6+ | 벡터 검색 |
| **Cache** | Redis | 7-alpine | LLM 캐시, Rate Limit |
| **Quality** | SonarQube | Community | On-Demand (Profile: analysis) |
| **Tunnel** | Cloudflare Tunnel | latest | Zero Trust, 포트 포워딩 불필요 |
| **CI/CD** | GitHub Actions | - | 기존 검증 |

## Docker 이미지 목록

| 이미지 | 용도 | 크기 |
|--------|------|------|
| `python:3.11-slim` | Backend base | ~120MB |
| `node:20-alpine` | Frontend base | ~180MB |
| `postgres:16-alpine` | Database | ~80MB |
| `redis:7-alpine` | Cache | ~30MB |
| `nginx:alpine` | Frontend production | ~23MB |
| `sonarqube:community` | Quality (On-Demand) | ~600MB |
| `cloudflare/cloudflared:latest` | Tunnel | ~50MB |

## PostgreSQL 확장

| 확장 | 용도 |
|------|------|
| `uuid-ossp` | UUID 생성 |
| `vector` | pgvector 벡터 검색 |

## 환경변수 목록

| 변수 | 서비스 | 설명 |
|------|--------|------|
| `DATABASE_URL` | backend | PostgreSQL 연결 |
| `REDIS_URL` | backend | Redis 연결 |
| `LANGGRAPH_CHECKPOINTER_URI` | backend | LangGraph Checkpoint DB |
| `GITHUB_TOKEN` | backend | GitHub API |
| `KIMI_API_KEY` | backend | LLM API |
| `LANGFUSE_HOST` | backend | Langfuse 서버 |
| `LANGFUSE_PUBLIC_KEY` | backend | Langfuse 공개키 |
| `LANGFUSE_SECRET_KEY` | backend | Langfuse 비밀키 |
| `TUNNEL_TOKEN` | cloudflared | Cloudflare Tunnel 토큰 |
| `VITE_API_URL` | frontend | Backend API URL |

## 네트워크 토폴로지

| 네트워크 | 드라이버 | 참여 서비스 |
|---------|--------|-----------|
| `internal_net` | bridge | postgres, redis, backend, frontend, sonarqube |
| `jittda-public` | bridge (external) | cloudflared, frontend |

## 관련 문서

- [[crosscutting/deployment]] -- Docker Compose 배포 상세
- [[crosscutting/security]] -- Cloudflare Zero Trust
- [[tech-stack/version-matrix]] -- 전체 버전 매트릭스
