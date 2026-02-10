# Radar 5축 점수 (Radar Scores)

> 코드: `scoring_formulas.py:calculate_radar_scores()`
> 반환: `RadarScores(candidate, required, sources, confidence, human_sources)`

## 5축 정의

| 축 | 라벨 | 의미 |
|----|------|------|
| 0 | Role Fit (역할 적합도) | JD 요구사항과 후보자 스킬의 매칭도 |
| 1 | Technical (기술 역량) | 코드 품질, 기술 폭, 기여 일관성 |
| 2 | Execution (실행력) | 경력 수준, 커밋 일관성, 코드 볼륨 |
| 3 | Communication (커뮤니케이션) | 문서화 능력, 코드 가독성 |
| 4 | Code Quality (코드 품질) | 종합 코드 품질 지표 |

## 계산 공식

### Axis 0: Role Fit
```
role_fit = jd_match × 70% + weighted_skill_overlap × 30%
```
- `jd_match`: JD 분석에서 산출된 매칭 점수 (0-1)
- `weighted_skill_overlap`: 후보자 스킬 vs JD 필수 스킬 겹침률 (가중 Jaccard)

### Axis 1: Technical Depth
```
technical = code_quality_score × 40% + jd_tech_breadth × 30% + consistency × 30%
```
- `code_quality_score`: McCabe 복잡도 + 테스트 커버리지 + 문서화 종합
- `jd_tech_breadth`: JD 기술 요구사항 충족 비율
- `consistency`: GitHub 커밋 패턴 일관성

### Axis 2: Execution & Delivery
```
execution = sfia_exp × 40% + commit_consistency × 30% + code_volume × 30%
```
- `sfia_exp`: SFIA v9 프레임워크 기반 경험 수준 점수
- `commit_consistency`: 최근 12개월 커밋 빈도 표준편차
- `code_volume`: 총 코드 기여량 정규화

### Axis 3: Communication
```
communication = doc_score × 50% + readability × 50%
```
- `doc_score`: README, 주석, docstring 비율
- `readability`: McCabe 복잡도 역수 (낮을수록 읽기 쉬움)

### Axis 4: Code Quality
```
code_quality = composite(code_quality_score)
```
- McCabe (1976) 순환 복잡도 기반 종합 점수
- 구성: `cyclomatic × 30% + halstead × 20% + maintainability × 25% + test_coverage × 25%`

## Required Scores (기대 점수)

경험 레벨별 기대 점수 (`calculate_required_scores()`):

| 레벨 | Role Fit | Technical | Execution | Communication | Code Quality |
|------|----------|-----------|-----------|---------------|--------------|
| CTO/VP | 90 | 85 | 90 | 85 | 80 |
| Senior | 80 | 75 | 80 | 70 | 70 |
| Mid | 65 | 60 | 60 | 55 | 55 |
| Junior | 50 | 45 | 40 | 40 | 40 |
| Entry | 35 | 30 | 25 | 30 | 30 |

## 학술 출처

- **SFIA v9**: Skills Framework for the Information Age (sfia-online.org)
- **McCabe (1976)**: "A Complexity Measure" - IEEE Transactions on Software Engineering
- **Dreyfus Model**: 기술 습득 5단계 모델 (Novice → Expert)

## 비개발자 해석 예시

| 점수 범위 | 해석 |
|----------|------|
| 80-100 | 해당 영역에서 매우 뛰어난 역량. 즉시 기여 가능 |
| 60-79 | 업계 평균 이상. 안정적인 성과 기대 |
| 40-59 | 보통 수준. 성장 가능성은 있으나 지원 필요 |
| 0-39 | 해당 영역 경험 부족. 집중 교육/멘토링 필요 |
