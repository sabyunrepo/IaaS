---
name: troubleshoot
description: 버그 수정 및 디버깅. bug, error, fix, debug, traceback, exception 관련 작업 시 사용.
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Troubleshooting Skill

## 디버깅 절차
1. 에러 메시지/트레이스백 분석
2. 관련 코드 읽기 및 재현
3. 근본 원인 식별
4. 수정 적용
5. 회귀 테스트 추가

## 공통 이슈 패턴
- **Temporal Activity 실패**: heartbeat 누락, 타임아웃, 직렬화 오류
- **DB 에러**: 스키마 불일치, 커넥션 풀 고갈, pgvector 차원 불일치
- **Redis 에러**: 연결 거부, 키 만료, 직렬화
- **LLM 에러**: 토큰 초과, rate limit, 응답 파싱 실패
- **프론트엔드**: SSR 불일치, i18n 키 누락, 상태 관리

## 활용 MCP
- `sequential`: 복잡한 원인 분석
- `db`: DB 쿼리 직접 확인
- `docker`: 컨테이너 로그 확인
