# Architecture Vault 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `docs/architecture/` Obsidian Vault에 ~77개 아키텍처 문서를 7 Wave로 작성한다.

**Architecture:** DDD 4계층(domain/application/infrastructure/interface) 기반 Obsidian Vault. YAML frontmatter로 관계 매핑, Dataview로 자동 인덱싱, Mermaid로 의존성 그래프 시각화.

**Tech Stack:** Obsidian + Markdown + YAML frontmatter + Mermaid + Dataview

**설계 문서:** `docs/plans/2026-02-19-architecture-documentation-design.md`
**소스 자료:**
- `plan/v5-design/phase0-scaffolding.md` ~ `phase6-testing.md`
- `plan/2026-02-15-v5-final-design.md`
- `jittda_doc/jittda_live_brainstorm_curated.md`
- `jittda_doc/jittda-v5-brainstorming-log.md`
- `jittda_doc/jittda_reveiw.md`

**규칙:**
1. 항상 frontmatter 먼저 — 관계 매핑이 내용보다 우선
2. MOC는 Dataview 쿼리로만 — 수동 목차 금지
3. 코드 예시 필수 — 추상 설명만 금지
4. ADR wikilink 필수 — 모든 설계 결정에 연결
5. Wave별 Git 커밋

---

## Wave 1: 골격 구조 (8개 파일)

### Task 1: 디렉토리 생성 + Obsidian 설정

**Files:**
- Create: `docs/architecture/.obsidian/community-plugins.json`
- Create: `docs/architecture/.obsidian/app.json`

**Step 1: 디렉토리 구조 생성**

```bash
mkdir -p docs/architecture/{.obsidian,domain/{identity-resolution,scoring-system,funnel-selection,question-generation,linkedin-profile},application/{hmas-graph,live-session,state-management,quality-gate},infrastructure/{git-adapter,github-client,tree-sitter-ast,complexity-analysis,plagiarism-detection,llm-instructor,vector-search,linkedin-adapter,voice-pipeline},interface/{rest-api,websocket,electron-app,d3-charts},decisions,crosscutting,tech-stack,templates}
```

**Step 2: Obsidian 설정 파일 작성**

`docs/architecture/.obsidian/community-plugins.json`:
```json
["dataview", "templater-obsidian", "obsidian-git", "folder-note-core", "obsidian-local-rest-api"]
```

`docs/architecture/.obsidian/app.json`:
```json
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "showFrontmatter": true
}
```

**Step 3: 확인**

Run: `find docs/architecture -type d | head -30`
Expected: 모든 하위 디렉토리 존재 확인

---

### Task 2: 템플릿 파일 (3개)

**Files:**
- Create: `docs/architecture/templates/moc-template.md`
- Create: `docs/architecture/templates/component-template.md`
- Create: `docs/architecture/templates/adr-template.md`

**Step 1: MOC 템플릿**

`docs/architecture/templates/moc-template.md`:
```markdown
---
title: "{{title}}"
type: moc
layer: "{{layer}}"
status: draft
created: {{date}}
updated: {{date}}
---

# {{title}}

## 개요

> 이 계층의 역할과 책임을 1-2문장으로 설명.

## 문서 목록

\`\`\`dataview
TABLE status, updated, tags
FROM "{{folder}}"
WHERE file.name != "MOC"
SORT file.name ASC
\`\`\`

## 관련 ADR

\`\`\`dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
\`\`\`
```

**Step 2: 컴포넌트 문서 템플릿**

`docs/architecture/templates/component-template.md`:
```markdown
---
title: "{{title}}"
type: "{{type}}"
status: draft
created: {{date}}
updated: {{date}}
tags: []
parent: "{{parent}}"
children: []
depends-on: []
affects: []
linear: []
phase: 0
---

# {{title}}

## 개요

> 이 컴포넌트의 목적과 역할을 2-3문장으로 설명.

## 상세 설계

### 핵심 개념

### 데이터 모델

### 코드 예시

```python
# 핵심 로직 예시
```

## 관련 문서

- 상위: {{parent}}
- 의존: (depends-on 목록)
- 영향: (affects 목록)
```

**Step 3: ADR 템플릿 (MADR v4)**

