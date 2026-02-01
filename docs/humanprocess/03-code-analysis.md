# 03. 코드 분석 (GitHub)

> Git Clone + Claude Code를 활용한 실제 코드 심층 분석

---

## 목표

지원자의 GitHub 저장소를 로컬에 클론하고, Claude Code를 사용하여 코드 패턴, 설계 능력, 면접 질문 후보를 추출합니다.

---

## 전체 시퀀스

```
[1] 저장소 선정
    ↓
[2] Git Clone (로컬)
    ↓
[3] Claude Code 실행
    ↓
[4] 저장소 구조 분석 (프롬프트 1)
    ↓
[5] 코드 품질 분석 (프롬프트 2)
    ↓
[6] 패턴/아키텍처 분석 (프롬프트 3)
    ↓
[7] 면접 질문 후보 추출 (프롬프트 4)
    ↓
[8] 결과 정리 및 저장
```

---

## 사전 준비

### 필요 도구

| 도구 | 설치 확인 | 용도 |
|------|-----------|------|
| **Git** | `git --version` | 저장소 클론 |
| **Claude Code** | `claude --version` | 코드 분석 |
| **VS Code** (선택) | - | 코드 브라우징 |

### Claude Code 설치 (미설치 시)

```bash
# npm으로 설치
npm install -g @anthropic-ai/claude-code

# 또는 brew (Mac)
brew install claude-code
```

---

## Step 1: 저장소 선정 및 Clone

### 1.1 분석할 저장소 선정

**우선순위 기준:**
1. JD와 관련된 기술 스택 사용
2. 최근 활동이 있는 저장소 (1년 이내)
3. 본인이 주요 기여자
4. README가 있고 프로젝트 설명이 있는 것

### 1.2 Git Clone

```bash
# 작업 디렉토리 생성
mkdir -p ~/interview-analysis/candidates/[지원자이름]
cd ~/interview-analysis/candidates/[지원자이름]

# 저장소 클론 (최대 3개 권장)
git clone https://github.com/username/repo1.git
git clone https://github.com/username/repo2.git

# 클론 완료 확인
ls -la
```

### 1.3 저장소 크기 확인

```bash
# 너무 큰 저장소는 분석에 시간이 오래 걸림
du -sh repo1/
du -sh repo2/

# 100MB 이상이면 주요 폴더만 분석 권장
```

---

## Step 2: Claude Code 실행

### 2.1 Claude Code 시작

```bash
# 클론한 저장소 디렉토리로 이동
cd ~/interview-analysis/candidates/[지원자이름]/repo1

# Claude Code 실행
claude
```

### 2.2 MCP 설정 (선택사항)

Claude Code에서 파일시스템 MCP가 활성화되어 있으면 더 효율적입니다.

```json
// ~/.claude/config.json 에 추가 (이미 설정되어 있을 수 있음)
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "/path/to/allowed/directory"]
    }
  }
}
```

---

## Step 3: 저장소 구조 분석

### 프롬프트 1: 전체 구조 파악

Claude Code에서 다음 명령 실행:

```
이 저장소의 전체 구조를 분석해줘.

다음 정보를 JSON 형식으로 정리해줘:
1. 프로젝트 유형 (웹서버, CLI, 라이브러리 등)
2. 사용 언어 및 프레임워크
3. 디렉토리 구조 설명
4. 주요 진입점 파일
5. 설정 파일 목록 (package.json, requirements.txt 등)
6. 테스트 존재 여부

출력 형식:
{
  "project_type": "",
  "main_language": "",
  "frameworks": [],
  "directory_structure": {
    "설명": "각 주요 디렉토리의 역할"
  },
  "entry_points": [],
  "config_files": [],
  "has_tests": true/false,
  "test_framework": ""
}
```

### 예상 응답 활용

Claude Code가 분석 결과를 제공하면, 이를 메모장에 저장합니다.

---

## Step 4: 코드 품질 분석

### 프롬프트 2: 코드 품질 평가

