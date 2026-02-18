---
name: obsidian-api
description: Obsidian Local REST API 래퍼. Vault CRUD, 검색, 디렉토리 동기화를 셸 함수로 제공.
argument-hint: [status | get | put | list | search | sync]
allowed-tools: Bash, Read, Write
---

# Obsidian-API Skill

> Obsidian Local REST API (v3.4.3)를 활용하여 **Vault 파일 CRUD, 검색, 디렉토리 동기화**를 수행한다.

---

## 셋업

```bash
source /Users/sabyun/goinfre/IaaS/.claude/skills/obsidian-api/obsidian-api.sh
```

API 키와 포트는 자동 설정됨 (HTTPS 27124, self-signed cert).

### 전제 조건
- Obsidian 앱 실행 중
- Community Plugin **"Local REST API"** 활성화
- 서버 확인: `obsidian_status`

---

## 주요 함수

| 함수 | 용도 | 예시 |
|------|------|------|
| `obsidian_status` | 서버 상태 확인 | `obsidian_status` |
| `obsidian_vault_get` | 파일 읽기 | `obsidian_vault_get "MOC.md"` |
| `obsidian_vault_put` | 파일 생성/덮어쓰기 | `obsidian_vault_put "note.md" "# Title"` |
| `obsidian_vault_append` | 파일 끝에 추가 | `obsidian_vault_append "log.md" "- entry"` |
| `obsidian_vault_delete` | 파일 삭제 | `obsidian_vault_delete "old.md"` |
| `obsidian_vault_list` | 디렉토리 목록 | `obsidian_vault_list "domain/"` |
| `obsidian_search` | Dataview DQL 검색 | `obsidian_search "TABLE file.name FROM #moc"` |
| `obsidian_search_simple` | 텍스트 검색 | `obsidian_search_simple "identity" 200` |
| `obsidian_active_get` | 현재 열린 파일 읽기 | `obsidian_active_get` |
| `obsidian_active_put` | 현재 열린 파일 교체 | `obsidian_active_put "new content"` |
| `obsidian_commands` | 커맨드 목록 | `obsidian_commands` |
| `obsidian_run_command` | 커맨드 실행 | `obsidian_run_command "app:reload"` |
| `obsidian_open` | Obsidian UI에서 열기 | `obsidian_open "domain/MOC.md"` |

---

## 파일 기반 입력 (대용량)

`@` 접두사로 로컬 파일에서 내용을 읽어 전송:

```bash
# 로컬 파일 → Vault
obsidian_vault_put "architecture/MOC.md" @/tmp/moc.md

# 로컬 파일을 Vault에 업로드
obsidian_vault_put_file "/Users/sabyun/goinfre/IaaS/docs/architecture/MOC.md" "architecture/MOC.md"
```

---

## 디렉토리 동기화

로컬 `docs/architecture/` 전체를 Obsidian Vault에 동기화:

```bash
# 로컬 docs/architecture/ → Vault의 architecture/ 경로
obsidian_sync_dir "/Users/sabyun/goinfre/IaaS/docs/architecture" "architecture"

# Vault 루트에 직접 동기화
obsidian_sync_dir "/Users/sabyun/goinfre/IaaS/docs/architecture"
```

---

## 활용 시나리오

### 1. 아키텍처 문서 → Obsidian Vault 동기화
```bash
source .claude/skills/obsidian-api/obsidian-api.sh
obsidian_status
obsidian_sync_dir "/Users/sabyun/goinfre/IaaS/docs/architecture"
```

### 2. 특정 문서 업데이트
```bash
obsidian_vault_put "domain/identity-resolution/MOC.md" @docs/architecture/domain/identity-resolution/MOC.md
```

### 3. Vault 내용 검색
```bash
obsidian_search_simple "BlameFilter" 200
obsidian_search "TABLE file.name, layer FROM \"\" WHERE type = \"component\""
```

### 4. Obsidian에서 파일 열기
```bash
obsidian_open "decisions/0001-langgraph-over-temporal.md"
```

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| 서버 미응답 (exit 7) | Obsidian 앱 실행 + 플러그인 활성화 확인 |
| 401 Unauthorized | API 키 확인 (`data.json`의 apiKey) |
| 404 Not Found | 경로 확인 (Vault 내 상대 경로) |
| 파일 이미 존재 (PUT) | 덮어쓰기됨 (주의) |
| 대용량 파일 | `@file` 접두사 사용 |

---

## Vault 정보

| 항목 | 값 |
|------|---|
| Vault 경로 | `/Users/sabyun/Documents/Obsidian Vault` |
| API 포트 | 27124 (HTTPS, self-signed) |
| 플러그인 버전 | 3.4.3 |