`docs/architecture/templates/adr-template.md`:
```markdown
---
title: "ADR-NNNN: {{title}}"
type: adr
status: proposed
date: {{date}}
decision-makers: ["@sabyun"]
supersedes: []
superseded-by: []
related-adrs: []
impacts: []
tags: []
---

# ADR-NNNN: {{title}}

## 상태

Proposed

## 컨텍스트

> 이 결정이 필요한 배경과 문제 상황.

## 고려한 옵션

### 옵션 A: {{option_a}}

- 장점: ...
- 단점: ...

### 옵션 B: {{option_b}}

- 장점: ...
- 단점: ...

## 결정

> 선택한 옵션과 이유.

## 결과

> 이 결정으로 인한 영향과 후속 조치.
```

---

### Task 3: 루트 MOC + RELATION-MAP

**Files:**
- Create: `docs/architecture/MOC.md`
- Create: `docs/architecture/RELATION-MAP.md`

**Step 1: 루트 MOC**

`docs/architecture/MOC.md`:
```markdown
---
title: "Jittda v5.0 Architecture"
type: moc
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Jittda v5.0 Architecture

> AI 면접 스크립트 생성기. v5.0 HMAS + Jittda Live 통합 아키텍처.

## DDD 4계층

| 계층 | 역할 | 진입점 |
|------|------|--------|
| [[domain/MOC\|Domain]] | 순수 비즈니스 로직 (외부 의존성 0) | Identity, Scoring, Funnel, Questions |
| [[application/MOC\|Application]] | LangGraph 오케스트레이션 | HMAS Graph, Live Session, State |
| [[infrastructure/MOC\|Infrastructure]] | 외부 서비스 어댑터 | Git, GitHub, AST, LLM, Vector |
| [[interface/MOC\|Interface]] | API + UI | REST, WebSocket, Electron, D3 |

## 횡단 관심사

- [[decisions/MOC\|Decisions (ADR)]] — 아키텍처 결정 기록
- [[crosscutting/MOC\|Crosscutting]] — 보안, 성능, 배포, 테스트
- [[tech-stack/MOC\|Tech Stack]] — 기술 스택 레지스트리
- [[RELATION-MAP]] — 전체 의존성 그래프

## 최근 업데이트

\`\`\`dataview
TABLE status, updated, type
FROM "docs/architecture"
WHERE file.name != "MOC" AND type != "moc"
SORT file.mtime DESC
LIMIT 15
\`\`\`

## 문서 현황

\`\`\`dataview
TABLE length(rows) as "문서 수"
FROM "docs/architecture"
WHERE type != "moc"
GROUP BY type
\`\`\`
```

**Step 2: RELATION-MAP**

소스: 설계 문서 섹션 8의 Mermaid 그래프를 `docs/architecture/RELATION-MAP.md`에 그대로 작성.
frontmatter: `title: "Relation Map"`, `type: crosscutting`, `status: draft`
내용: 설계 문서의 Mermaid 그래프 + 범례 테이블.

---

### Task 4: 계층별 MOC (4개)

**Files:**
- Create: `docs/architecture/domain/MOC.md`
- Create: `docs/architecture/application/MOC.md`
- Create: `docs/architecture/infrastructure/MOC.md`
- Create: `docs/architecture/interface/MOC.md`

각 MOC의 구조:
```yaml
---
title: "{{Layer}} Layer"
type: moc
layer: "{{layer}}"
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[MOC]]"
---
```

본문: 해당 계층의 DDD 역할 설명 (1-2문장) + Dataview 쿼리로 하위 문서 자동 목록.

**소스 참조:**
- Domain: `plan/v5-design/phase1-domain.md` 서두
- Application: `plan/v5-design/phase3-application.md` 서두
- Infrastructure: `plan/v5-design/phase2-infrastructure.md` 서두
- Interface: `plan/v5-design/phase5-output-frontend.md` 서두

**Step 5: 확인 + 커밋**

```bash
find docs/architecture -name "*.md" | wc -l
# Expected: 8개 (3 템플릿 + MOC + RELATION-MAP + 4 계층 MOC)
git add docs/architecture/
git commit -m "docs: Wave 1 — Obsidian Vault 골격 구조 생성"
```