```
이 프로젝트의 코드 품질을 분석해줘.

다음 항목을 평가해줘:
1. 코드 구조화 수준 (모듈화, 관심사 분리)
2. 네이밍 컨벤션 준수 여부
3. 에러 핸들링 방식
4. 타입 힌트/타입 정의 사용 여부
5. 주석 및 문서화 수준
6. 하드코딩된 값이 있는지
7. 보안 관련 이슈 (있다면)

각 항목을 1-5점으로 평가하고, 구체적인 예시를 코드와 함께 보여줘.

출력 형식:
{
  "scores": {
    "modularity": {"score": N, "reason": "", "example_file": ""},
    "naming": {"score": N, "reason": "", "example": ""},
    "error_handling": {"score": N, "reason": "", "example_file": ""},
    "type_safety": {"score": N, "reason": ""},
    "documentation": {"score": N, "reason": ""},
    "hardcoding": {"score": N, "issues": []},
    "security": {"score": N, "issues": []}
  },
  "overall_score": N,
  "strengths": [],
  "improvements_needed": []
}
```

---

## Step 5: 패턴 및 아키텍처 분석

### 프롬프트 3: 설계 패턴 탐지

```
이 프로젝트에서 사용된 설계 패턴과 아키텍처를 분석해줘.

다음을 찾아줘:
1. 사용된 디자인 패턴 (Singleton, Factory, Repository, Strategy 등)
2. 아키텍처 패턴 (MVC, Clean Architecture, Hexagonal 등)
3. 의존성 주입 사용 여부
4. 비동기 처리 방식
5. 데이터베이스 접근 패턴 (ORM, Raw SQL 등)
6. API 설계 방식 (REST, GraphQL 등)
7. 특이하거나 인상적인 구현

각 패턴에 대해 실제 코드 위치와 스니펫을 포함해줘.

출력 형식:
{
  "design_patterns": [
    {
      "pattern": "패턴명",
      "file": "파일 경로",
      "line_range": "시작-끝",
      "code_snippet": "관련 코드 (20줄 이내)",
      "explanation": "왜 이 패턴을 사용했는지 추측"
    }
  ],
  "architecture": {
    "type": "아키텍처 유형",
    "layers": ["레이어 목록"],
    "explanation": "설명"
  },
  "notable_implementations": [
    {
      "title": "구현 제목",
      "file": "파일 경로",
      "code_snippet": "코드",
      "why_notable": "왜 주목할 만한지",
      "question_potential": "이것에 대해 물어볼 수 있는 질문"
    }
  ]
}
```

---

## Step 6: 면접 질문 후보 추출

### 프롬프트 4: 코드 기반 질문 생성

```
지금까지 분석한 내용을 바탕으로, 이 코드에 대해 물어볼 수 있는 기술 면접 질문을 생성해줘.

조건:
- 지원자가 이 코드를 직접 작성했다고 가정
- 코드의 구체적인 부분을 근거로 질문
- 단순 암기가 아닌 이해도를 평가하는 질문
- 난이도: easy 3개, medium 4개, hard 3개

각 질문에 대해:
1. 질문 텍스트
2. 질문의 근거가 되는 코드 파일/라인
3. 실제 코드 스니펫
4. 이 질문으로 평가할 수 있는 것
5. 예상되는 좋은 답변의 핵심 포인트

출력 형식:
{
  "code_based_questions": [
    {
      "id": "code-q1",
      "difficulty": "easy/medium/hard",
      "question": "질문 내용",
      "source_file": "파일 경로",
      "line_range": "시작-끝",
      "code_snippet": "```언어\n코드\n```",
      "evaluation_target": "이 질문으로 평가하려는 것",
      "expected_key_points": [
        "좋은 답변에 포함되어야 할 포인트1",
        "포인트2",
        "포인트3"
      ],
      "follow_up": "꼬리 질문"
    }
  ]
}
```

---

## Step 7: 복수 저장소 분석 (선택)

여러 저장소를 분석하는 경우:

### 프롬프트 5: 저장소 간 비교

```bash
# 다른 저장소로 이동
cd ~/interview-analysis/candidates/[지원자이름]/repo2
claude
```

```
이 저장소도 분석해줘. 이전에 분석한 repo1과 비교했을 때:

1. 기술 스택의 차이점
2. 코드 스타일의 일관성
3. 성장/변화가 보이는 부분
4. 각 저장소에서 보이는 강점

이 지원자의 전반적인 코딩 성향과 역량을 평가해줘.
```

---

## Step 8: 결과 통합 및 저장

### 프롬프트 6: 최종 코드 분석 요약

```
지금까지 분석한 모든 내용을 종합하여 최종 코드 분석 리포트를 작성해줘.

포함할 내용:
1. 분석한 저장소 목록
2. 기술 스택 요약
3. 코드 품질 점수 (평균)
4. 주요 강점 3가지
5. 개선 필요 영역 2가지
6. 면접 질문 추천 TOP 5 (코드 근거 포함)

마크다운 형식으로 출력해줘.
```

