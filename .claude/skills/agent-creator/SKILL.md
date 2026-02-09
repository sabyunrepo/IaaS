---
name: agent-creator
description: 서브에이전트 생성 스킬. 새 프로젝트 전용 서브에이전트를 만들 때 사용.
argument-hint: [agent-name] [purpose]
allowed-tools: Read, Write, Glob
---

# Agent Creator Skill

IaaS 프로젝트용 Claude Code 서브에이전트를 생성합니다.

## 서브에이전트란?

Task 도구로 호출되는 전문화된 AI 에이전트. `.claude/agents/` 디렉토리에 마크다운 파일로 정의.

## 생성 절차

1. 목적과 전문 영역 정의
2. 필요한 도구(tools) 선정 → See `references/available-tools.md`
3. `assets/agent-template.md` 기반으로 에이전트 파일 생성
4. `.claude/agents/{name}.md`에 저장

## 에이전트 설계 원칙

- **단일 책임**: 하나의 전문 영역에 집중 (pipeline-debugger, i18n-checker 등)
- **최소 도구**: 필요한 도구만 선언 (읽기 전용이면 Read, Grep, Glob만)
- **명확한 출력**: Output Format 섹션 필수 (결과를 사람이 읽기 좋게)
- **트리거 정의**: 어떤 키워드/상황에서 호출되는지 명시
- **경량 모델**: 단순 분석은 `model: haiku`, 복잡한 작업은 `model: inherit`

## 기존 에이전트 목록

| 에이전트 | 역할 | 도구 |
|---------|------|------|
| `pipeline-debugger` | Temporal 워크플로우 디버깅 | Read, Grep, Glob, Bash |
| `output-quality-reviewer` | LLM 아웃풋 품질 검증 | Read, Grep, Glob, Bash |
| `prompt-optimizer` | 프롬프트 A/B 테스트 분석 | Read, Write, Edit, Grep, Glob, Bash |
| `frontend-verifier` | Playwright UI 검증 | Read, Grep, Glob, Bash |
| `i18n-checker` | 국제화 완전성 검증 | Read, Grep, Glob |

## 참고
- `references/available-tools.md` — 사용 가능한 도구 목록
- `assets/agent-template.md` — 에이전트 템플릿
