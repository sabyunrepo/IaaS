---
title: "Plagiarism Detection"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
linear: [JIT-97]
---

# Plagiarism Detection

> MinHash/LSH 기반 코드 유사도 탐지 어댑터 계층.
> Datasketch 라이브러리를 사용하며, DatasketchWorker(W5)에서 소비된다.
> GitHub 오픈소스 코드와 후보자 코드의 유사도를 판별하여 `plagiarism_report`를 생성한다.

## 설계 결정

- Datasketch MinHash: 확률적 해싱으로 O(1) 유사도 근사
- LSH(Locality-Sensitive Hashing): 대용량 코드베이스에서 유사 후보 빠른 검색
- 함수 단위 청크: Tree-sitter AST로 함수 경계 분리 후 MinHash 적용
- Jaccard 유사도 임계값: 0.8 이상이면 유사도 의심 플래그

## 문서 목록

| 문서 | 설명 |
|------|------|
| [[plagiarism-detection/datasketch-minhash\|datasketch-minhash]] | MinHash/LSH 구현, 코드 예시 |

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure/plagiarism-detection"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 ADR

```dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
```

## 사용 Worker

| Worker | 사용 도구 | 출력 |
|--------|----------|------|
| W5 DatasketchWorker | Datasketch MinHash/LSH | `plagiarism_report` (유사도 맵) |
