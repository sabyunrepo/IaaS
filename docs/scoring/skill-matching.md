# Skill Matching (스킬 매칭)

> 코드: `analysis_generation.py:_build_skill_table()` (규칙 기반) + `_llm_build_skill_table()` (LLM 기반)
> 반환: `list[SkillMatchRow]` — skill, candidate, type, evidence, confidence

## 개요

JD 요구 스킬과 후보자 보유 스킬을 매칭하여 **매칭 타입**, **근거**, **신뢰도**를 산출.
LLM 매칭을 우선 시도하고, 실패 시 규칙 기반 매칭으로 fallback.

## 매칭 파이프라인

```
1. LLM 매칭 시도 (_llm_build_skill_table)
   ↓ 실패 시
2. 규칙 기반 매칭 (_build_skill_table)
```

## 매칭 타입

| 타입 | 의미 | 신뢰도 범위 | 예시 |
|------|------|------------|------|
| `exact` | 정확히 일치 | 90-100 | JD "Python" ↔ 후보자 "Python" |
| `similar` | 유사 매칭 (부분 포함) | 70-80 | JD "React.js" ↔ 후보자 "React" |
| `partial` | 부분 매칭 (코드에서 발견) | 60-65 | JD "Docker" ↔ GitHub에서 Docker 사용 흔적 |
| `none` | 매칭 실패 | 0 | JD 요구 스킬을 어디에서도 확인 불가 |

## 규칙 기반 매칭 로직 (2단계)

### 1단계: 이력서 스킬 매칭

```
for each JD requirement:
  for each resume skill:
    if exact match     → type=exact,  confidence=95
    if substring match → type=similar, confidence=70-75
```

- 양방향 substring 매칭 (JD ⊂ Resume OR Resume ⊂ JD)
- 길이 가드: 3자 이상만 substring 매칭 허용

### 2단계: GitHub 코드 스킬 매칭 (보강)

```
for each JD requirement:
  for each code tech_stack skill:
    if exact match     → type=exact,  confidence=90
    if substring match → type=partial, confidence=60-65
```

### 이중 소스 보강

```
Resume 매칭 + GitHub 매칭 모두 확인 시:
  evidence = "Resume: {skill} listed + GitHub: {skill} detected"
  confidence = min(100, original_confidence + 5)
```

## LLM 기반 매칭

- 프롬프트: `v2_generation.yaml:skill_matching`
- 입력: JD 요구사항 + 후보자 이력서 스킬 + GitHub 코드 스킬
- 출력: 구조화된 매칭 테이블 (skill, candidate, type, evidence, confidence)
- 장점: 시맨틱 유사도 판단 가능 (예: "AWS" ↔ "Cloud Infrastructure")

## Weighted Overlap Score (가중 겹침률)

스킬 테이블 결과를 종합하여 overall_match의 `skill_match` 구성요소를 산출:

```python
for each skill_row:
  category = JD에서의 카테고리 ("필수" or "우대")
  weight = 1.0 if "필수" else 0.5
  weighted_sum += confidence × weight
  total_weight += weight × 100

skill_match = (weighted_sum / total_weight) × 100
```

- **필수 스킬**: 가중치 1.0 (매칭 실패 시 전체 점수에 큰 영향)
- **우대 스킬**: 가중치 0.5 (보너스 성격)

## 품질 검증

매칭 후 자동 품질 로그:
- `no_evidence`: 근거 없는 행 수 (전체의 50% 초과 시 경고)
- `zero_conf`: 신뢰도 0인 행 수
- `type_conf_mismatch`: 타입↔신뢰도 불일치 (exact인데 confidence < 70 등)

## 정렬 규칙

- 필수 스킬 우선 정렬 (필수 → 우대)
- 최대 15개 행 (Issue #245)

## 코드 위치

- 규칙 기반: `analysis_generation.py:_build_skill_table()` (500-604)
- LLM 기반: `analysis_generation.py:_llm_build_skill_table()` (400-498)
- 호출 위치: `analysis_generation.py:682-687`
- 모델 정의: `models/deep_analysis.py:SkillMatchRow`
- UI 표시: `DeepAnalysisTab.tsx` (스킬 매칭 테이블)
