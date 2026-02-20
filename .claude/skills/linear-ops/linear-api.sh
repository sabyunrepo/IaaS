#!/usr/bin/env bash
# Linear GraphQL API 래퍼
# 사용법: source .claude/skills/linear-ops/linear-api.sh && linear_get_issue "issue-uuid"
#
# 함수 목록:
#   linear_get_issue       "issue-id" (UUID 또는 JIT-26 형식)
#   linear_search_issues   "검색어" [limit]
#   linear_list_issues     [team-uuid] [limit]
#   linear_update_status   "issue-id" "backlog|todo|in_progress|in_review|done|canceled"
#   linear_update_description "issue-id" "설명"
#   linear_create_issue    "제목" "team-uuid" ["설명"] [priority]
#   linear_add_comment     "issue-id" "본문" | @/path/to/file.md
#   linear_list_teams
#   linear_list_projects   [limit]
#
# API 키 우선순위: LINEAR_API_KEY > LINEAR_API_TOKEN > settings.local.json 자동 감지

set -euo pipefail

LINEAR_ENDPOINT="https://api.linear.app/graphql"

_linear_key() {
  # 1. 환경변수 확인
  if [[ -n "${LINEAR_API_KEY:-}" ]]; then
    echo "$LINEAR_API_KEY"
    return
  fi
  if [[ -n "${LINEAR_API_TOKEN:-}" ]]; then
    echo "$LINEAR_API_TOKEN"
    return
  fi

  # 2. settings.local.json에서 자동 추출
  local settings_file="${CLAUDE_SETTINGS_PATH:-/home/sabyun/IaaS/.claude/settings.local.json}"
  if [[ -f "$settings_file" ]]; then
    local key
    key=$(grep -o 'LINEAR_API_KEY=\\"[^"]*\\"' "$settings_file" 2>/dev/null | head -1 | sed 's/LINEAR_API_KEY=\\"//' | sed 's/\\"//')
    if [[ -n "$key" ]]; then
      export LINEAR_API_KEY="$key"
      echo "$key"
      return
    fi
  fi

  echo ""
}

_linear_ensure_key() {
  local key
  key=$(_linear_key)
  if [[ -z "$key" ]]; then
    echo "ERROR: LINEAR_API_KEY 미설정. 환경변수를 설정하거나 settings.local.json을 확인하세요." >&2
    return 1
  fi
}

_linear_gql() {
  _linear_ensure_key || return 1
  # 멀티라인 GraphQL → 한 줄로 압축 후 JSON 전송
  local query
  query=$(echo "$1" | tr '\n' ' ' | sed 's/  */ /g')
  local variables="${2:-null}"
  local payload
  payload=$(jq -n --arg q "$query" --argjson v "$variables" '{query: $q, variables: $v}')
  curl -s -X POST "$LINEAR_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Authorization: $(_linear_key)" \
    --data "$payload"
}

# Issue identifier (JIT-26) → UUID 변환
_linear_resolve_id() {
  local input="$1"
  # UUID 형식이면 그대로 반환
  if [[ "$input" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    echo "$input"
    return
  fi
  # JIT-26 같은 identifier → search로 UUID 추출
  local result
  result=$(linear_search_issues "$input" 1)
  local uuid
  uuid=$(echo "$result" | jq -r '.data.searchIssues.nodes[0].id // empty' 2>/dev/null)
  if [[ -n "$uuid" ]]; then
    echo "$uuid"
  else
    echo "ERROR: '$input' 이슈를 찾을 수 없습니다." >&2
    return 1
  fi
}

# ── Jittda 팀 워크플로우 상태 UUID ──
_linear_state_id() {
  case "$1" in
    backlog)     echo "0427fdcb-12f5-4773-ada5-6c8400b7edfd" ;;
    todo)        echo "3c7a018f-8193-4aa2-bd1a-536ea78e2905" ;;
    in_progress) echo "74296a83-5745-4764-8eb3-9d7b6dfa6bfa" ;;
    in_review)   echo "4cfc961c-7246-48de-a490-8d57f298d9d8" ;;
    done)        echo "ee3386e5-f051-4779-97c0-f45afc6b62fb" ;;
    canceled)    echo "94012442-4212-4a79-82f4-757f07a802e2" ;;
    duplicate)   echo "b499a4fa-9a33-485b-a705-7ad7afbe3082" ;;
    *)           echo "$1" ;;  # UUID 직접 전달도 허용
  esac
}

# ── API 함수 ──

linear_get_issue() {
  local input="$1"
  local issue_id
  issue_id=$(_linear_resolve_id "$input") || return 1
  _linear_gql '
    query($id: String!) {
      issue(id: $id) {
        id identifier title description priority priorityLabel
        state { id name type }
        assignee { id name email }
        creator { id name }
        team { id name key }
        project { id name }
        labels { nodes { id name } }
        comments { nodes { id body createdAt user { name } } }
        url createdAt updatedAt completedAt
        branchName estimate
      }
    }
  ' "$(jq -n --arg id "$issue_id" '{id: $id}')"
}

linear_search_issues() {
  local query="$1"
  local first="${2:-20}"
  _linear_gql '
    query($term: String!, $first: Int) {
      searchIssues(term: $term, first: $first) {
        nodes {
          id identifier title
          state { name }
          assignee { name }
          priority priorityLabel url
        }
      }
    }
  ' "$(jq -n --arg term "$query" --argjson first "$first" '{term: $term, first: $first}')"
}