---

## Wave 2: ADR 핵심 결정 (11개 파일)

### Task 5: ADR MOC + 템플릿

**Files:**
- Create: `docs/architecture/decisions/MOC.md`

frontmatter: `type: moc`, `layer: decisions`, `parent: "[[MOC]]"`
본문: Dataview ADR 대시보드 — 설계 문서 섹션 4의 "ADR 대시보드" 쿼리 사용.

---

### Task 6: ADR 0001~0005 (핵심 아키텍처 결정)

**Files:**
- Create: `docs/architecture/decisions/0001-langgraph-over-temporal.md`
- Create: `docs/architecture/decisions/0002-clean-slate-not-migration.md`
- Create: `docs/architecture/decisions/0003-ddd-four-layers.md`
- Create: `docs/architecture/decisions/0004-reference-passing.md`
- Create: `docs/architecture/decisions/0005-instructor-pydantic.md`

각 ADR은 MADR v4 형식:
- **컨텍스트**: 왜 이 결정이 필요했는지
- **고려한 옵션**: 2-3개 (장단점 비교 테이블)
- **결정**: 선택한 옵션과 근거
- **결과**: 후속 영향

**소스 참조:**
| ADR | 소스 |
|-----|------|
| 0001 | `jittda_doc/jittda-v5-brainstorming-log.md` Phase 1~3 (Temporal vs LangGraph 비교) |
| 0002 | `plan/v5-design/phase0-scaffolding.md` §3 (Clean Slate 접근 전략) |
| 0003 | `plan/v5-design/phase0-scaffolding.md` §4 (DDD 4계층 구조) |
| 0004 | `plan/v5-design/phase3-application.md` §10.3 (Reference Passing) |
| 0005 | `plan/v5-design/phase2-infrastructure.md` §12 (Instructor + Pydantic) |

**핵심 frontmatter 예시 (0001):**
```yaml
---
title: "ADR-0001: LangGraph over Temporal"
type: adr
status: accepted
date: 2026-02-15
decision-makers: ["@sabyun"]
related-adrs:
  - "[[decisions/0003-ddd-four-layers]]"
  - "[[decisions/0004-reference-passing]]"
impacts:
  - "[[application/hmas-graph/MOC]]"
  - "[[application/state-management/MOC]]"
  - "[[application/live-session/MOC]]"
tags: [langgraph, temporal, orchestration]
---
```

---

### Task 7: ADR 0006~0009 (기술 스택 결정)

**Files:**
- Create: `docs/architecture/decisions/0006-tree-sitter-025.md`
- Create: `docs/architecture/decisions/0007-pgvector-iterative-scan.md`
- Create: `docs/architecture/decisions/0008-stt-korean-alternative.md`
- Create: `docs/architecture/decisions/0009-electron-vs-tauri.md`

**소스 참조:**
| ADR | 소스 |
|-----|------|
| 0006 | 기술 스택 조사 결과 (Tree-sitter 0.25 Breaking Changes) |
| 0007 | 기술 스택 조사 결과 (pgvector 0.8.1 iterative_scan) |
| 0008 | 기술 스택 조사 결과 (Deepgram 한국어 미지원 → Whisper) |
| 0009 | `jittda_doc/jittda_reveiw.md` (Electron → Tauri 검토) |

**Step: 확인 + 커밋**

```bash
find docs/architecture/decisions -name "*.md" | wc -l
# Expected: 11개 (MOC + 9 ADR + adr-template.md 이미 Wave 1에서 생성됨)
# 실제 신규: 10개 (MOC + 9 ADR)
git add docs/architecture/decisions/
git commit -m "docs: Wave 2 — ADR 핵심 결정 9개 작성"
```

---

## Wave 3: Domain Layer (15개 파일)

### Task 8: Identity Resolution (6개)

**Files:**
- Create: `docs/architecture/domain/identity-resolution/MOC.md`
- Create: `docs/architecture/domain/identity-resolution/overview.md`
- Create: `docs/architecture/domain/identity-resolution/github-node-id.md`
- Create: `docs/architecture/domain/identity-resolution/dynamic-mailmap.md`
- Create: `docs/architecture/domain/identity-resolution/blame-forensics.md`
- Create: `docs/architecture/domain/identity-resolution/models.md`

