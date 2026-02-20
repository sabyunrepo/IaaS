---
title: "Code Evolution Strategy"
type: component
layer: domain
parent: "[[domain/question-generation/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-107"]
---

# Code Evolution (전략 C)

## 핵심 원리

**Git 히스토리에서 Code Churn이 높았던 구간, 대규모 리팩토링 지점**을 추적하여 코드의 변화 과정을 질문한다.

코드의 변화 과정을 아는 것은 실제로 그 코드를 작성하고 유지보수한 사람만이 가능하다. AI가 대신 작성한 코드라면 수정 이력의 맥락을 설명하지 못한다.

- **합격 신호**: 초기 설계의 구체적 문제점과 해결 과정을 서술 (해당 코드를 직접 고민해본 사람만 답변 가능)
- **불합격 신호**: 최종 결과물만 설명 (AI는 수정 역사를 모름)

## 분석 로직

```
PyDriller + Git 히스토리 분석:
  1. 파일별 Code Churn(수정 빈도 × 수정 크기) 계산
  2. Churn 상위 10% 파일/모듈 식별
  3. 동일 모듈의 대규모 구조 변경 커밋 (diff > 100줄) 추적
  4. 리팩토링 패턴 커밋 메시지 감지 ("refactor", "rewrite", "redesign")
  → 위 조건을 충족하는 모듈을 질문 대상으로 선정
```

## 질문 예시

```
질문: "PaymentGateway 모듈이 초기 버전에서 3번 구조가 크게 바뀌었습니다.
      초기 설계에서 예상하지 못했던 문제는 구체적으로 무엇이었나요?"

검증 포인트:
  합격: "처음에는 동기 처리로 구현했는데, 결제 요청이 동시에 몰리면서
         타임아웃이 발생했습니다. 그래서 큐 기반 비동기 처리로 전환했습니다",
        "초기에는 단일 결제사만 지원했는데 다중 PG사 추가 요구가 생겨서
         Strategy 패턴으로 리팩토링했습니다"
  불합격: "최종 버전이 더 깔끔해서 바꿨습니다" (과정 설명 불가),
           "팀원이 바꿨습니다" (자신의 작업이 아님)
```

## Git Churn 분석

```python
# infrastructure/github/churn_analyzer.py
from pydriller import Repository

def calculate_code_churn(repo_path: str, file_path: str) -> dict:
    """파일별 Code Churn 계산"""
    churn_data = {"commits": 0, "additions": 0, "deletions": 0, "churn_score": 0.0}

    for commit in Repository(repo_path, filepath=file_path).traverse_commits():
        for modified_file in commit.modified_files:
            if modified_file.filename in file_path:
                churn_data["commits"] += 1
                churn_data["additions"] += modified_file.added_lines
                churn_data["deletions"] += modified_file.deleted_lines

    # Churn Score = (additions + deletions) / commits (수정 당 변경량)
    if churn_data["commits"] > 0:
        churn_data["churn_score"] = (
            churn_data["additions"] + churn_data["deletions"]
        ) / churn_data["commits"]

    return churn_data
```

## 프롬프트 구성

```python
# infrastructure/llm/prompts/code_evolution.yaml
system: |
  당신은 코드 리뷰 전문가입니다.
  Git 히스토리에서 구조가 크게 변경된 모듈을 분석하여,
  개발자의 설계 진화 과정을 검증하는 질문을 작성하세요.

  규칙:
  - Fact-Grounded: "해당 모듈은 {commit_count}회 대규모 구조 변경이 있었습니다"
  - 변경 이력의 구체적 수치(커밋 수, 변경 규모) 포함
  - "최종 결과물"이 아닌 "변화 과정"에 집중한 질문
```

## 코드 예시 (QuestionCrafter)

```python
# application/question/question_crafter.py
async def craft_evolution_question(
    module_name: str,
    file_path: str,
    refactor_commits: list[dict],
    churn_score: float,
    jd_context: dict,
) -> InterviewQuestion:
    """전략 C: 코드 변경 이력 기반 질문 생성"""
    topic = {
        "strategy": "evolution",
        "module_name": module_name,
        "file_path": file_path,
        "refactor_history": {
            "commit_count": len(refactor_commits),
            "churn_score": churn_score,
            "major_changes": [
                {"sha": c["sha"][:8], "message": c["message"], "diff_size": c["diff_size"]}
                for c in refactor_commits[:3]  # 상위 3개 주요 변경만 포함
            ],
        },
    }
    return await generate_question(topic=topic, context=jd_context)
```

## 출력 필드에서 전략별 특성

| 필드 | Code Evolution 특성 |
|------|---------------------|
| `strategy` | `"evolution"` |
| `intent` | "직접 작성 및 유지보수 진정성 검증" |
| `code_reference` | Churn이 높은 파일:라인 범위 |
| `red_flags` | `["최종 결과물만 설명", "과정 설명 불가", "타인 작업으로 미루기"]` |
| `follow_up_triggers` | `["변화 과정 설명 미흡 시 → 특정 커밋의 변경 이유를 재질문"]` |

## 진정성 지표와의 연결

Code Evolution 분석에서 사용하는 Code Churn 데이터는 4대 지표 중 **안정성(20%)** 산출의 "리워크 비율(Churn)" 세부 지표로도 활용된다. PyDriller가 담당하며 `Worker W7`이 처리한다.
