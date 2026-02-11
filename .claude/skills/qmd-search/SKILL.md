---
name: qmd-search
description: QMD 코드 인덱스 시맨틱 검색. 코드 탐색 시 전체 파일 Read 대신 관련 청크만 조회하여 토큰 절감.
allowed-tools: Bash, Read, Grep, Glob
---

# QMD Code Search Skill

> 프로젝트 코드를 시맨틱 검색하여 관련 800토큰 청크만 반환. Read 대비 80-93% 토큰 절감.

## 컬렉션

| Name | Path | Content |
|------|------|---------|
| vantict-backend | backend/ | Python + YAML (32K+ lines) |
| vantict-frontend | frontend/ | TS/TSX (9.8K lines) |
| vantict-docs | docs/ | Markdown (17.5K lines) |

## 검색 명령어

| 명령 | 용도 | 속도 |
|------|------|------|
| `qmd search "<query>" -c <collection>` | BM25 키워드 검색 | 빠름 |
| `qmd vsearch "<query>" -c <collection>` | 벡터 시맨틱 검색 | 보통 |
| `qmd query "<query>"` | 하이브리드 + reranking (최고 품질) | 느림 |
| `qmd get "<path>"` | 특정 파일/청크 조회 | 즉시 |

## 도구 선택 기준 (QMD vs Grep vs Read)

| 상황 | 우선 도구 | 이유 |
|------|----------|------|
| 의미 검색 ("X가 뭐 하는 코드?") | `qmd search` | 시맨틱 매칭, 800토큰 청크 |
| 복잡 탐색 ("Y 동작 흐름") | `qmd query` | 멀티홉 + reranking |
| 정확 패턴 ("CachedLLMService") | Grep | 정규식 정밀 매칭 |
| 전체 파일 필요 | Read | 완전한 컨텍스트 |
| 외부 라이브러리 문서 | context7 | QMD는 내부 코드만 |
| QMD 결과 → 상세 확인 | qmd get → Read(offset) | 단계적 확장 |

## 사용 패턴

### 패턴 1: 시맨틱 코드 검색
```bash
qmd search "scoring formula calculation" -c vantict-backend -n 5
```

### 패턴 2: 컬렉션 지정 검색
```bash
# 백엔드만
qmd search "error handling" -c vantict-backend
# 프론트엔드만
qmd vsearch "chart component" -c vantict-frontend
# 문서만
qmd search "workflow phases" -c vantict-docs
```

### 패턴 3: 딥 서치 (복잡 질문)
```bash
qmd query "how does the interview workflow handle LLM failures"
```

### 패턴 4: 특정 파일 조회
```bash
qmd get "backend/app/services/scoring_formulas.py" --full --line-numbers
```

## 출력 형식 옵션
- `--json` : JSON 출력 (파싱용)
- `--md` : 마크다운 출력
- `--line-numbers` : 줄번호 포함
- `--full` : 전체 내용 (청크 아님)
- `-n <num>` : 결과 수 제한

## 유지보수 (수동만)
- 재인덱싱: `qmd update && qmd embed`
- 상태 확인: `qmd status`
- NEVER: 자동으로 `qmd collection add`, `qmd embed`, `qmd update` 실행 금지
