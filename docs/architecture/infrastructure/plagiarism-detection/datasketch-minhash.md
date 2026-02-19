---
title: "Datasketch MinHash/LSH — 코드 유사도 탐지"
type: component
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [datasketch, minhash, lsh, plagiarism, jaccard, infrastructure]
parent: "[[plagiarism-detection/MOC]]"
children: []
depends-on:
  - "[[tree-sitter-ast/query-cursor-api]]"
affects:
  - "[[application/nodes/datasketch-worker]]"
linear: [JIT-97]
phase: 2
---

# Datasketch MinHash/LSH — 코드 유사도 탐지

## 개요

Datasketch 라이브러리의 MinHash + LSH(Locality-Sensitive Hashing)를 사용하여
후보자 코드와 오픈소스 코드의 유사도를 탐지한다.
MinHash는 Jaccard 유사도의 확률적 근사로 O(1) 해시 비교를 제공하며,
LSH는 대규모 코드베이스에서 유사 후보를 빠르게 검색한다.
DatasketchWorker(W5)에서 소비하여 `plagiarism_report`를 생성한다.

## 상세 설계

### 핵심 개념

| 개념 | 설명 |
|------|------|
| Jaccard 유사도 | 두 집합의 교집합 / 합집합 비율. 1에 가까울수록 유사 |
| MinHash | k개의 해시 함수로 집합의 MinHash 서명(signature) 생성. Jaccard 유사도의 근사 |
| LSH | MinHash 서명을 밴드(band)로 분할하여 유사 쌍을 빠르게 탐색 |
| n-gram | 코드를 토큰 n-gram으로 분해하여 집합 표현 (단어 순서 일부 보존) |
| 임계값 | Jaccard >= 0.8이면 유사도 의심 플래그 |

### 알고리즘 흐름

```
후보자 함수 코드
      │
      ▼
토큰화 (공백/줄바꿈 정규화)
      │
      ▼
n-gram 분해 (n=3, 토큰 단위)
      │
      ▼
MinHash 서명 생성 (num_perm=128)
      │
      ├──→ LSH Index 쿼리 → 유사 후보 함수 반환
      │
      └──→ 개별 Jaccard 추정 → 임계값(0.8) 비교
                │
                ▼
        plagiarism_report (유사도 맵)
```

### 코드 예시

#### MinHash 서명 생성

```python
# infrastructure/analysis/datasketch_adapter.py
import re
from datasketch import MinHash, MinHashLSH


def tokenize_code(source_code: str) -> list[str]:
    """소스코드를 토큰 목록으로 변환.

    정규화:
    - 공백/줄바꿈 → 단일 공백
    - 주석 제거 (단순 # // 라인 주석)
    - 문자열 리터럴 → "__STR__" 치환 (내용 비교 방지)
    - 숫자 리터럴 → "__NUM__" 치환
    """
    # 문자열 리터럴 치환
    code = re.sub(r'"[^"]*"', '__STR__', source_code)
    code = re.sub(r"'[^']*'", '__STR__', code)
    # 숫자 리터럴 치환
    code = re.sub(r'\b\d+\b', '__NUM__', code)
    # 단일 라인 주석 제거
    code = re.sub(r'#[^\n]*', '', code)
    code = re.sub(r'//[^\n]*', '', code)
    # 공백 정규화
    tokens = code.split()
    return tokens


def make_ngrams(tokens: list[str], n: int = 3) -> list[str]:
    """토큰 목록을 n-gram 집합으로 변환.

    Args:
        tokens: 토큰 목록
        n: n-gram 크기 (기본 3 — 코드 구조 패턴 포착에 적합)

    Returns:
        ["token1 token2 token3", "token2 token3 token4", ...]
    """
    if len(tokens) < n:
        return [" ".join(tokens)]
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def create_minhash(source_code: str, num_perm: int = 128) -> MinHash:
    """소스코드에서 MinHash 서명 생성.

    Args:
        source_code: 비교할 소스코드 (함수 단위 권장)
        num_perm: 해시 순열 수. 클수록 정확하지만 느림 (기본 128)

    Returns:
        MinHash 서명 객체
    """
    tokens = tokenize_code(source_code)
    ngrams = make_ngrams(tokens, n=3)

    minhash = MinHash(num_perm=num_perm)
    for ngram in ngrams:
        minhash.update(ngram.encode("utf8"))
    return minhash
```

#### LSH Index 구축 및 쿼리