**소스:** `plan/v5-design/phase1-domain.md` §7 전체 (7.1~7.3)

**overview.md 핵심 내용:**
- 3단계 파이프라인 전체 흐름도 (Step 1 → 2 → 3)
- 문제점(AS-IS)과 해결(TO-BE) 비교
- frontmatter `depends-on`: `[[decisions/0002-clean-slate-not-migration]]`

**github-node-id.md:**
- GraphQL 쿼리 코드 예시 (`plan/v5-design/phase1-domain.md:36-57` 참조)
- databaseId의 불변성 설명
- frontmatter `affects`: `[[domain/identity-resolution/dynamic-mailmap]]`

**dynamic-mailmap.md:**
- MailmapBuilder 코드 예시 (`plan/v5-design/phase1-domain.md:63-80` 참조)
- 4가지 매칭 규칙 (noreply, 프로필, Levenshtein, 도메인)
- confidence 레벨 (CONFIRMED, HIGH, MEDIUM, LOW)

**blame-forensics.md:**
- `git blame -w -M -C -C` 옵션 설명
- AST pruning (import, 주석, config, generated 제거)
- PureContribution 산출 과정

**models.md:**
- Pydantic v2 모델 정의 코드:
  - `MailmapEntry`, `IdentityCluster`
  - `BlameLineAttribution`, `PureContribution`
- (`plan/v5-design/phase1-domain.md` §7.3 참조)

---

### Task 9: Scoring System (7개)

**Files:**
- Create: `docs/architecture/domain/scoring-system/MOC.md`
- Create: `docs/architecture/domain/scoring-system/four-metrics.md`
- Create: `docs/architecture/domain/scoring-system/logic-metric.md`
- Create: `docs/architecture/domain/scoring-system/mastery-metric.md`
- Create: `docs/architecture/domain/scoring-system/stability-metric.md`
- Create: `docs/architecture/domain/scoring-system/authenticity-metric.md`
- Create: `docs/architecture/domain/scoring-system/confidence-levels.md`

**소스:** `plan/v5-design/phase1-domain.md` §11 (4대 지표 체계)

**four-metrics.md 핵심 내용:**
- 가중 합산 공식: `30% 논리력 + 30% 전문성 + 20% 안정성 + 20% 진정성`
- 4축 지표 개요 테이블
- 각 지표 상세 → children wikilink

**logic-metric.md ~ authenticity-metric.md 각각:**
- 해당 지표의 세부 항목 + 가중치
- 측정 도구 매핑 (Radon, Lizard, SonarQube, Datasketch 등)
- 산출 코드 예시 (Python)
- frontmatter `depends-on`: `[[infrastructure/complexity-analysis/MOC]]` 등

**confidence-levels.md:**
- 🟢🟡🔴 3단계 신뢰도 기준
- 데이터소스 수 × 공개 레포 수 매트릭스

---

### Task 10: Funnel Selection + Question Generation + LinkedIn (4개 서브태스크)

**Funnel Selection (4개 파일):**
- Create: `docs/architecture/domain/funnel-selection/MOC.md`
- Create: `docs/architecture/domain/funnel-selection/hard-filter.md`
- Create: `docs/architecture/domain/funnel-selection/relevance-scoring.md`
- Create: `docs/architecture/domain/funnel-selection/vector-similarity.md`

**소스:** `plan/v5-design/phase1-domain.md` §8 (3단계 퍼널)

**Question Generation (5개 파일):**
- Create: `docs/architecture/domain/question-generation/MOC.md`
- Create: `docs/architecture/domain/question-generation/three-strategies.md`
- Create: `docs/architecture/domain/question-generation/negative-selection.md`
- Create: `docs/architecture/domain/question-generation/intentional-complexity.md`
- Create: `docs/architecture/domain/question-generation/code-evolution.md`

**소스:** `plan/v5-design/phase4-questions.md` §14 (3전략 질문 생성)

**LinkedIn Profile (2개 파일):**
- Create: `docs/architecture/domain/linkedin-profile/MOC.md`
- Create: `docs/architecture/domain/linkedin-profile/profile-model.md`