linear_list_issues() {
  local team_id="${1:-}"
  local first="${2:-50}"
  if [[ -n "$team_id" ]]; then
    _linear_gql '
      query($first: Int, $filter: IssueFilter) {
        issues(first: $first, filter: $filter, orderBy: updatedAt) {
          nodes {
            id identifier title
            state { name }
            assignee { name }
            priority priorityLabel url
          }
        }
      }
    ' "$(jq -n --argjson first "$first" --arg tid "$team_id" '{first: $first, filter: {team: {id: {eq: $tid}}}}')"
  else
    _linear_gql '
      query($first: Int) {
        issues(first: $first, orderBy: updatedAt) {
          nodes {
            id identifier title
            state { name }
            assignee { name }
            priority priorityLabel url
          }
        }
      }
    ' "$(jq -n --argjson first "$first" '{first: $first}')"
  fi
}

linear_update_status() {
  local input="$1"
  local status_key="$2"  # backlog|todo|in_progress|in_review|done|canceled 또는 UUID
  local issue_id
  issue_id=$(_linear_resolve_id "$input") || return 1
  local state_id
  state_id=$(_linear_state_id "$status_key")
  _linear_gql '
    mutation($id: String!, $stateId: String!) {
      issueUpdate(id: $id, input: { stateId: $stateId }) {
        success
        issue { id identifier title state { name } }
      }
    }
  ' "$(jq -n --arg id "$issue_id" --arg sid "$state_id" '{id: $id, stateId: $sid}')"
}

linear_update_description() {
  local input="$1"
  local description="$2"
  local issue_id
  issue_id=$(_linear_resolve_id "$input") || return 1
  _linear_gql '
    mutation($id: String!, $desc: String!) {
      issueUpdate(id: $id, input: { description: $desc }) {
        success
        issue { id identifier title }
      }
    }
  ' "$(jq -n --arg id "$issue_id" --arg desc "$description" '{id: $id, desc: $desc}')"
}

linear_create_issue() {
  local title="$1"
  local team_id="$2"
  local description="${3:-}"
  local priority="${4:-0}"
  _linear_gql '
    mutation($title: String!, $teamId: String!, $desc: String, $priority: Int) {
      issueCreate(input: { title: $title, teamId: $teamId, description: $desc, priority: $priority }) {
        success
        issue { id identifier title url state { name } }
      }
    }
  ' "$(jq -n --arg t "$title" --arg tid "$team_id" --arg d "$description" --argjson p "$priority" '{title: $t, teamId: $tid, desc: $d, priority: $p}')"
}

linear_add_comment() {
  # 이슈에 코멘트 추가
  # 사용법: linear_add_comment "JIT-26" "코멘트 본문"
  #         linear_add_comment "JIT-26" @/tmp/comment.md  (파일에서 읽기)
  local input="$1"
  local body="$2"
  local issue_id
  issue_id=$(_linear_resolve_id "$input") || return 1

  # @파일경로 형식이면 파일에서 읽기
  if [[ "$body" == @* ]]; then
    local file_path="${body#@}"
    body=$(cat "$file_path")
  fi

  # Python으로 JSON 인코딩 (GraphQL ! 이스케이프 문제 우회)
  python3 -c "
import json, subprocess, sys
payload = json.dumps({
    'query': 'mutation(\$id: String!, \$body: String!) { commentCreate(input: { issueId: \$id, body: \$body }) { success comment { id } } }',
    'variables': {'id': sys.argv[1], 'body': sys.argv[2]}
})
r = subprocess.run(['curl', '-s', '-X', 'POST', '$LINEAR_ENDPOINT',
    '-H', 'Content-Type: application/json',
    '-H', 'Authorization: $(echo $(_linear_key))',
    '-d', payload], capture_output=True, text=True)
print(r.stdout)
" "$issue_id" "$body"
}

linear_list_teams() {
  _linear_gql '{ teams { nodes { id name key } } }'
}

linear_list_projects() {
  local first="${1:-50}"
  _linear_gql '
    query($first: Int) {
      projects(first: $first) {
        nodes { id name state }
      }
    }
  ' "$(jq -n --argjson first "$first" '{first: $first}')"
}

# ── Milestone (Project) 함수 ──

linear_create_project() {
  # 프로젝트(마일스톤) 생성
  # Usage: linear_create_project "이름" "team-uuid" ["설명"]
  local name="$1"
  local team_id="$2"
  local description="${3:-}"
  _linear_gql '
    mutation($name: String!, $teamIds: [String!]!, $desc: String) {
      projectCreate(input: { name: $name, teamIds: $teamIds, description: $desc }) {
        success
        project { id name state slugId url }
      }
    }
  ' "$(jq -n --arg n "$name" --arg tid "$team_id" --arg d "$description" '{name: $n, teamIds: [$tid], desc: $d}')"
}

linear_assign_issue_to_project() {
  # 이슈를 프로젝트(마일스톤)에 할당
  # Usage: linear_assign_issue_to_project "issue-id" "project-id"
  local input="$1"
  local project_id="$2"
  local issue_id
  issue_id=$(_linear_resolve_id "$input") || return 1
  _linear_gql '
    mutation($id: String!, $projectId: String!) {
      issueUpdate(id: $id, input: { projectId: $projectId }) {
        success
        issue { id identifier title project { name } }
      }
    }
  ' "$(jq -n --arg id "$issue_id" --arg pid "$project_id" '{id: $id, projectId: $pid}')"
}

linear_list_project_issues() {
  # 프로젝트(마일스톤)의 이슈 목록 조회
  # Usage: linear_list_project_issues "project-id" [limit]
  local project_id="$1"
  local first="${2:-50}"
  _linear_gql '
    query($pid: String!, $first: Int) {
      project(id: $pid) {
        name state
        issues(first: $first) {
          nodes {
            id identifier title
            state { name }
            priority priorityLabel
          }
        }
      }
    }
  ' "$(jq -n --arg pid "$project_id" --argjson first "$first" '{pid: $pid, first: $first}')"
}
