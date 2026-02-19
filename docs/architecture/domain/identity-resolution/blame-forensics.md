---
title: Blame Forensics (3단계 포렌식 쿼리)
type: component
parent: "[[domain/identity-resolution/MOC]]"
depends-on:
  - "[[domain/identity-resolution/dynamic-mailmap]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Blame Forensics

Identity Resolution Step 3. `IdentityCluster`를 기반으로 blame 라인을 필터링하고, AST Pruning을 거쳐 **순수 로직 기여분(PureContribution)**만 추출한다.

## 3단계 포렌식 쿼리 구조

```
Level 1 (Git Internal):
  git blame -w -M -C -C --line-porcelain
  -> 공백(-w), 파일 이동(-M), 코드 복사(-C) 제외한 순수 로직 작성분만 추출

Level 2 (Semantic Pruning):
  Tree-sitter AST 파싱 ->
  import 구문, 주석, Config 설정, 자동 생성 코드(Generated Code) 제거 ->
  함수/클래스 본문만 보존

Level 3 (Authenticity Check):
  Vibector(WPM) + CLAVE(스타일로메트리) + Datasketch(표절) 교차 검증
```

## Level 1: git blame 옵션 설명

| 옵션 | 의미 | 제거 대상 |
|------|------|----------|
| `-w` | 공백 변경 무시 | 들여쓰기 수정, 줄 끝 공백 정리 등 |
| `-M` | 파일 내 코드 이동 감지 | 함수/블록을 같은 파일 내에서 이동한 커밋 |
| `-C -C` | 파일 간 코드 복사 감지 | 다른 파일에서 복사한 코드, 파일 리네임 |
| `--line-porcelain` | 기계 파싱용 출력 형식 | — |

`-C -C` (이중 `-C`)는 단순 리네임뿐 아니라 파일 간 복사까지 추적한다. 이 옵션들의 조합으로 `BlameLineAttribution.is_move`, `is_copy`, `is_whitespace_only` 필드가 채워진다.

## Level 2: AST Pruning

Tree-sitter를 사용해 소스 파일을 AST로 파싱한 후, 다음 노드 유형을 제거한다.

| 제거 대상 | Tree-sitter 노드 유형 (예시) | 이유 |
|----------|---------------------------|------|
| import 구문 | `import_statement`, `import_from_statement` | 의존성 선언, 로직 아님 |
| 주석 | `comment`, `block_comment` | 설명 텍스트, 로직 아님 |
| Config 설정 | `assignment` (최상위 상수, `settings.py` 패턴) | 환경 설정, 알고리즘 아님 |
| 자동 생성 코드 | `# generated`, `# auto-generated` 헤더 파일 | 툴 생성, 본인 작성 아님 |

제거 후 **함수 본문(`function_definition`)과 클래스 본문(`class_definition`)만 보존**된다. 이것이 `PureContribution.function_bodies`에 저장된다.

## Level 3: Authenticity Check

| 도구 | 검증 항목 | 출력 지표 |
|------|----------|---------|
| Vibector | 인간 타이핑 속도 (WPM) 분석 | `human_typing_ratio` |
| CLAVE | 코딩 스타일로메트리 일관성 | `style_consistency` |
| Datasketch (LSH) | 코드 표절/복사 비율 | `plagiarism_ratio` |

세 도구의 교차 검증 결과가 `AuthenticityScore` 모델([[domain/identity-resolution/models]] 참조)로 집약된다.

## PureContribution 산출

Level 1~2를 통과한 blame 라인만을 집계하여 `PureContribution`을 구성한다.

```
total_lines          = 전체 blame 라인 수
pure_logic_lines     = total_lines - removed_imports - removed_comments
                       - removed_config - removed_generated
                       - is_move 라인 - is_copy 라인 - is_whitespace_only 라인

function_bodies      = Level 2 AST Pruning 후 보존된 함수/클래스 본문 목록
```

`pure_logic_lines`와 `function_bodies`는 Scoring Calculator의 **진정성(Authenticity) 지표** 산출에 직접 사용된다.

```
Index_authenticity = (LoC_total - LoC_AI - LoC_copy) / LoC_total * 100
```

## 연관 Linear 티켓

- JIT-88: Blame Filter (blame 라인 필터링, identity_cluster 기반)
- JIT-89: Semantic Pruner 규칙 (AST 노이즈 제거: import, 주석, config, generated)