**소스:** `plan/v5-design/phase1-domain.md` §7.4 (JIT-124)

**Step: 확인 + 커밋**

```bash
find docs/architecture/domain -name "*.md" | wc -l
# Expected: ~28개 (MOC 포함)
git add docs/architecture/domain/
git commit -m "docs: Wave 3 — Domain Layer 문서 작성 완료"
```

---

## Wave 4: Infrastructure Layer (15개 파일)

### Task 11: Git + GitHub 어댑터 (6개)

**Files:**
- Create: `docs/architecture/infrastructure/git-adapter/MOC.md`
- Create: `docs/architecture/infrastructure/git-adapter/clone-strategy.md`
- Create: `docs/architecture/infrastructure/git-adapter/blame-extraction.md`
- Create: `docs/architecture/infrastructure/git-adapter/mailmap-generation.md`
- Create: `docs/architecture/infrastructure/github-client/MOC.md`
- Create: `docs/architecture/infrastructure/github-client/graphql-api.md`
- Create: `docs/architecture/infrastructure/github-client/rest-api.md`

**소스:** `plan/v5-design/phase2-infrastructure.md` §9.1 (CollectorWorker)
- clone-strategy: shallow clone, sparse checkout 전략
- blame-extraction: `git blame -w -M -C -C` + identity_cluster 필터링
- mailmap-generation: 인프라 레벨 .mailmap 파일 생성/적용
- graphql-api: GitHub GraphQL 쿼리 (databaseId, contributions)
- rest-api: PyGithub REST API (repos, languages, commits)

---

### Task 12: AST + 복잡도 + 표절 분석 (8개)

**Files:**
- Create: `docs/architecture/infrastructure/tree-sitter-ast/MOC.md`
- Create: `docs/architecture/infrastructure/tree-sitter-ast/parser-setup.md`
- Create: `docs/architecture/infrastructure/tree-sitter-ast/language-support.md`
- Create: `docs/architecture/infrastructure/tree-sitter-ast/query-cursor-api.md`
- Create: `docs/architecture/infrastructure/complexity-analysis/MOC.md`
- Create: `docs/architecture/infrastructure/complexity-analysis/radon.md`
- Create: `docs/architecture/infrastructure/complexity-analysis/lizard.md`
- Create: `docs/architecture/infrastructure/complexity-analysis/sonarqube.md`
- Create: `docs/architecture/infrastructure/plagiarism-detection/MOC.md`
- Create: `docs/architecture/infrastructure/plagiarism-detection/datasketch-minhash.md`

**소스:**
- Tree-sitter: `plan/v5-design/phase2-infrastructure.md` §9.3 + 기술 스택 조사 결과 (0.25 Breaking Changes)
- 복잡도: `plan/v5-design/phase2-infrastructure.md` §9.4 (Radon CC/Halstead, Lizard MI)
- SonarQube: `plan/v5-design/phase2-infrastructure.md` §9.5 (Docker Profile On-Demand)
- 표절: `plan/v5-design/phase2-infrastructure.md` §9.6 (MinHash/LSH)

**parser-setup.md 핵심:** 0.25.x 설정 코드, 0.24 대비 변경점, `depends-on: [[decisions/0006-tree-sitter-025]]`
**query-cursor-api.md:** QueryCursor 기반 캡처/매칭 코드 예시

---

### Task 13: LLM + Vector + LinkedIn + Voice (9개)

**Files:**
- Create: `docs/architecture/infrastructure/llm-instructor/MOC.md`
- Create: `docs/architecture/infrastructure/llm-instructor/instructor-setup.md`
- Create: `docs/architecture/infrastructure/llm-instructor/langfuse-integration.md`
- Create: `docs/architecture/infrastructure/llm-instructor/prompt-management.md`
- Create: `docs/architecture/infrastructure/vector-search/MOC.md`
- Create: `docs/architecture/infrastructure/vector-search/pgvector-setup.md`
- Create: `docs/architecture/infrastructure/vector-search/embedding-strategy.md`
- Create: `docs/architecture/infrastructure/linkedin-adapter/MOC.md`
- Create: `docs/architecture/infrastructure/linkedin-adapter/brightdata-scraper.md`
- Create: `docs/architecture/infrastructure/voice-pipeline/MOC.md`
- Create: `docs/architecture/infrastructure/voice-pipeline/vad-silero.md`
- Create: `docs/architecture/infrastructure/voice-pipeline/stt-provider.md`
- Create: `docs/architecture/infrastructure/voice-pipeline/tts-provider.md`
- Create: `docs/architecture/infrastructure/voice-pipeline/groq-realtime.md`

