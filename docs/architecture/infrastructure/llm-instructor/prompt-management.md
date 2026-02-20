---
title: "Prompt Management"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [prompt, langfuse, yaml, versioning, langfuse-first]
parent: "[[llm-instructor/MOC]]"
linear: [JIT-98, JIT-110]
---

# Prompt Management

## 개요

> YAML 파일로 프롬프트를 소스 코드와 함께 관리하고,
> Langfuse에 업로드하여 런타임에 풀링하는 Langfuse-first 아키텍처.
> 프롬프트 변경은 코드 배포 없이 Langfuse 라벨 전환만으로 반영된다.

## 상세 설계

### 핵심 개념

**Langfuse-first 원칙**:
1. YAML 파일은 프롬프트의 소스 오브 트루스 (버전 관리 목적)
2. 런타임에는 항상 Langfuse에서 `production` 라벨로 로드
3. 핫픽스: Langfuse UI에서 직접 편집 후 `production` 라벨 이동 → 즉시 반영 (재배포 불필요)
4. 실험: 새 버전을 `staging` 또는 `experiment-*` 라벨로 배포 → A/B 테스트

### YAML 프롬프트 구조

```
backend/prompts/
├── question_craft_v5.yaml       # 면접 질문 생성
├── skill_extraction_v2.yaml     # 스킬 추출 (W9)
├── clave_analysis_v3.yaml       # 저자 지문 분석 (W4)
├── api_depth_analysis_v1.yaml   # API 깊이 분석 (W10)
├── architecture_eval_v1.yaml    # 아키텍처 평가 (W11)
└── enhancement/
    ├── difficulty_tuner_v1.yaml  # 난이도 조정
    ├── accessibility_v1.yaml     # 비개발자 접근성
    └── verification_v1.yaml     # 검증력 강화
```

### 코드 예시

#### YAML 프롬프트 파일 형식

```yaml
# backend/prompts/question_craft_v5.yaml
name: "question_craft_v5"
version: "5.2"
model: "kimi-k2.5"
temperature: 0.7
max_tokens: 1500
description: "코드 기반 면접 질문 생성 — 3전략 (부정 선택, 코드 진화, 의도적 복잡도)"

system: |
  당신은 시니어 기술 면접관을 보조하는 AI 참모입니다.
  지원자의 실제 GitHub 코드를 분석한 데이터를 바탕으로
  비개발자 면접관도 이해할 수 있는 면접 질문을 생성합니다.

  ## 필수 규칙
  - 질문은 반드시 지원자의 실제 코드/커밋에서 근거를 가져올 것
  - intent 필드: 비개발자가 "왜 이 질문을 하는가"를 이해할 수 있게 설명
  - evidence_refs: 구체적인 파일 경로, 함수명, 커밋 해시 포함
  - follow_up_hints: 답변에서 추가 검증이 필요한 포인트 (최대 3개)
  - NEVER return null for any field

user: |
  ## 분석 대상 토픽
  전략: {{ topic.strategy }}
  코드 근거:
  {{ topic.code_evidence }}

  ## 지원자 컨텍스트
  포지션: {{ context.position }}
  경력: {{ context.career_years }}년
  JD 핵심 역량: {{ context.jd_skills | join(", ") }}

  ## 지시
  위 코드 근거를 바탕으로 면접 질문 1개를 생성하세요.
```

#### 업로드 스크립트

```python
# scripts/upload_prompts_to_langfuse.py
"""
YAML 프롬프트를 Langfuse에 업로드.

사용법:
  # production 라벨로 업로드 (기본)
  docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production

  # staging 라벨로 업로드 (테스트)
  docker compose exec backend python scripts/upload_prompts_to_langfuse.py --label staging

  # 특정 프롬프트만
  docker compose exec backend python scripts/upload_prompts_to_langfuse.py --name question_craft_v5
"""
import argparse
import yaml
from pathlib import Path
from langfuse import Langfuse

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def upload_prompt(langfuse: Langfuse, yaml_path: Path, label: str) -> None:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    langfuse.create_prompt(
        name=data["name"],
        prompt=data["system"],  # 또는 messages 배열
        config={
            "model": data["model"],
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 1500),
        },
        labels=[label],
    )
    print(f"Uploaded: {data['name']} → label={label}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--label", default="staging")
    parser.add_argument("--name", help="특정 프롬프트만 업로드")
    args = parser.parse_args()

    label = "production" if args.production else args.label
    langfuse = Langfuse()

    yaml_files = (
        [PROMPTS_DIR / f"{args.name}.yaml"]
        if args.name
        else list(PROMPTS_DIR.rglob("*.yaml"))
    )

    for yaml_path in yaml_files:
        upload_prompt(langfuse, yaml_path, label)

if __name__ == "__main__":
    main()
```

#### 런타임 프롬프트 로드

```python
# infrastructure/llm/prompt_loader.py
from langfuse import Langfuse
from functools import lru_cache
from dataclasses import dataclass

@dataclass
class CompiledPrompt:
    messages: list[dict]
    model: str
    temperature: float

def load_and_compile(
    prompt_name: str,
    label: str = "production",
    **variables,
) -> CompiledPrompt:
    """Langfuse에서 프롬프트 로드 + 변수 치환"""
    langfuse = get_langfuse()
    prompt = langfuse.get_prompt(prompt_name, label=label)

    return CompiledPrompt(
        messages=prompt.compile(**variables),
        model=prompt.config.get("model", "kimi-k2.5"),
        temperature=prompt.config.get("temperature", 0.7),
    )
```

### 프롬프트 라이프사이클

```
YAML 편집 (로컬)
      │
      ▼
git commit + PR
      │
      ▼
merge → CI/CD: upload_prompts_to_langfuse.py --label staging
      │
      ▼
QA 검증 (staging 라벨 환경)
      │
      ▼
Langfuse UI: staging → production 라벨 이동 (재배포 불필요)
      │
      ▼
런타임 즉시 반영
```

### 핫픽스 절차

긴급 프롬프트 수정 시 (배포 없이):
1. Langfuse UI → Prompts → 해당 프롬프트 → 새 버전 생성
2. 내용 수정 후 저장
3. `production` 라벨을 새 버전으로 이동
4. 런타임 즉시 반영 확인
5. YAML 파일에도 동일 내용 반영 후 커밋 (소스 동기화)

## 관련 문서

- 상위: [[llm-instructor/MOC]]
- 연관: [[llm-instructor/instructor-setup]], [[llm-instructor/langfuse-integration]]
