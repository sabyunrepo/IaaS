#!/usr/bin/env bash
# Obsidian Local REST API Shell Wrapper
# Usage: source /Users/sabyun/goinfre/IaaS/.claude/skills/obsidian-api/obsidian-api.sh

# ─── Configuration ─────────────────────────────────────────────
OBSIDIAN_API_KEY="${OBSIDIAN_API_KEY:-d9d0f6e22d569d7cae2a55948971755b1aa9cbea955c5022b98bc775f27703d0}"
OBSIDIAN_PORT="${OBSIDIAN_PORT:-27124}"
OBSIDIAN_HOST="${OBSIDIAN_HOST:-127.0.0.1}"
OBSIDIAN_BASE="https://${OBSIDIAN_HOST}:${OBSIDIAN_PORT}"

# ─── Internal Helpers ──────────────────────────────────────────
_obsidian_curl() {
  local method="$1" path="$2"
  shift 2
  /usr/bin/curl -sk -X "$method" \
    -H "Authorization: Bearer ${OBSIDIAN_API_KEY}" \
    "$@" \
    "${OBSIDIAN_BASE}${path}"
}

# ─── Status ────────────────────────────────────────────────────
obsidian_status() {
  # 서버 상태 확인 (인증 상태 포함)
  _obsidian_curl GET "/" -H "Accept: application/json" 2>/dev/null
  local rc=$?
  if [ $rc -ne 0 ]; then
    echo '{"error":"Obsidian REST API 서버에 연결할 수 없습니다. Obsidian 앱에서 Local REST API 플러그인이 활성화되어 있는지 확인하세요."}' >&2
    return 1
  fi
}

# ─── Vault: Read ───────────────────────────────────────────────
obsidian_vault_get() {
  # 파일 내용 읽기
  # Usage: obsidian_vault_get "path/to/note.md"
  local filepath="$1"
  if [ -z "$filepath" ]; then
    echo "Usage: obsidian_vault_get <filepath>" >&2; return 1
  fi
  _obsidian_curl GET "/vault/$(python3 -c "import urllib.parse; print(urllib.parse.quote('$filepath', safe='/'))")" \
    -H "Accept: text/markdown"
}

# ─── Vault: Create / Update ───────────────────────────────────
obsidian_vault_put() {
  # 파일 생성 또는 덮어쓰기
  # Usage: obsidian_vault_put "path/to/note.md" "content" OR obsidian_vault_put "path/to/note.md" @/tmp/file.md
  local filepath="$1" content="$2"
  if [ -z "$filepath" ] || [ -z "$content" ]; then
    echo "Usage: obsidian_vault_put <filepath> <content|@file>" >&2; return 1
  fi
  local encoded
  encoded="$(python3 -c "import urllib.parse; print(urllib.parse.quote('$filepath', safe='/'))")"
  if [[ "$content" == @* ]]; then
    _obsidian_curl PUT "/vault/${encoded}" \
      -H "Content-Type: text/markdown" \
      --data-binary "$content"
  else
    _obsidian_curl PUT "/vault/${encoded}" \
      -H "Content-Type: text/markdown" \
      -d "$content"
  fi
}

# ─── Vault: Append ─────────────────────────────────────────────
obsidian_vault_append() {
  # 파일 끝에 내용 추가 (파일 없으면 생성)
  # Usage: obsidian_vault_append "path/to/note.md" "content" OR @file
  local filepath="$1" content="$2"
  if [ -z "$filepath" ] || [ -z "$content" ]; then
    echo "Usage: obsidian_vault_append <filepath> <content|@file>" >&2; return 1
  fi
  local encoded
  encoded="$(python3 -c "import urllib.parse; print(urllib.parse.quote('$filepath', safe='/'))")"
  if [[ "$content" == @* ]]; then
    _obsidian_curl POST "/vault/${encoded}" \
      -H "Content-Type: text/markdown" \
      --data-binary "$content"
  else
    _obsidian_curl POST "/vault/${encoded}" \
      -H "Content-Type: text/markdown" \
      -d "$content"
  fi
}

# ─── Vault: Delete ─────────────────────────────────────────────
obsidian_vault_delete() {
  # 파일 삭제
  # Usage: obsidian_vault_delete "path/to/note.md"
  local filepath="$1"
  if [ -z "$filepath" ]; then
    echo "Usage: obsidian_vault_delete <filepath>" >&2; return 1
  fi
  _obsidian_curl DELETE "/vault/$(python3 -c "import urllib.parse; print(urllib.parse.quote('$filepath', safe='/'))")"
}

# ─── Vault: List Directory ─────────────────────────────────────
obsidian_vault_list() {
  # 디렉토리 파일 목록 (비워두면 루트)
  # Usage: obsidian_vault_list ["path/to/dir/"]
  local dirpath="${1:-}"
  if [ -n "$dirpath" ]; then
    # 슬래시로 끝나야 함
    [[ "$dirpath" != */ ]] && dirpath="${dirpath}/"
    _obsidian_curl GET "/vault/$(python3 -c "import urllib.parse; print(urllib.parse.quote('$dirpath', safe='/'))")" \
      -H "Accept: application/json"
  else
    _obsidian_curl GET "/vault/" -H "Accept: application/json"
  fi
}