**소스:**
- Instructor: `plan/v5-design/phase2-infrastructure.md` §12 + 기술 스택 조사 (1.14 from_provider)
- pgvector: `plan/v5-design/phase2-infrastructure.md` §13 + 기술 스택 조사 (0.8.1 iterative_scan)
- LinkedIn: `plan/v5-design/phase2-infrastructure.md` §9.7 (JIT-125 BrightData)
- Voice: `jittda_doc/jittda_live_brainstorm_curated.md` (Audio Pipeline 섹션)

**instructor-setup.md:** `from_provider()` API, Kimi K2.5 연동 코드, `depends-on: [[decisions/0005-instructor-pydantic]]`
**pgvector-setup.md:** init.sql 설정, HNSW 인덱스, iterative_scan, `depends-on: [[decisions/0007-pgvector-iterative-scan]]`
**stt-provider.md:** Deepgram 한국어 미지원 분석, Whisper large-v3 대안, `depends-on: [[decisions/0008-stt-korean-alternative]]`

**Step: 확인 + 커밋**

```bash
find docs/architecture/infrastructure -name "*.md" | wc -l
# Expected: ~33개
git add docs/architecture/infrastructure/
git commit -m "docs: Wave 4 — Infrastructure Layer 문서 작성 완료"
```

---

## Wave 5: Application Layer (10개 파일)

### Task 14: HMAS Graph (7개)

**Files:**
- Create: `docs/architecture/application/hmas-graph/MOC.md`
- Create: `docs/architecture/application/hmas-graph/meta-agent.md`
- Create: `docs/architecture/application/hmas-graph/forensic-supervisor.md`
- Create: `docs/architecture/application/hmas-graph/logic-supervisor.md`
- Create: `docs/architecture/application/hmas-graph/stack-supervisor.md`
- Create: `docs/architecture/application/hmas-graph/execution-flow.md`
- Create: `docs/architecture/application/hmas-graph/conditional-edges.md`

**소스:** `plan/v5-design/phase3-application.md` §10 전체

**meta-agent.md:** Level 1 총괄 오케스트레이터, MetaState TypedDict, 5개 Phase 흐름
**forensic-supervisor.md:** W1~W5 Worker 구성, 실행 순서, 결과 취합
**logic-supervisor.md:** W6~W8 완전 병렬 실행
**stack-supervisor.md:** W9~W11, LogicSupervisor 완료 후 시작 (AST 의존)
**execution-flow.md:** Mermaid 시퀀스 다이어그램 — Fan-out/Fan-in 흐름
**conditional-edges.md:** 데이터 가용성 Tier별 분기 로직 (Platinum/Gold/Silver)

모든 파일의 `depends-on`: `[[decisions/0001-langgraph-over-temporal]]`

---

### Task 15: Live Session + State + Quality Gate (8개)

**Files:**
- Create: `docs/architecture/application/live-session/MOC.md`
- Create: `docs/architecture/application/live-session/pre-interview-graph.md`
- Create: `docs/architecture/application/live-session/live-engine.md`
- Create: `docs/architecture/application/live-session/post-interview-graph.md`
- Create: `docs/architecture/application/live-session/three-layer-questions.md`
- Create: `docs/architecture/application/state-management/MOC.md`
- Create: `docs/architecture/application/state-management/reference-passing.md`
- Create: `docs/architecture/application/state-management/meta-state.md`
- Create: `docs/architecture/application/state-management/checkpoint-schema.md`
- Create: `docs/architecture/application/quality-gate/MOC.md`
- Create: `docs/architecture/application/quality-gate/review-loop.md`