### 결과 파일 저장

```bash
# 분석 결과를 파일로 저장
# Claude Code에서:
/결과를 code-analysis-result.md 파일로 저장해줘
```

또는 수동으로 복사하여 저장.

---

## 분석용 커스텀 스킬 (선택)

반복적으로 사용할 경우, Claude Code 스킬로 만들어두면 편리합니다.

### 스킬 생성 방법

```bash
# Claude Code에서
/skill create code-analyzer
```

### 스킬 내용 예시

```markdown
# Code Analyzer Skill

이 스킬은 면접 질문 생성을 위한 코드 분석을 수행합니다.

## 사용법
`/skill code-analyzer` 실행 후 저장소 경로 입력

## 분석 항목
1. 저장소 구조 분석
2. 코드 품질 평가 (1-5점)
3. 설계 패턴 탐지
4. 면접 질문 후보 생성 (10개)

## 출력 형식
- code-analysis-summary.md: 요약 리포트
- code-questions.json: 질문 목록 (JSON)
- notable-code.md: 주목할 만한 코드 스니펫
```

---

## 결과 정리 템플릿

```markdown
# 코드 분석 결과

## 분석 정보
- 지원자: [이름]
- 분석 일시: [날짜]
- 분석 저장소:
  - repo1: [URL]
  - repo2: [URL]

## 기술 스택 요약
| 카테고리 | 기술 |
|----------|------|
| 언어 | Python, TypeScript |
| 프레임워크 | FastAPI, React |
| DB | PostgreSQL, Redis |
| 인프라 | Docker, AWS |

## 코드 품질 점수
| 항목 | 점수 (1-5) |
|------|------------|
| 모듈화 | 4 |
| 네이밍 | 4 |
| 에러 핸들링 | 3 |
| 타입 안정성 | 5 |
| 문서화 | 3 |
| **평균** | **3.8** |

## 발견된 설계 패턴
1. **Repository Pattern** - `app/repositories/`
2. **Dependency Injection** - FastAPI Depends 활용
3. **Factory Pattern** - `app/factories/`

## 주목할 만한 코드

### 1. Redis 캐싱 구현
**파일**: `app/services/cache.py` (Line 45-78)
```python
# 코드 스니펫
```
**주목 이유**: TTL과 캐시 무효화 전략이 잘 구현됨

### 2. 비동기 배치 처리
**파일**: `app/workers/batch.py` (Line 100-150)
```python
# 코드 스니펫
```
**주목 이유**: asyncio.gather를 활용한 효율적인 병렬 처리

## 코드 기반 면접 질문 (TOP 5)

### Q1. [Medium] Redis 캐싱
> "cache.py에서 TTL을 300초로 설정하셨는데, 이 값은 어떻게 결정하셨나요?"

**근거 코드**: `app/services/cache.py:52`
**평가 항목**: 캐시 전략 이해도
**예상 답변 포인트**:
- 데이터 변경 빈도 고려
- 메모리 사용량과 히트율 트레이드오프
- 비즈니스 요구사항 기반 결정

### Q2. [Hard] 동시성 처리
> "batch.py의 process_batch 함수에서 동시 실행 제한을 어떻게 구현하셨나요?"

**근거 코드**: `app/workers/batch.py:120`
...

## 강점
1. 비동기 프로그래밍에 대한 깊은 이해
2. 일관된 코드 스타일
3. 적절한 추상화 레벨

## 개선 필요 영역
1. 테스트 커버리지 부족
2. 에러 메시지 상세화 필요
```

---

## 다음 단계

코드 분석이 완료되면 JD 분석으로 진행합니다.

**다음**: [04. JD 분석](./04-jd-analysis.md)

---

## 팁

- **Private 저장소**: 지원자에게 임시 접근 권한을 요청하거나, 주요 코드 파일만 공유받아 분석

- **대규모 저장소**: `src/` 또는 `app/` 같은 핵심 디렉토리만 집중 분석

- **모노레포**: 지원 포지션과 관련된 패키지/서비스만 선택하여 분석

- **시간 절약**: 프롬프트 4(질문 생성)가 가장 중요하므로, 시간이 부족하면 1-3은 간략히 하고 4에 집중

---

## 자동화 파이프라인 (Temporal Activity)

