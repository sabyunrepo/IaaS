# 06. LLM Activity 흐름 및 파이프라인 상세

> Vantict Sniper v4.0 — AI 기술 면접 스크립트 생성 파이프라인
> 최종 업데이트: 2026-02-07

---

## 목차

1. [파이프라인 개요](#1-파이프라인-개요)
2. [Phase별 상세 흐름도](#2-phase별-상세-흐름도)
3. [Activity별 상세 분석](#3-activity별-상세-분석)
4. [데이터 흐름도](#4-데이터-흐름도)
5. [LLM 호출 패턴](#5-llm-호출-패턴)
6. [프롬프트 YAML 매핑](#6-프롬프트-yaml-매핑)
7. [외부 서비스 의존성](#7-외부-서비스-의존성)
8. [모델 설정 및 비용 구조](#8-모델-설정-및-비용-구조)

---

## 1. 파이프라인 개요

InterviewGenerationWorkflow는 **5-Phase 파이프라인** (Phase 0 ~ Phase 4)으로 구성되며, 입력 보강부터 최종 면접 스크립트 생성까지 약 **25+개 Activity**를 오케스트레이션한다.

```
Phase 0          Phase 1         Phase 2              Phase 2.5
Input            Planning        Parallel Analysis     Knowledge Graph
Enrichment                                             Construction
    |                |               |                      |
    v                v               v                      v
 enrich_input -> create_plan -> [analyze_jd      ] -> build_knowledge_graph
                                [analyze_documents]
                                [analyze_code     ]
                                   |
                                   v
                              Phase 3                 Phase 4
                              Question                Review &
                              Generation              Finalization
                                   |                      |
                                   v                      v
                              select_topics           review_questions
                              craft_question x20       -> (revision loop)
                              [enhance_terminology ]   finalize_output
                              [craft_eval_scenarios]   generate_intel_brief
                              [design_follow_ups   ]   generate_deep_analysis
                              [gen_interviewer_notes]   generate_decision_support
                              [gen_decision_guide  ]   persist_result
                                                       send_webhook
```

### Phase 요약

| Phase | 이름 | 설명 | 병렬 실행 | Progress |
|-------|------|------|-----------|----------|
| **Phase 0** | Input Enrichment | 문서에서 URL 추출, LinkedIn/GitHub 프로필 수집 | - | 5% |
| **Phase 1** | Planning | GitHub 워크로드 추정, 실행 계획 수립 | - | 15% |
| **Phase 2** | Analysis | JD/문서/코드 분석 (병렬), KG 구축 | JD + Doc 병렬, Code 별도 | 25% |
| **Phase 3** | Generation | 토픽 선정, 질문 생성 (병렬), 강화 에이전트 (병렬) | 질문 20개 병렬, 강화 5개 병렬 | 60~70% |
| **Phase 4** | Review & Finalization | 품질 검토, 리비전 루프, 최종화, Intel/Analysis/Decision 생성 | Intel+Analysis+Decision 병렬 | 85~100% |

---

## 2. Phase별 상세 흐름도

### Phase 0: Input Enrichment

```
input_data (사용자 입력)
    |
    v
enrich_input
    ├─ Resume/Portfolio/Cover Letter에서 URL 추출 (GitHub, LinkedIn)
    ├─ git_url 필드 처리 (프로필 URL → 레포 목록 자동 가져오기)
    ├─ LinkedIn → Bright Data API → 프로필 수집
    ├─ GitHub username 자동 추론
    └─ available_analyses 결정 (jd_analysis, document_analysis, code_analysis)
    |
    v
enriched_input: {raw_input, github_urls, linkedin_profile, available_analyses, ...}
```

### Phase 1: Planning

```
enriched_input
    |
    v
create_execution_plan
    ├─ GitHub API로 레포별 워크로드 추정
    ├─ JD 텍스트에서 기술 스택 키워드 추출 (regex)
    └─ 실행 계획 생성 (어떤 분석을 활성화할지)
    |
    v
execution_plan: {phases, workload, jd_tech_stack, ...}
```

### Phase 2: Parallel Analysis

```
execution_plan
    |
    ├─ [병렬] analyze_jd(jd_text)               → jd_analysis
    ├─ [병렬] analyze_documents(raw_input)       → document_analysis
    └─ [별도] _run_parallel_code_analysis()      → code_analysis
                 ├─ analyze_code (Manager: 레포 필터링)
                 ├─ analyze_single_repo x N (병렬, HYBRID 3-Stage)
                 ├─ validate_code_analysis x N (품질 검증)
                 └─ 실패 레포 재분석 (최대 1회)
    |
    v
analysis: {jd_analysis, document_analysis, code_analysis}
    |
    v
Phase 2.5: build_knowledge_graph (non-blocking)
    ├─ 후보자 엔티티 추출 (profile)
    ├─ 코드 엔티티 추출 (code_analysis)
    ├─ JD 엔티티 추출 (jd_analysis)
    └─ 충돌 감지 (conflict_detector)
```

### Phase 3: Question Generation

```
analysis + enriched_input
    |
    v
3a. select_topics (KG + Vector + Code + JD 후보 기반 토픽 20개 선정)
    |
    v
3b. craft_question x 20 (병렬, 카테고리별 특화 프롬프트)
    |
    v
3c-3g. Enhancement Agents (병렬)
    ├─ enhance_terminology       (용어 설명 추가)
    ├─ craft_evaluation_scenarios (3단계 평가 시나리오)
    ├─ design_follow_ups         (후속 질문 분기)
    ├─ generate_interviewer_notes (면접관 참고 노트)
    └─ generate_decision_guide   (채용 의사결정 가이드)
    |
    v
questions (enhanced, 20개)
```

### Phase 4: Review & Finalization

```
questions
    |
    v
4a. review_questions (품질 검토: 중복, 난이도 균형, 카테고리 분포)
    |
    ├─ verdict == "APPROVED" → 4b로 진행
    └─ verdict == "NEEDS_REVISION" → revise_questions → review_questions (최대 3회 반복)
    |
    v
4b. finalize_output (용어집 통합, 후보자 요약, 면접관 가이드, 스크립트 조립)
    |
    v
4c. [병렬] Intel/Analysis/Decision 생성
    ├─ generate_intel_brief       (Intel Brief: JD 요약, 역량 매칭, GitHub, LinkedIn)
    ├─ generate_deep_analysis     (Deep Analysis: 레이더 차트, Engineering DNA, 리스크)
    └─ generate_decision_support  (Decision: 의사결정 요약, 면접관 팁, JD 역량 매핑)
    |
    v
4d. persist_result (DB 저장)
4e. send_webhook (콜백 URL로 결과 전송, fire-and-forget)
```

---

## 3. Activity별 상세 분석

### Phase 0: Input Enrichment

#### `enrich_input`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/input_enrichment.py` |
| **함수명** | `enrich_input(input_data: dict) -> dict` |
| **Phase** | `input_enrichment` |
| **입력 데이터** | `input_data`: 사용자 원본 입력 (resume_path, portfolio_path, cover_letter_path, jd_text, git_url, linkedin_url, experience_level 등) |
| **출력 데이터** | `{raw_input, github_urls, candidate_github_username, linkedin_profile, extraction_sources, available_analyses, document_errors, github_validation}` |
| **사용 LLM 모델** | 없음 (LLM 미사용) |
| **사용 프롬프트** | 없음 |
| **사용 도구/서비스** | `DocumentParser.extract_text()`, `LinkedInService.get_profile()` (Bright Data API), `GitHubService.get_user_repos()`, `GitHubService.infer_candidate_username()` |
| **output_language** | 미사용 |
| **Heartbeat** | 문서별 URL 추출, LinkedIn API 호출, GitHub URL 검증 시 heartbeat |

---

### Phase 1: Planning

#### `create_execution_plan`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/planning.py` |
| **함수명** | `create_execution_plan(enriched_input: dict) -> dict` |
| **Phase** | `planning` |
| **입력 데이터** | `enriched_input`: Phase 0 결과 전체 |
| **출력 데이터** | `{candidate_github_username, phases: [{name, enabled}], workload, estimated_total_time_seconds, raw_input, jd_tech_stack}` |
| **사용 LLM 모델** | 없음 (LLM 미사용) |
| **사용 프롬프트** | 없음 |
| **사용 도구/서비스** | `GitHubService.get_repo_info()`, `GitHubService.get_repo_languages()`, regex 기반 기술 스택 추출 (`_extract_tech_stack_from_jd`) |
| **output_language** | 미사용 |
| **Heartbeat** | 레포별 워크로드 추정 시 heartbeat |

---

### Phase 2: Analysis

#### `analyze_jd`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/jd_analysis.py` |
| **함수명** | `analyze_jd(jd_text: str, job_id: str | None, output_language: str) -> dict` |
| **Phase** | `analysis` |
| **입력 데이터** | JD 텍스트 (원문), job_id, output_language |
| **출력 데이터** | `{job_title, company_name, requirements[], responsibilities[], company_culture[], tech_stack[], skill_matches, overall_match_score, gaps, strengths, kg_entity_count}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `jd_analysis.yaml` → `analyze` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()`, `KnowledgeGraph.extract_and_store_jd_entities()` |
| **output_language** | 지원 (프롬프트 변수로 전달) |

#### `analyze_documents`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/document_analysis.py` |
| **함수명** | `analyze_documents(input_data: dict) -> dict` |
| **Phase** | `analysis` |
| **입력 데이터** | `input_data`: resume_path, portfolio_path, cover_letter_path, job_id, language_config |
| **출력 데이터** | `{profile: {name, contact, education, work_experience, skills, projects, ...}, raw_texts[], parse_info[], kg_entity_count}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `document_analysis.yaml` → `extract_profile` |
| **사용 도구/서비스** | `DocumentParser.parse_document()` (Docling primary, pymupdf4llm fallback), `CachedLLMService`, `run_llm_with_heartbeat()`, `VectorStore.store_profile()`, `KnowledgeGraph.extract_and_store_candidate_entities()` |
| **output_language** | 지원 (프롬프트 변수로 전달) |

#### `analyze_code`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/code_analysis.py` |
| **함수명** | `analyze_code(github_urls: list[str], input_data: dict, execution_plan: dict | None) -> dict` |
| **Phase** | `analysis` |
| **입력 데이터** | GitHub URL 리스트, input_data (job_id, jd_tech_stack, candidate_github_username), execution_plan |
| **출력 데이터** | `{repositories[], target_repos[], jd_tech_stack, candidate_username, combined_tech_stack, total_patterns, total_notable_implementations, top_question_candidates[], kg_entity_count}` |
| **사용 LLM 모델** | `Kimi K2.5 Coder` (`moonshot/moonshot-v1-auto`) — `CodeAnalyzer.llm_analyze_code()` 내부 |
| **사용 프롬프트** | CodeAnalyzer 내부 프롬프트 (code_analysis.py에서 직접 구성) |
| **사용 도구/서비스** | `GitHubService.filter_repos_by_language()`, `CodeAnalyzer.analyze_with_pydriller()`, `CodeAnalyzer.analyze_ast()`, `CodeAnalyzer.llm_analyze_code()`, `VectorStore.store_code()`, `KnowledgeGraph.extract_and_store_code_entities()` |
| **output_language** | 미사용 (코드 분석은 언어 비의존) |
| **비고** | 4-Phase 내부 파이프라인: PyGithub(필터) → PyDriller(추출) → AST(구조) → LLM(의미) |

#### `analyze_single_repo`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/code_analysis.py` |
| **함수명** | `analyze_single_repo(repo_info: dict, jd_tech_stack: list, candidate_username: str | None, job_id: str | None) -> dict` |
| **Phase** | `analysis` |
| **입력 데이터** | 단일 레포 정보, JD 기술 스택, 후보자 username, job_id |
| **출력 데이터** | `{repo_url, repo_name, language, candidate_commits, candidate_additions, avg_complexity, ast_analysis, analysis, notable_implementations, hybrid_metadata}` |
| **사용 LLM 모델** | `GLM-4.7` (`zai/glm-4.7`) — 비용 최적화 전용 모델 |
| **사용 프롬프트** | CodeAnalyzer 내부 프롬프트 (3-Stage별 별도 구성) |
| **사용 도구/서비스** | `CodeAnalyzer` (PyDriller + AST + HYBRID 3-Stage LLM) |
| **output_language** | 미사용 |
| **비고** | HYBRID 3-Stage Multi-Agent: Overview Agent → Deep Analysis Agents (병렬) → Synthesis Agent |

#### `validate_code_analysis`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/code_analysis.py` |
| **함수명** | `validate_code_analysis(repo_result: dict, min_commits: int, min_notables: int) -> dict` |
| **Phase** | `analysis` |
| **입력 데이터** | analyze_single_repo 결과 |
| **출력 데이터** | `{valid: bool, issues[], suggestions[], repo_name, metrics}` |
| **사용 LLM 모델** | 없음 (규칙 기반 검증) |
| **사용 프롬프트** | 없음 |
| **사용 도구/서비스** | 없음 (순수 로직) |

---

### Phase 2.5: Knowledge Graph

#### `build_knowledge_graph`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/knowledge_graph_activities.py` |
| **함수명** | `build_knowledge_graph(job_id: str, profile: dict | None, code_analysis: dict | None, jd_analysis: dict | None) -> dict` |
| **Phase** | `analysis` |
| **입력 데이터** | job_id, LinkedIn 프로필, 코드 분석 결과, JD 분석 결과 |
| **출력 데이터** | `{status, entity_counts, relation_counts, total_entities, total_relations, conflict_summary, kg_summary}` |
| **사용 LLM 모델** | 없음 (규칙 기반 엔티티 추출) |
| **사용 프롬프트** | 없음 |
| **사용 도구/서비스** | `KnowledgeGraph` (PostgreSQL 기반 그래프 스토어), `ConflictDetector` |

#### `get_kg_question_candidates`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/knowledge_graph_activities.py` |
| **함수명** | `get_kg_question_candidates(job_id: str, limit: int, balance_categories: bool) -> dict` |
| **Phase** | `generation` |
| **입력 데이터** | job_id, 후보 수 제한, 카테고리 균형 여부 |
| **출력 데이터** | `{status, candidates[], summary}` |
| **사용 LLM 모델** | 없음 (그래프 쿼리) |
| **사용 도구/서비스** | `InterviewGraphQueries` |

#### `get_evidence_chain`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/knowledge_graph_activities.py` |
| **함수명** | `get_evidence_chain(job_id: str, topic: str) -> dict` |
| **Phase** | `generation` |
| **입력 데이터** | job_id, 토픽명 |
| **출력 데이터** | `{status, topic, evidence_chain[]}` |
| **사용 LLM 모델** | 없음 |
| **사용 도구/서비스** | `InterviewGraphQueries` |

#### `clear_knowledge_graph`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/knowledge_graph_activities.py` |
| **함수명** | `clear_knowledge_graph(job_id: str) -> dict` |
| **Phase** | `cleanup` |
| **입력 데이터** | job_id |
| **출력 데이터** | `{status, job_id}` |
| **사용 LLM 모델** | 없음 |
| **사용 도구/서비스** | `KnowledgeGraph` |

---

### Phase 3: Question Generation

#### `select_topics`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `select_topics(analysis: dict, enriched_input: dict, job_id: str | None) -> list[dict]` |
| **Phase** | `question_generation` |
| **입력 데이터** | 통합 분석 결과, enriched_input (경험 레벨 등), job_id |
| **출력 데이터** | 20개 토픽 리스트: `[{category, topic, difficulty, source, evidence}]` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `select_topics` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()`, `InterviewGraphQueries.get_top_question_candidates()`, `VectorStore.search_profile()`, `VectorStore.search_code()` |
| **output_language** | 미사용 (토픽 선정은 내부 로직) |
| **비고** | KG 후보 (0.15 부스트) → Vector Search 후보 → Code 후보 → JD 후보 우선순위 |

#### `craft_question`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `craft_question(topic: dict, analysis: dict, enriched_input: dict, job_id: str | None) -> dict` |
| **Phase** | `question_generation` |
| **입력 데이터** | 단일 토픽, 통합 분석 결과, enriched_input, job_id |
| **출력 데이터** | `{id, question_text, category, difficulty, language, topic, alternative_phrasing, expected_answer, evaluation_criteria, ...}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `craft_question_{category}` (카테고리별 특화), fallback → `craft_question` (범용) |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()`, `InterviewGraphQueries.get_evidence_chain_for_topic()`, `VectorStore.search_profile()`, `VectorStore.search_code()` |
| **output_language** | 지원 (프롬프트 변수로 전달) |
| **비고** | 카테고리별 5종 특화 프롬프트: `craft_question_role_fit`, `craft_question_technical_depth`, `craft_question_execution_ownership`, `craft_question_communication`, `craft_question_risk_flags` |

#### `enhance_terminology`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `enhance_terminology(questions: list[dict], enriched_input: dict) -> dict` |
| **Phase** | `question_generation` |
| **입력 데이터** | 생성된 질문 리스트 (최대 25개), enriched_input |
| **출력 데이터** | `{question_id: [{term, explanation}]}` — 질문별 용어 설명 매핑 |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `enhance_terminology` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |

#### `craft_evaluation_scenarios`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `craft_evaluation_scenarios(questions: list[dict], enriched_input: dict) -> dict` |
| **Phase** | `question_generation` |
| **입력 데이터** | 생성된 질문 리스트, enriched_input |
| **출력 데이터** | `{question_id: {good, average, poor}}` — 3단계 평가 시나리오 |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `craft_evaluation_scenarios` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |

#### `design_follow_ups`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `design_follow_ups(questions: list[dict], enriched_input: dict) -> dict` |
| **Phase** | `question_generation` |
| **입력 데이터** | 생성된 질문 리스트, enriched_input |
| **출력 데이터** | `{question_id: [{follow_up_text, trigger_condition}]}` — 후속 질문 분기 |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `design_follow_ups` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |

#### `generate_interviewer_notes`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `generate_interviewer_notes(questions: list[dict], enriched_input: dict) -> dict` |
| **Phase** | `question_generation` |
| **입력 데이터** | 생성된 질문 리스트, enriched_input |
| **출력 데이터** | `{question_id: {note_text, key_signals}}` — 면접관 참고 노트 |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `generate_interviewer_notes` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |

#### `generate_decision_guide`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `generate_decision_guide(analysis: dict, enriched_input: dict) -> dict` |
| **Phase** | `question_generation` |
| **입력 데이터** | 통합 분석 결과, enriched_input |
| **출력 데이터** | `{hire_signals, caution_areas, decision_matrix, ...}` — 채용 의사결정 가이드 |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `generate_decision_guide` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |

#### `revise_questions`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/question_generation.py` |
| **함수명** | `revise_questions(questions: list[dict], review_feedback: dict, enriched_input: dict) -> list[dict]` |
| **Phase** | `question_generation` |
| **입력 데이터** | 기존 질문 리스트, 리뷰 피드백, enriched_input |
| **출력 데이터** | 수정된 질문 리스트 |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `question_generation.yaml` → `revise_questions` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |

---

### Phase 4: Quality Review & Finalization

#### `review_questions`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/quality_review.py` |
| **함수명** | `review_questions(questions: list[dict], output_language: str) -> dict` |
| **Phase** | `quality_review` |
| **입력 데이터** | 생성된 질문 리스트, output_language |
| **출력 데이터** | `{verdict: "APPROVED"|"NEEDS_REVISION", issues[], questions_to_revise[], category_distribution, difficulty_distribution}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) |
| **사용 프롬프트** | `quality_review.yaml` → `review` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |
| **비고** | 규칙 기반 검증 (카테고리/난이도 분포) + LLM 기반 중복/품질 검토 결합 |

#### `finalize_output`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/finalization.py` |
| **함수명** | `finalize_output(questions: list[dict], analysis: dict, enriched_input: dict) -> dict` |
| **Phase** | `finalization` |
| **입력 데이터** | 최종 질문 리스트, 통합 분석 결과, enriched_input |
| **출력 데이터** | `{generated_at, output_language, candidate_summary, questions, interviewer_guide, full_glossary, linkedin_profile, candidate, metadata, output_path}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) — 2회 호출 |
| **사용 프롬프트** | `finalization.yaml` → `candidate_summary` (후보자 요약), `finalization.yaml` → `interviewer_guide` (면접관 가이드) |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()`, `StorageService` (LocalStack S3 / AWS S3) |
| **output_language** | 지원 |

#### `generate_intel_brief`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/intel_generation.py` |
| **함수명** | `generate_intel_brief(jd_analysis, document_analysis, code_analysis, linkedin_profile, jd_text, job_id, output_language) -> dict` |
| **Phase** | `finalization` |
| **입력 데이터** | JD 분석, 문서 분석, 코드 분석, LinkedIn 프로필, JD 원문, job_id, output_language |
| **출력 데이터** | `IntelBrief {jd_summary, jd_full, competencies[], github, linkedin[], linkedin_warning}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) — 역량 매칭에 1회 호출 |
| **사용 프롬프트** | `v2_generation.yaml` → `competency_matching` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |
| **비고** | LLM 우선, 실패 시 규칙 기반 fallback (`_match_competencies`) |

#### `generate_deep_analysis`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/analysis_generation.py` |
| **함수명** | `generate_deep_analysis(jd_analysis, code_analysis, document_analysis, job_id, output_language) -> dict` |
| **Phase** | `finalization` |
| **입력 데이터** | JD 분석, 코드 분석, 문서 분석, job_id, output_language |
| **출력 데이터** | `DeepAnalysis {radar_candidate[5], radar_required[5], engineering_dna[], risk_flags[], skill_table[], overall_match}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) — 최대 2회 호출 (레이더 + DNA) |
| **사용 프롬프트** | `v2_generation.yaml` → `radar_analysis`, `v2_generation.yaml` → `engineering_dna` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |
| **비고** | LLM 우선, 실패 시 규칙 기반 fallback (각각 `_calculate_radar_scores`, `_analyze_engineering_dna`) |

#### `generate_decision_support`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/decision_generation.py` |
| **함수명** | `generate_decision_support(candidate_summary, questions, jd_analysis, document_analysis, job_id, output_language) -> dict` |
| **Phase** | `finalization` |
| **입력 데이터** | 후보자 요약, 질문 리스트, JD 분석, 문서 분석, job_id, output_language |
| **출력 데이터** | `DecisionSupport {summary: DecisionSummary, interviewer_guide: InterviewerGuideTips, jd_competency_map[]}` |
| **사용 LLM 모델** | `Kimi K2.5` (`moonshot/moonshot-v1-auto`) — 최대 2회 호출 (요약 + 팁) |
| **사용 프롬프트** | `v2_generation.yaml` → `decision_summary`, `v2_generation.yaml` → `interviewer_tips` |
| **사용 도구/서비스** | `CachedLLMService`, `run_llm_with_heartbeat()` |
| **output_language** | 지원 |
| **비고** | LLM 우선, 실패 시 규칙 기반 fallback (각각 `_extract_decision_summary`, `_build_interviewer_tips`) |

---

### 인프라/유틸리티 Activity

#### `persist_result`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/persist_result.py` |
| **함수명** | `persist_result(job_id: str, final_script: dict) -> dict` |
| **Phase** | `finalization` |
| **입력 데이터** | job_id, 최종 스크립트 |
| **출력 데이터** | `{persisted: bool}` |
| **사용 LLM 모델** | 없음 |
| **사용 도구/서비스** | PostgreSQL (`JobDB` 테이블 업데이트) |

#### `send_webhook`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/send_webhook.py` |
| **함수명** | `send_webhook(job_id: str, callback_url: str, status: str, final_output: dict | None) -> dict` |
| **Phase** | `finalization` |
| **입력 데이터** | job_id, callback URL, 상태, 최종 결과 |
| **출력 데이터** | `{sent: bool, status_code: int | None}` |
| **사용 LLM 모델** | 없음 |
| **사용 도구/서비스** | `httpx.AsyncClient` (HTTP POST) |

#### `start_job_trace` / `end_job_trace` / `log_phase_event`

| 항목 | 내용 |
|------|------|
| **파일 경로** | `backend/app/workflows/activities/observability_activities.py` |
| **함수명** | `start_job_trace(job_id, user_id, metadata)`, `end_job_trace(job_id, trace_id, status, quality_score)`, `log_phase_event(job_id, phase, event, metadata)` |
| **Phase** | Observability (전 Phase에 걸쳐 사용) |
| **사용 LLM 모델** | 없음 |
| **사용 도구/서비스** | Langfuse (`create_trace_for_job`, `score_trace`, `flush_langfuse`) |

---

## 4. 데이터 흐름도

### 핵심 데이터 객체 흐름

```
사용자 입력 (input_data)
    │
    ├─ resume_path, portfolio_path, cover_letter_path
    ├─ jd_text
    ├─ git_url / linkedin_url
    ├─ experience_level
    └─ language_config.output_language
    │
    ▼
┌─────────────────────────────────────────────────┐
│  enriched_input                                  │
│  ├─ raw_input (원본 유지)                        │
│  ├─ github_urls[] (개인 레포만, 조직 제외)       │
│  ├─ linkedin_profile (Bright Data API)           │
│  ├─ candidate_github_username (추론됨)           │
│  └─ available_analyses[] (활성화할 분석 목록)    │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  execution_plan                                  │
│  ├─ phases[] (각 분석 활성화 여부)               │
│  ├─ workload{} (레포별 예상 소요시간)            │
│  └─ jd_tech_stack[] (regex로 추출한 기술 스택)   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  analysis (통합 분석 결과)                       │
│  ├─ jd_analysis                                  │
│  │   ├─ job_title, company_name                  │
│  │   ├─ requirements[] (필수/우대)               │
│  │   ├─ responsibilities[]                       │
│  │   └─ tech_stack[]                             │
│  ├─ document_analysis                            │
│  │   ├─ profile (name, skills, experiences)      │
│  │   └─ parse_info[]                             │
│  └─ code_analysis (optional)                     │
│      ├─ repositories[]                           │
│      ├─ combined_tech_stack[]                    │
│      └─ top_question_candidates[]                │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Knowledge Graph (PostgreSQL)                    │
│  ├─ 후보자 엔티티 (스킬, 경력, 프로젝트)        │
│  ├─ 코드 엔티티 (패턴, 기술, 구현)              │
│  ├─ JD 엔티티 (요구사항, 기술스택)              │
│  └─ 충돌 리포트 (이력서 vs 코드 불일치)         │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  questions[] (20개, 강화 완료)                   │
│  ├─ id (UUID)                                    │
│  ├─ question_text, category, difficulty          │
│  ├─ terminology[] (용어 설명)                    │
│  ├─ evaluation_scenarios (3단계)                 │
│  ├─ follow_up_questions[]                        │
│  ├─ interviewer_note                             │
│  └─ kg_source, code_reference (출처 추적)        │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  final_script (최종 출력)                        │
│  ├─ candidate_summary                            │
│  ├─ questions[] (강화 완료)                      │
│  ├─ interviewer_guide                            │
│  ├─ full_glossary[]                              │
│  ├─ decision_guide                               │
│  ├─ intel (IntelBrief)                           │
│  ├─ analysis (DeepAnalysis)                      │
│  ├─ decision (DecisionSupport)                   │
│  ├─ category_weights (경험 레벨별)               │
│  └─ linkedin_profile, candidate (프론트엔드용)   │
└─────────────────────────────────────────────────┘
```

### 저장소 연동

```
Activity 실행 중 저장소 연동:

analyze_documents ──→ VectorStore.store_profile()     ──→ pgvector (프로필 임베딩)
                  ──→ KnowledgeGraph.extract_candidate ──→ PostgreSQL (엔티티)

analyze_code      ──→ VectorStore.store_code()        ──→ pgvector (코드 임베딩)
                  ──→ KnowledgeGraph.extract_code      ──→ PostgreSQL (엔티티)

analyze_jd        ──→ KnowledgeGraph.extract_jd        ──→ PostgreSQL (엔티티)

select_topics     ──→ VectorStore.search_profile()    ←── pgvector (시맨틱 검색)
                  ──→ VectorStore.search_code()       ←── pgvector (시맨틱 검색)
                  ──→ GraphQueries.get_candidates()   ←── PostgreSQL (KG 쿼리)

craft_question    ──→ VectorStore.search_profile()    ←── pgvector (추가 컨텍스트)
                  ──→ GraphQueries.get_evidence()     ←── PostgreSQL (증거 체인)

finalize_output   ──→ StorageService.upload_json()    ──→ S3 (최종 스크립트)
persist_result    ──→ JobDB.update()                  ──→ PostgreSQL (Job 상태)
```

---

## 5. LLM 호출 패턴

### CachedLLMService 아키텍처

```python
class CachedLLMService:
    """Redis 캐시 + LiteLLM Router + Instructor 통합"""

    async def run(prompt, activity_name) -> dict | list | str:
        """글로벌 캐시: llm_cache:{activity_name}:{SHA256(model:prompt)}"""

    async def run_for_job(prompt, job_id, activity_name) -> dict | list | str:
        """잡 스코프 캐시: llm_cache:job:{job_id}:{activity_name}:{SHA256(model:prompt)}"""

    async def run_with_prompt_config(prompt_config) -> dict | list | str:
        """Langfuse 프롬프트 버전 연동"""

    async def invalidate_for_job(job_id) -> None:
        """잡별 캐시 일괄 삭제"""
```

### run_llm_with_heartbeat 래퍼

```python
async def run_llm_with_heartbeat(
    llm: CachedLLMService,
    prompt: str,
    activity_name: str,
    interval: float = 30.0,
) -> dict | list | str:
    """
    LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)

    - asyncio.create_task()로 heartbeat 백그라운드 루프 생성
    - interval초마다 activity.heartbeat() 호출
    - LLM 응답 수신 후 heartbeat 태스크 cancel
    """
```

### 모델 라우팅 흐름

```
Activity 함수 호출
    │
    ▼
CachedLLMService(activity_name="craft_question")
    │
    ├─ llm_config.get_model_for_activity("craft_question")
    │   └─ ACTIVITY_MODEL_CONFIG["craft_question"] = "moonshot/moonshot-v1-auto"
    │
    ├─ Redis 캐시 조회 (LLM_CACHE_ENABLED=true 시)
    │   ├─ HIT → 캐시된 응답 반환
    │   └─ MISS → LLM 호출
    │
    ├─ LiteLLM Router (Fallback Chain)
    │   ├─ Primary: moonshot/moonshot-v1-auto (Kimi K2.5)
    │   └─ Fallback: settings.LLM_FALLBACK_MODEL (GPT-4o → Claude)
    │
    ├─ Instructor (JSON 구조화 출력 강제)
    │
    ├─ Redis 캐시 저장
    │
    └─ Langfuse Span 기록 (observability)
```

### Phase별 LLM 호출 횟수 (1회 워크플로우 기준)

| Phase | Activity | LLM 호출 수 | 비고 |
|-------|----------|------------|------|
| Phase 2 | `analyze_jd` | 1 | |
| Phase 2 | `analyze_documents` | 1 | |
| Phase 2 | `analyze_single_repo` x N | N x 3 | 레포당 3회 (Overview + Deep x files + Synthesis), GLM-4.7 사용 |
| Phase 3 | `select_topics` | 1 | |
| Phase 3 | `craft_question` x 20 | 20 | 병렬 |
| Phase 3 | `enhance_terminology` | 1 | 병렬 (3c-3g) |
| Phase 3 | `craft_evaluation_scenarios` | 1 | 병렬 |
| Phase 3 | `design_follow_ups` | 1 | 병렬 |
| Phase 3 | `generate_interviewer_notes` | 1 | 병렬 |
| Phase 3 | `generate_decision_guide` | 1 | 병렬 |
| Phase 4 | `review_questions` | 1~4 | 리비전 루프 (최대 3회) |
| Phase 4 | `revise_questions` | 0~3 | 리비전 시에만 |
| Phase 4 | `finalize_output` | 2 | candidate_summary + interviewer_guide |
| Phase 4 | `generate_intel_brief` | 1 | 병렬 |
| Phase 4 | `generate_deep_analysis` | 2 | 병렬 (radar + dna) |
| Phase 4 | `generate_decision_support` | 2 | 병렬 (summary + tips) |
| **합계** | | **~35~40+** | 코드 분석 레포 수에 따라 변동 |

---

## 6. 프롬프트 YAML 매핑

### 프롬프트 파일 구조

```
backend/app/prompts/
├── document_analysis.yaml      # 문서 분석
├── jd_analysis.yaml            # JD 분석
├── question_generation.yaml    # 질문 생성 (13개 프롬프트 키)
├── quality_review.yaml         # 품질 검토
├── finalization.yaml           # 최종화 (6개 프롬프트 키)
└── v2_generation.yaml          # v2 Intel/Analysis/Decision (5개 프롬프트 키)
```

### 프롬프트 키 → Activity 매핑 전체

| YAML 파일 | 프롬프트 키 | 사용 Activity | 설명 |
|-----------|------------|--------------|------|
| `document_analysis.yaml` | `extract_profile` | `analyze_documents` | 이력서/포트폴리오 프로필 추출 |
| `jd_analysis.yaml` | `analyze` | `analyze_jd` | JD 구조화 추출 |
| `question_generation.yaml` | `select_topics` | `select_topics` | 20개 토픽 선정 |
| `question_generation.yaml` | `craft_question` | `craft_question` | 범용 질문 생성 (fallback) |
| `question_generation.yaml` | `craft_question_role_fit` | `craft_question` | role_fit 카테고리 특화 |
| `question_generation.yaml` | `craft_question_technical_depth` | `craft_question` | technical_depth 카테고리 특화 |
| `question_generation.yaml` | `craft_question_execution_ownership` | `craft_question` | execution_ownership 카테고리 특화 |
| `question_generation.yaml` | `craft_question_communication` | `craft_question` | communication 카테고리 특화 |
| `question_generation.yaml` | `craft_question_risk_flags` | `craft_question` | risk_flags 카테고리 특화 |
| `question_generation.yaml` | `enhance_terminology` | `enhance_terminology` | 전문용어 비개발자 설명 |
| `question_generation.yaml` | `craft_evaluation_scenarios` | `craft_evaluation_scenarios` | 3단계 평가 시나리오 |
| `question_generation.yaml` | `design_follow_ups` | `design_follow_ups` | 후속 질문 분기 설계 |
| `question_generation.yaml` | `generate_interviewer_notes` | `generate_interviewer_notes` | 면접관 참고 노트 |
| `question_generation.yaml` | `generate_decision_guide` | `generate_decision_guide` | 채용 의사결정 가이드 |
| `question_generation.yaml` | `revise_questions` | `revise_questions` | 피드백 기반 질문 수정 |
| `quality_review.yaml` | `review` | `review_questions` | 질문 품질 검토 |
| `finalization.yaml` | `candidate_summary` | `finalize_output` | 후보자 종합 요약 |
| `finalization.yaml` | `interviewer_guide` | `finalize_output` | 면접관 가이드 |
| `finalization.yaml` | `final_synthesis` | (예비) | 최종 종합 |
| `finalization.yaml` | `generate_intel_brief` | (예비) | Intel Brief |
| `finalization.yaml` | `generate_deep_analysis` | (예비) | Deep Analysis |
| `finalization.yaml` | `generate_decision_support` | (예비) | Decision Support |
| `v2_generation.yaml` | `competency_matching` | `generate_intel_brief` | JD-후보자 역량 시맨틱 매칭 |
| `v2_generation.yaml` | `radar_analysis` | `generate_deep_analysis` | 5축 레이더 점수 산출 |
| `v2_generation.yaml` | `engineering_dna` | `generate_deep_analysis` | Engineering DNA 분석 |
| `v2_generation.yaml` | `decision_summary` | `generate_decision_support` | 의사결정 요약 생성 |
| `v2_generation.yaml` | `interviewer_tips` | `generate_decision_support` | 면접관 팁 생성 |

---

## 7. 외부 서비스 의존성

### 서비스 의존성 매트릭스

| 외부 서비스 | 사용 Activity | 용도 | 필수 여부 |
|------------|--------------|------|-----------|
| **Kimi K2.5** (Moonshot AI) | 대부분 LLM Activity | 주요 LLM 모델 | 필수 |
| **GLM-4.7** (Zhipu AI) | `analyze_single_repo` | 코드 분석 전용 (비용 최적화) | 코드 분석 시 필수 |
| **PostgreSQL 16** | `persist_result`, KG 관련 | Job 상태 저장, Knowledge Graph 스토어 | 필수 |
| **pgvector** | `analyze_documents`, `analyze_code`, `select_topics`, `craft_question` | 프로필/코드 벡터 임베딩 저장 및 시맨틱 검색 | 권장 (없으면 fallback) |
| **Redis 7** | `CachedLLMService` | LLM 응답 캐시 | 권장 (없으면 캐시 비활성화) |
| **Langfuse** | `start_job_trace`, `end_job_trace`, `@observe_activity` | LLM Observability, 트레이싱, 품질 점수 | 선택 |
| **Bright Data API** | `enrich_input` | LinkedIn 프로필 수집 | 선택 (없으면 LinkedIn 미사용) |
| **GitHub API** (PyGithub) | `enrich_input`, `create_execution_plan`, `analyze_code` | 레포 메타데이터, 언어 감지 | 코드 분석 시 필수 |
| **LocalStack S3 / AWS S3** | `finalize_output` | 최종 스크립트 JSON 저장 | 필수 |
| **httpx** | `send_webhook` | Webhook 콜백 전송 | 선택 |

### 환경변수 의존성

| 환경변수 | 기본값 | 영향 범위 |
|---------|--------|-----------|
| `LLM_MODEL` | `moonshot/moonshot-v1-auto` | 전체 Activity 기본 모델 |
| `LLM_FALLBACK_MODEL` | GPT-4o | Fallback 체인 |
| `GLM_CODER_MODEL` | `zai/glm-4.7` | `analyze_single_repo` 코드 분석 |
| `LLM_CACHE_ENABLED` | `true` | Redis 캐시 on/off |
| `LLM_MAX_OUTPUT_TOKENS` | 모델별 상이 | 응답 최대 토큰 수 |
| `GITHUB_ANALYSIS_YEARS` | 3 | 코드 분석 대상 기간 (년) |
| `REDIS_PASSWORD` | - | Redis 인증 |
| `INTERNAL_API_TOKEN` | - | Worker-Backend 내부 인증 |
| `DB_POOL_SIZE` | 10 | PostgreSQL 커넥션 풀 |

---

## 8. 모델 설정 및 비용 구조

### 현재 모델 설정 (`llm_config.py`)

| 모델 변수 | 모델명 | Context 길이 | 비용 (1M 토큰) | 용도 |
|-----------|--------|-------------|---------------|------|
| `KIMI_K2_5_MODEL` | `moonshot/moonshot-v1-auto` | 256K | $0.06 / $0.18 (input/output) | 전체 Activity 기본 모델 |
| `KIMI_K2_MODEL` | `moonshot/moonshot-v1-128k` | 128K | $0.06 / $0.18 | 레거시 호환 |
| `GLM_CODER_MODEL` | `zai/glm-4.7` | - | $0.60 / $2.20 | HYBRID 코드 분석 전용 |
| `GLM_CHAT_MODEL` | `zai/glm-4.5-flash` | - | 무료 | (현재 미사용, 병렬 제한) |

### Activity별 모델 할당

```
Phase 0: enrich_input              → Kimi K2.5 (실제 LLM 미호출)
Phase 1: select_topics             → Kimi K2.5
Phase 2: analyze_documents         → Kimi K2.5
Phase 2: analyze_jd                → Kimi K2.5
Phase 2: analyze_code              → Kimi K2.5 (Coder)
Phase 2: code_overview_analysis    → Kimi K2.5 (Coder)  ← 설정상, 실제 GLM-4.7 사용
Phase 2: code_deep_analysis        → Kimi K2.5 (Coder)  ← 설정상, 실제 GLM-4.7 사용
Phase 2: code_synthesis_analysis   → Kimi K2.5 (Coder)  ← 설정상, 실제 GLM-4.7 사용
Phase 3: craft_question            → Kimi K2.5
Phase 3: enhance_terminology       → Kimi K2.5
Phase 3: craft_evaluation_scenarios → Kimi K2.5
Phase 3: design_follow_ups        → Kimi K2.5
Phase 3: generate_interviewer_notes → Kimi K2.5
Phase 3: generate_decision_guide   → Kimi K2.5
Phase 3: revise_questions          → Kimi K2.5
Phase 4: quality_review            → Kimi K2.5
Phase 4: finalize_candidate_summary → Kimi K2.5
Phase 4: finalize_interviewer_guide → Kimi K2.5
```

> **참고**: `analyze_single_repo`는 `llm_config.py`의 `ACTIVITY_MODEL_CONFIG`와 별도로 코드 내에서 직접 `GLM_MODEL = settings.GLM_CODER_MODEL` (`zai/glm-4.7`)을 사용한다. `v2_generation` 관련 Activity들(`generate_intel_brief`, `generate_deep_analysis`, `generate_decision_support`)은 내부에서 `CachedLLMService()`를 기본 생성하므로 `ACTIVITY_MODEL_CONFIG`의 기본 설정을 따른다.

### 모델별 최대 출력 토큰

| 모델 프리픽스 | max_output_tokens |
|-------------|-------------------|
| `moonshot/` | 16,384 |
| `zai/glm-4.5-flash` | 4,096 |
| `zai/` (기타) | 8,192 |
| `openai:` / `openai/` | 16,384 |
| `anthropic:` / `anthropic/` | 8,192 |

### Retry 정책

| 정책 이름 | 용도 | 초기 간격 | 백오프 계수 | 최대 간격 | 최대 시도 |
|----------|------|----------|-----------|----------|----------|
| `DEFAULT_RETRY` | 일반 Activity | 1초 | 2.0 | 30초 | 3회 |
| `LLM_RETRY` | LLM 호출 Activity | 2초 | 2.0 | 60초 | 3회 |
| `EXTERNAL_API_RETRY` | 외부 API (GitHub, LinkedIn) | 3초 | 2.0 | 120초 | 4회 |

---

## 부록: 경험 레벨별 질문 배분

### 카테고리 배분 (총 20개 질문)

| 경험 레벨 | role_fit | technical_depth | execution_ownership | communication | risk_flags |
|----------|----------|-----------------|---------------------|---------------|------------|
| **신입** | 6 (30%) | 5 (25%) | 3 (15%) | 4 (20%) | 2 (10%) |
| **주니어** | 6 (30%) | 5 (25%) | 3 (15%) | 4 (20%) | 2 (10%) |
| **미들** | 5 (25%) | 4 (20%) | 4 (20%) | 4 (20%) | 3 (15%) |
| **시니어** | 3 (15%) | 4 (20%) | 5 (25%) | 4 (20%) | 4 (20%) |
| **CTO/VP** | 3 (15%) | 3 (15%) | 5 (25%) | 4 (20%) | 5 (25%) |

### 카테고리 가중치 (평가 점수 계산용)

| 경험 레벨 | role_fit | technical_depth | execution_ownership | communication | risk_flags |
|----------|----------|-----------------|---------------------|---------------|------------|
| **신입** | 0.30 | 0.25 | 0.15 | 0.20 | 0.10 |
| **주니어** | 0.30 | 0.25 | 0.15 | 0.20 | 0.10 |
| **미들** | 0.25 | 0.20 | 0.20 | 0.20 | 0.15 |
| **시니어** | 0.15 | 0.20 | 0.25 | 0.20 | 0.20 |
| **CTO/VP** | 0.15 | 0.15 | 0.25 | 0.20 | 0.25 |
