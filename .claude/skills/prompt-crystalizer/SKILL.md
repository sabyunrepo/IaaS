---
name: prompt-crystalizer
description: 프롬프트/문서 토큰 압축 스킬. 긴 CLAUDE.md, YAML 프롬프트 등을 효율적으로 압축.
argument-hint: [target-file]
allowed-tools: Read, Write, Edit
---

# Prompt Crystalizer Skill

긴 프롬프트, 문서, 설정 파일의 토큰을 압축합니다.

## 압축 기법

### 1. Activation Signal (활성화 신호)
Claude가 이미 아는 일반 지식을 길게 설명하는 대신, 핵심 키워드로 해당 지식을 "활성화"

**Before** (120 tokens):
```
When writing Python code, you should follow PEP 8 style guidelines which include
using 4 spaces for indentation, limiting lines to 79 characters, using snake_case
for functions and variables, and CamelCase for classes...
```

**After** (15 tokens):
```
Python style: PEP 8 (snake_case, 4-space indent, 79-char lines)
```

### 2. Conditional Expansion (조건부 전개)
상세 내용을 `[조건] → [동작]` 형태로 압축

**Before**:
```
When you encounter a Temporal workflow error, you should first check the worker
logs using docker compose logs, then identify which activity failed, check the
checkpoint status, and suggest a restart point.
```

**After**:
```
Temporal error → check worker logs → identify failed activity → checkpoint → restart point
```

### 3. Reference Delegation (참조 위임)
상세 내용을 별도 파일로 분리하고 참조만 남김

**Before**: SKILL.md에 500줄 상세 설명
**After**: SKILL.md에 50줄 개요 + `See references/details.md`

### 4. Table Compression (테이블 압축)
반복 구조를 테이블로 변환

**Before**: 10개 항목을 각각 설명하는 단락
**After**: `| 항목 | 값 | 설명 |` 테이블

### 5. Deduplication (중복 제거)
글로벌 CLAUDE.md와 프로젝트 CLAUDE.md 간 중복 제거

## 적용 절차

1. **대상 파일 읽기**: 현재 토큰 수 추정
2. **중복 분석**: 다른 설정 파일과 내용 겹침 확인
3. **기법 적용**: 위 5가지 기법을 순서대로 적용
4. **검증**: 압축 후 핵심 정보 누락 없는지 확인
5. **토큰 비교**: 전후 토큰 수 비교 (목표: 50-70% 절감)

## 압축하면 안 되는 것

- 프로젝트 고유 라우팅 테이블 (Auto-Routing Engine)
- 파일 배치 규칙 (File Placement)
- 네이밍 컨벤션 (Naming Conventions)
- 보안 규칙 (Security Rules)
- 프로젝트 특화 비즈니스 로직

## 예상 토큰 절감

| 기법 | 평균 절감율 |
|------|-----------|
| Activation Signal | 70-85% |
| Conditional Expansion | 50-65% |
| Reference Delegation | 60-80% |
| Table Compression | 40-55% |
| Deduplication | 30-50% |