> 위 수동 프로세스를 자동화한 `analyze_code` Activity의 설계.
> 상세 구현: [03-workflow.md](../architecture/03-workflow.md) 참조

### 기술 스택

| 라이브러리 | 역할 | 비고 |
|-----------|------|------|
| **PyGithub** | GitHub REST API 래퍼 | 레포 메타데이터, 언어 정보 조회 (Phase 1) |
| **PyDriller** | Git 레포 분석 전용 | 커밋 순회, 복잡도, diff, 소스 추출 (Phase 2) |
| **ast** (빌트인) | Python AST 파싱 | 함수/클래스/패턴 구조 추출 (Phase 3) |
| **tree-sitter** | JS/TS AST 파싱 | Python 외 언어 구조 분석 (Phase 3) |
| **radon** (선택) | 추가 정적 분석 | PyDriller에 복잡도 내장이므로 보조용 |

### 4-Phase 파이프라인

```
Phase 1: PyGithub (API) — 레포 선별
  ├─ GET /repos/{owner}/{repo}/languages → 언어 비율 조회
  ├─ JD 기술스택과 매칭 (예: Python ≥30%)
  └─ 매칭되는 레포만 Phase 2로 전달

Phase 2: PyDriller (로컬) — 코드 추출 + 정적 메트릭
  ├─ auto-clone (shallow clone 지원)
  ├─ only_authors=[candidate_username]   → 후보자 커밋만
  ├─ since=3년 전, to=현재               → 기간 필터
  ├─ only_modifications_with_file_types=[".py"]  → JD 매칭 확장자
  └─ 파일별 추출: complexity, nloc, diff, source_code, methods

Phase 3: AST (로컬) — 구조적 코드 분석
  ├─ 대상: Phase 2 상위 N개 (complexity × JD match 기준)
  ├─ Python: ast 모듈 (빌트인)
  ├─ JS/TS: tree-sitter 파서
  ├─ 추출: 함수 시그니처, 클래스 계층, 디자인 패턴, import 구조
  └─ 미지원 언어: fallback → Phase 2 메트릭만 사용

Phase 4: LLM — 의미 분석
  ├─ 파일 랭킹: complexity × JD매칭 × 최신성 점수
  ├─ Phase 2 메트릭 + Phase 3 AST 구조를 컨텍스트로 전달
  ├─ 토큰 예산(30K/레포) 내 상위 파일만 전송
  ├─ 패턴 탐지 + notable implementations 추출
  └─ 벡터 스토어(pgvector) 저장
```

### PyDriller 핵심 API

```python
from pydriller import Repository
from datetime import datetime

for commit in Repository(
    "https://github.com/user/repo.git",
    since=datetime(2023, 1, 30),
    to=datetime(2026, 1, 30),
    only_authors=["candidate"],
    only_modifications_with_file_types=[".py"]
).traverse_commits():
    for file in commit.modified_files:
        file.filename      # 파일명
        file.complexity    # cyclomatic complexity (내장)
        file.nloc          # 코드 라인 수
        file.diff          # unified diff
        file.source_code   # 변경 후 전체 소스
        file.methods       # 변경된 메서드 목록
        file.added_lines   # 추가 라인 수
        file.deleted_lines # 삭제 라인 수
```

### PyGithub 레포 선별 예시

```python
from github import Github

g = Github("access_token")
user = g.get_user("candidate_username")

target_repos = []
for repo in user.get_repos():
    languages = repo.get_languages()
    total = sum(languages.values())
    if total > 0 and languages.get("Python", 0) / total >= 0.3:
        target_repos.append({
            "url": repo.clone_url,
            "name": repo.name,
            "primary_language": repo.language,
            "language_ratio": languages.get("Python", 0) / total,
        })
```

### 제약사항 및 대응

| 제약 | 영향 | 대응 |
|------|------|------|
| Private 레포 | 접근 불가 | 후보자 OAuth 토큰 필요 |
| PyGithub Rate limit | 5,000 req/hr | 인증 토큰 사용, 충분 |
| 대용량 레포 clone | 시간/디스크 | `depth=100` shallow clone |
| 커밋 수 과다 (>1000) | 분석 시간 | 최근 3년 + 파일타입 필터로 축소 |
| LLM 토큰 초과 | 비용/품질 | 파일 랭킹 → 상위 N개만 전송 |
| 오픈소스 기여 | 외부 레포 | GraphQL contributionsCollection (1년×3회) |