```python
def build_lsh_index(
    reference_functions: list[dict],
    threshold: float = 0.8,
    num_perm: int = 128,
) -> MinHashLSH:
    """참조 함수 코드베이스로 LSH Index 구축.

    Args:
        reference_functions: [{"id": str, "code": str}, ...]
            id: 참조 함수 고유 식별자 (e.g. "repo_name::file::func_name")
            code: 함수 소스코드
        threshold: Jaccard 유사도 임계값 (기본 0.8)
        num_perm: MinHash 순열 수 (create_minhash와 동일하게 설정)

    Returns:
        쿼리 가능한 MinHashLSH 인덱스
    """
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)

    for func in reference_functions:
        minhash = create_minhash(func["code"], num_perm=num_perm)
        lsh.insert(func["id"], minhash)

    return lsh


def query_similar_functions(
    candidate_code: str,
    lsh: MinHashLSH,
    num_perm: int = 128,
) -> list[str]:
    """후보자 함수와 유사한 참조 함수 ID 목록 반환.

    Args:
        candidate_code: 후보자 함수 소스코드
        lsh: build_lsh_index()로 구축한 인덱스
        num_perm: create_minhash()와 동일한 값 사용

    Returns:
        유사한 참조 함수 ID 목록 (Jaccard >= threshold)
    """
    minhash = create_minhash(candidate_code, num_perm=num_perm)
    return lsh.query(minhash)


def estimate_jaccard(code_a: str, code_b: str, num_perm: int = 128) -> float:
    """두 코드 간 Jaccard 유사도 근사값 반환.

    Args:
        num_perm: 클수록 오차 감소 (기본 128 → 오차 약 ±0.05)

    Returns:
        0.0~1.0 사이 유사도 추정값
    """
    minhash_a = create_minhash(code_a, num_perm=num_perm)
    minhash_b = create_minhash(code_b, num_perm=num_perm)
    return minhash_a.jaccard(minhash_b)
```

#### DatasketchWorker(W5) 통합

```python
# application/nodes/datasketch_worker.py
from infrastructure.analysis.datasketch_adapter import (
    build_lsh_index,
    query_similar_functions,
    estimate_jaccard,
)
from infrastructure.analysis.tree_sitter_adapter import TreeSitterAdapter
from infrastructure.analysis.language_detector import detect_language

tree_sitter = TreeSitterAdapter()

# 참조 코드베이스 (오픈소스 함수 모음 — 사전 구축)
# 실제 운영 시 pgvector 또는 별도 캐시에서 로드
REFERENCE_LSH_INDEX: MinHashLSH | None = None


async def datasketch_worker(state: dict) -> dict:
    """W5: 후보자 코드 표절 탐지.

    흐름:
        1. cleaned_diffs에서 후보자 함수 추출 (Tree-sitter)
        2. 함수별 MinHash 생성
        3. LSH Index 쿼리 → 유사 참조 함수 탐색
        4. 유사도 >= 0.8이면 plagiarism_report에 추가
    """
    cleaned_diffs: list[dict] = state["cleaned_diffs"]

    plagiarism_report: dict = {
        "total_functions_scanned": 0,
        "suspicious_count": 0,
        "flagged": [],  # Jaccard >= 0.8 함수 목록
    }

    for diff in cleaned_diffs:
        lang = detect_language(diff["file_path"])
        if lang is None:
            continue

        tree = tree_sitter.parse_code(diff["content"], lang)
        functions = tree_sitter.extract_functions(tree.root_node, lang)
        plagiarism_report["total_functions_scanned"] += len(functions)

        for func in functions:
            func_code = func["node"].text.decode("utf-8")

            # LSH 빠른 탐색
            similar_ids = (
                query_similar_functions(func_code, REFERENCE_LSH_INDEX)
                if REFERENCE_LSH_INDEX
                else []
            )

            for ref_id in similar_ids:
                # 개별 Jaccard 정밀 측정 (참조 코드를 캐시에서 로드)
                ref_code = load_reference_code(ref_id)
                jaccard = estimate_jaccard(func_code, ref_code)

                if jaccard >= 0.8:
                    plagiarism_report["suspicious_count"] += 1
                    plagiarism_report["flagged"].append({
                        "candidate_function": func["name"],
                        "file_path": diff["file_path"],
                        "start_line": func["start_line"],
                        "reference_id": ref_id,
                        "jaccard_similarity": round(jaccard, 4),
                        "confidence": (
                            "HIGH" if jaccard >= 0.95
                            else "MEDIUM" if jaccard >= 0.85
                            else "LOW"
                        ),
                    })

    return {"plagiarism_report": plagiarism_report}


def load_reference_code(ref_id: str) -> str:
    """참조 함수 코드 로드 (캐시/DB에서). stub — 실제 구현 필요."""
    # TODO(JIT-97): pgvector 또는 Redis 캐시에서 로드
    return ""
```

### 임계값 가이드

| Jaccard | 신뢰도 | 해석 |
|---------|--------|------|
| >= 0.95 | HIGH | 거의 동일 코드. 복사 가능성 매우 높음 |
| 0.85–0.94 | MEDIUM | 높은 유사도. 변수명만 변경한 수준 가능 |
| 0.80–0.84 | LOW | 의심 수준. 추가 수동 검토 필요 |
| < 0.80 | - | 탐지 안 함 (정상 범주) |

### pyproject.toml 의존성

```toml
datasketch = ">=1.6.5"
```

## 관련 문서

- 상위: [[plagiarism-detection/MOC]]
- 의존: [[tree-sitter-ast/query-cursor-api]] (함수 단위 추출)
- 설계 원본: `plan/v5-design/phase2-infrastructure.md` §9.1 W5