# ─── Search ────────────────────────────────────────────────────
obsidian_search() {
  # Dataview DQL 검색
  # Usage: obsidian_search "TABLE file.name FROM #tag"
  local query="$1"
  if [ -z "$query" ]; then
    echo "Usage: obsidian_search <dataview-query>" >&2; return 1
  fi
  _obsidian_curl POST "/search/" \
    -H "Content-Type: application/vnd.olrapi.dataview.dql+txt" \
    -H "Accept: application/json" \
    -d "$query"
}

obsidian_search_simple() {
  # 단순 텍스트 검색 (contextLength로 주변 텍스트 포함)
  # Usage: obsidian_search_simple "검색어" [contextLength]
  local query="$1" context="${2:-100}"
  if [ -z "$query" ]; then
    echo "Usage: obsidian_search_simple <query> [contextLength]" >&2; return 1
  fi
  local encoded_query
  encoded_query="$(python3 -c "import urllib.parse; print(urllib.parse.quote('$query'))")"
  _obsidian_curl POST "/search/simple/?query=${encoded_query}&contextLength=${context}" \
    -H "Content-Type: text/plain" \
    -H "Accept: application/json"
}

# ─── Active File ───────────────────────────────────────────────
obsidian_active_get() {
  # 현재 열린 파일 내용 읽기
  _obsidian_curl GET "/active/" -H "Accept: text/markdown"
}

obsidian_active_put() {
  # 현재 열린 파일 내용 교체
  # Usage: obsidian_active_put "new content" OR @file
  local content="$1"
  if [ -z "$content" ]; then
    echo "Usage: obsidian_active_put <content|@file>" >&2; return 1
  fi
  if [[ "$content" == @* ]]; then
    _obsidian_curl PUT "/active/" -H "Content-Type: text/markdown" --data-binary "$content"
  else
    _obsidian_curl PUT "/active/" -H "Content-Type: text/markdown" -d "$content"
  fi
}

# ─── Commands ──────────────────────────────────────────────────
obsidian_commands() {
  # 사용 가능한 커맨드 목록
  _obsidian_curl GET "/commands/" -H "Accept: application/json"
}

obsidian_run_command() {
  # 커맨드 실행
  # Usage: obsidian_run_command "command-id"
  local cmd_id="$1"
  if [ -z "$cmd_id" ]; then
    echo "Usage: obsidian_run_command <command-id>" >&2; return 1
  fi
  _obsidian_curl POST "/commands/${cmd_id}/"
}

# ─── Open File in Obsidian UI ──────────────────────────────────
obsidian_open() {
  # Obsidian UI에서 파일 열기
  # Usage: obsidian_open "path/to/note.md"
  local filepath="$1"
  if [ -z "$filepath" ]; then
    echo "Usage: obsidian_open <filepath>" >&2; return 1
  fi
  _obsidian_curl POST "/open/$(python3 -c "import urllib.parse; print(urllib.parse.quote('$filepath', safe='/'))")"
}

# ─── Batch: Put from file ──────────────────────────────────────
obsidian_vault_put_file() {
  # 로컬 파일을 Obsidian vault에 업로드
  # Usage: obsidian_vault_put_file "local/path.md" "vault/path.md"
  local local_path="$1" vault_path="$2"
  if [ -z "$local_path" ] || [ -z "$vault_path" ]; then
    echo "Usage: obsidian_vault_put_file <local-path> <vault-path>" >&2; return 1
  fi
  if [ ! -f "$local_path" ]; then
    echo "Error: 파일이 존재하지 않습니다: $local_path" >&2; return 1
  fi
  obsidian_vault_put "$vault_path" "@${local_path}"
}

# ─── Batch: Sync directory ─────────────────────────────────────
obsidian_sync_dir() {
  # 로컬 디렉토리의 .md 파일을 Obsidian vault에 동기화
  # Usage: obsidian_sync_dir "local/dir" "vault/prefix"
  local local_dir="$1" vault_prefix="${2:-}"
  if [ -z "$local_dir" ]; then
    echo "Usage: obsidian_sync_dir <local-dir> [vault-prefix]" >&2; return 1
  fi
  local count=0 failed=0
  while IFS= read -r -d '' file; do
    local rel_path="${file#${local_dir}/}"
    local vault_path="${vault_prefix:+${vault_prefix}/}${rel_path}"
    if obsidian_vault_put_file "$file" "$vault_path" >/dev/null 2>&1; then
      ((count++))
    else
      echo "FAIL: $rel_path" >&2
      ((failed++))
    fi
  done < <(find "$local_dir" -name "*.md" -print0)
  echo "동기화 완료: ${count}개 성공, ${failed}개 실패"
}