**소스:**
- Live Session: `jittda_doc/jittda_live_brainstorm_curated.md` (3-Phase 로직)
- State: `plan/v5-design/phase3-application.md` §10.3 (Reference Passing)
- Quality Gate: `plan/v5-design/phase4-questions.md` §14.4

**pre-interview-graph.md:** LangGraph Phase 1 그래프 — 데이터 수집 → Knowledge Graph → Question Deck
**live-engine.md:** 비-LangGraph 로컬 엔진, 3-Layer 구조, 지연 예산
**post-interview-graph.md:** Evaluator + Ranker + Reporter 병렬
**three-layer-questions.md:** Layer 1/2/3 비교 테이블, 지연/주체/목적
**reference-passing.md:** Load-Process-Save-Return Ref 패턴, `depends-on: [[decisions/0004-reference-passing]]`
**meta-state.md:** MetaState TypedDict 전체 필드 정의
**checkpoint-schema.md:** LangGraph 3.0.x checkpoint 테이블 스키마

**Step: 확인 + 커밋**

```bash
find docs/architecture/application -name "*.md" | wc -l
# Expected: ~19개
git add docs/architecture/application/
git commit -m "docs: Wave 5 — Application Layer 문서 작성 완료"
```

---

## Wave 6: Interface Layer (10개 파일)

### Task 16: REST API + WebSocket (5개)

**Files:**
- Create: `docs/architecture/interface/rest-api/MOC.md`
- Create: `docs/architecture/interface/rest-api/endpoints.md`
- Create: `docs/architecture/interface/rest-api/schemas.md`
- Create: `docs/architecture/interface/websocket/MOC.md`
- Create: `docs/architecture/interface/websocket/realtime-protocol.md`

**소스:** `plan/v5-design/phase3-application.md` §10.5 (FastAPI + WebSocket)

**endpoints.md:** FastAPI 라우트 목록 (POST /jobs, GET /jobs/{id}, GET /jobs/{id}/status, WebSocket /ws/jobs/{id})
**schemas.md:** 요청/응답 Pydantic 스키마
**realtime-protocol.md:** WebSocket 메시지 프로토콜 (HMAS 실행 진행률, Agent 상태)

---

### Task 17: Electron App + D3 Charts (9개)

**Files:**
- Create: `docs/architecture/interface/electron-app/MOC.md`
- Create: `docs/architecture/interface/electron-app/architecture.md`
- Create: `docs/architecture/interface/electron-app/audio-capture.md`
- Create: `docs/architecture/interface/electron-app/lancedb-local.md`
- Create: `docs/architecture/interface/electron-app/tauri-migration.md`
- Create: `docs/architecture/interface/d3-charts/MOC.md`
- Create: `docs/architecture/interface/d3-charts/four-axis-radar.md`
- Create: `docs/architecture/interface/d3-charts/complexity-treemap.md`
- Create: `docs/architecture/interface/d3-charts/ai-code-heatmap.md`
- Create: `docs/architecture/interface/d3-charts/skill-heatmap.md`

**소스:**
- Electron: `jittda_doc/jittda_live_brainstorm_curated.md` (Electron 아키텍처, Audio Pipeline)
- D3: `plan/v5-design/phase5-output-frontend.md` §16 (7개 차트)

**architecture.md:** Main/Renderer/Child Process 구조, IPC 통신
**audio-capture.md:** OS별 구현 (macOS CoreAudio, Windows WASAPI)
**lancedb-local.md:** Read-Heavy 전략, 서버 동기화 흐름
**tauri-migration.md:** Electron vs Tauri 비교, `depends-on: [[decisions/0009-electron-vs-tauri]]`

**Step: 확인 + 커밋**

```bash
find docs/architecture/interface -name "*.md" | wc -l
# Expected: ~15개
git add docs/architecture/interface/
git commit -m "docs: Wave 6 — Interface Layer 문서 작성 완료"
```

---

## Wave 7: Crosscutting + Tech Stack (10개 파일)

### Task 18: Crosscutting (8개)

