---
name: improve
description: 성능 최적화 및 개선. performance, 성능, 최적화, optimize, bottleneck, 병목 관련 작업 시 사용.
argument-hint: [--perf] [target]
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Performance Improvement Skill

## 최적화 절차
1. 병목 지점 식별 (프로파일링, 로그 분석)
2. 측정 가능한 기준선 설정
3. 최적화 적용
4. 성능 비교 측정
5. 트레이드오프 문서화

## 영역별 최적화

### Backend
- DB 쿼리 최적화 (EXPLAIN ANALYZE, 인덱스)
- N+1 쿼리 제거
- Redis 캐싱 전략
- 비동기 처리 활용
- LLM 호출 캐시 (CachedLLMService)

### Frontend
- 번들 크기 최적화
- 렌더링 성능 (React.memo, useMemo)
- 이미지/에셋 최적화
- 코드 스플리팅

### Infrastructure
- Docker 이미지 최적화
- 연결 풀 튜닝
- Temporal 워커 설정 최적화

## 활용 MCP
- `sequential`: 병목 분석
- `playwright`: 프론트엔드 성능 측정