**Files:**
- Create: `docs/architecture/crosscutting/MOC.md`
- Create: `docs/architecture/crosscutting/security.md`
- Create: `docs/architecture/crosscutting/performance.md`
- Create: `docs/architecture/crosscutting/monitoring.md`
- Create: `docs/architecture/crosscutting/error-handling.md`
- Create: `docs/architecture/crosscutting/testing-strategy.md`
- Create: `docs/architecture/crosscutting/deployment.md`
- Create: `docs/architecture/crosscutting/data-availability-tiers.md`

**소스:**
- testing: `plan/v5-design/phase6-testing.md`
- deployment: `plan/v5-design/phase0-scaffolding.md` §15 (Docker + Cloudflare Tunnel)
- data-availability: `jittda_doc/jittda_live_brainstorm_curated.md` (Platinum/Gold/Silver)
- security/performance/monitoring/error-handling: 전체 설계 문서에서 관련 내용 취합

**data-availability-tiers.md 핵심:**
- Platinum (이력서+GitHub+포트폴리오), Gold (이력서+GitHub), Silver (이력서만)
- Conditional Edges 분기 로직
- Fallback 전략

---

### Task 19: Tech Stack (5개)

**Files:**
- Create: `docs/architecture/tech-stack/MOC.md`
- Create: `docs/architecture/tech-stack/backend.md`
- Create: `docs/architecture/tech-stack/frontend.md`
- Create: `docs/architecture/tech-stack/infrastructure.md`
- Create: `docs/architecture/tech-stack/version-matrix.md`

**소스:** 설계 문서 섹션 6 (기술 스택 업데이트 2026.02 최신)

**version-matrix.md 핵심:**
- 전체 패키지 버전 매트릭스 테이블
- v5 설계서 대비 변경점 하이라이트
- Breaking Changes 코드 예시

**Step: 확인 + 최종 커밋**

```bash
find docs/architecture -name "*.md" | wc -l
# Expected: ~77개
git add docs/architecture/crosscutting/ docs/architecture/tech-stack/
git commit -m "docs: Wave 7 — Crosscutting + Tech Stack 문서 작성 완료"
```

---

## Wave 완료 후: 검증

### Task 20: 전체 Vault 검증

**Step 1: 파일 수 확인**
```bash
find docs/architecture -name "*.md" | wc -l
# Expected: ~77개
```

**Step 2: frontmatter 일관성 확인**
```bash
# 모든 MD 파일에 title 필드가 있는지 확인
grep -rL "^title:" docs/architecture/ --include="*.md" | grep -v ".obsidian" | grep -v "templates/"
# Expected: 결과 없음 (모든 파일에 title 존재)
```

**Step 3: 깨진 wikilink 확인**
```bash
# [[...]] 패턴 추출 → 실제 파일 존재 여부 확인
grep -roh '\[\[[^]]*\]\]' docs/architecture/ --include="*.md" | sort -u | head -20
# 수동 검증: 각 링크가 실제 파일을 가리키는지
```

**Step 4: RELATION-MAP.md 최종 업데이트**
- 모든 계층의 실제 파일이 그래프에 반영되었는지 확인
- 누락된 의존성 엣지 추가

**Step 5: 최종 커밋**
```bash
git add docs/architecture/
git commit -m "docs: Vault 검증 완료 — 전체 ~77개 문서, 관계 매핑 확인"
```

---

## 실행 요약

| Wave | Task | 파일 수 | 커밋 메시지 |
|------|------|---------|------------|
| 1 | 1~4 | ~8 | `docs: Wave 1 — Obsidian Vault 골격 구조 생성` |
| 2 | 5~7 | ~11 | `docs: Wave 2 — ADR 핵심 결정 9개 작성` |
| 3 | 8~10 | ~15 | `docs: Wave 3 — Domain Layer 문서 작성 완료` |
| 4 | 11~13 | ~15 | `docs: Wave 4 — Infrastructure Layer 문서 작성 완료` |
| 5 | 14~15 | ~10 | `docs: Wave 5 — Application Layer 문서 작성 완료` |
| 6 | 16~17 | ~10 | `docs: Wave 6 — Interface Layer 문서 작성 완료` |
| 7 | 18~19 | ~10 | `docs: Wave 7 — Crosscutting + Tech Stack 문서 작성 완료` |
| - | 20 | 0 | `docs: Vault 검증 완료` |

**총 20개 Task, ~77개 파일, 8개 커밋**
