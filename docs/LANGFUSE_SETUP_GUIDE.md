# Langfuse UI Setup Guide

이 가이드는 Langfuse UI에서 직접 설정해야 하는 항목들을 설명합니다.

## 1. 프로젝트 및 API 키 설정

### 1.1 Langfuse 프로젝트 생성

1. [Langfuse Dashboard](http://localhost:3100) 접속 (로컬) 또는 [Langfuse Cloud](https://cloud.langfuse.com)
2. **New Project** 클릭
3. 프로젝트 이름: `vantict-sniper` 입력
4. **Create** 클릭

### 1.2 API 키 생성

1. 프로젝트 선택 후 **Settings** → **API Keys**
2. **Create API Key** 클릭
3. 키 이름: `vantict-production` 또는 `vantict-development`
4. 생성된 키를 `.env`에 설정:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
LANGFUSE_HOST=http://localhost:3100  # 또는 https://cloud.langfuse.com
```

---

## 2. 프롬프트 관리 설정

### 2.1 프롬프트 버전 관리 활성화

Langfuse에서 프롬프트를 직접 관리하려면:

1. **Prompts** 메뉴 클릭
2. **New Prompt** 클릭
3. 아래 프롬프트들을 등록:

| Prompt Name | Description | Labels |
|-------------|-------------|--------|
| `document_analysis_extract_profile` | 이력서/포트폴리오 프로필 추출 | `production`, `v1.0` |
| `jd_analysis_analyze` | JD 분석 | `production`, `v1.0` |
| `question_generation_select_topics` | 토픽 선정 | `production`, `v1.0` |
| `question_generation_craft_question` | 질문 생성 | `production`, `v1.0` |
| `quality_review_review` | 품질 검토 | `production`, `v1.0` |
| `finalization_candidate_summary` | 후보자 요약 | `production`, `v1.0` |

### 2.2 프롬프트 등록 방법

1. **Prompts** → **New Prompt**
2. **Name**: 위 테이블의 Prompt Name 입력
3. **Prompt Content**: `backend/app/prompts/` 폴더의 해당 YAML 파일에서 template 복사
4. **Variables**: 템플릿의 `{variable_name}` 추출하여 등록
5. **Labels**: `production`, `v1.0` 추가
6. **Save**

### 2.3 프롬프트 A/B 테스트 설정

새 버전 테스트 시:

1. 기존 프롬프트 선택
2. **New Version** 클릭
3. 새 프롬프트 내용 입력
4. **Labels**: `staging`, `v2.0` 설정
5. 코드에서 버전 지정:

```python
# 특정 버전 사용
prompt = langfuse.get_prompt("question_generation_craft_question", version=2)

# 라벨로 선택
prompt = langfuse.get_prompt("question_generation_craft_question", label="staging")
```

---

## 3. 트레이싱 설정

### 3.1 트레이스 샘플링 설정

대용량 트래픽 시 샘플링 설정:

1. **Settings** → **Tracing**
2. **Sampling Rate**: 0.1 ~ 1.0 (10% ~ 100%)
3. 권장:
   - 개발: 1.0 (100%)
   - 스테이징: 0.5 (50%)
   - 프로덕션: 0.1 ~ 0.3 (10-30%)

### 3.2 트레이스 보존 기간

1. **Settings** → **Data Retention**
2. 설정:
   - Traces: 30일 (기본)
   - Generations: 90일
   - Scores: 영구

---

## 4. 평가(Evaluation) 설정

### 4.1 평가 기준 생성

질문 품질 평가를 위한 스코어 설정:

1. **Scores** → **Score Configs** → **New**
2. 다음 스코어 생성:

| Score Name | Data Type | Min | Max | Description |
|------------|-----------|-----|-----|-------------|
| `evidence_grounding` | Numeric | 0 | 100 | 증거 기반 점수 (F1 개념) |
| `hallucination_risk` | Categorical | - | - | low, medium, high |
| `question_quality` | Numeric | 0 | 10 | 전반적 질문 품질 |
| `relevance` | Numeric | 0 | 10 | 관련성 점수 |
| `clarity` | Numeric | 0 | 10 | 명확성 점수 |

### 4.2 자동 평가 설정 (LLM-as-Judge)

1. **Evaluators** → **New Evaluator**
2. **Type**: LLM-based
3. **Name**: `evidence_grounding_evaluator`
4. **Prompt**:

```
You are evaluating if an interview question is grounded in documented evidence.

Question: {{question_text}}
Evidence: {{evidence_summary}}

Rate the evidence grounding from 0-100:
- 100: Question directly references documented evidence
- 70-99: Question is about stated skills but generalizes
- 40-69: Question is tangentially related
- 0-39: Question appears hallucinated

Output only the numeric score.
```

5. **Output Mapping**: `evidence_grounding` 스코어에 연결

---

## 5. 대시보드 설정

### 5.1 커스텀 대시보드 생성

1. **Dashboards** → **New Dashboard**
2. **Name**: `Vantict Interview Quality`
3. 다음 위젯 추가:

#### 위젯 1: Evidence Grounding Score 분포
- Type: Histogram
- Score: `evidence_grounding`
- Group by: Date

#### 위젯 2: Hallucination Risk 분포
- Type: Pie Chart
- Score: `hallucination_risk`

#### 위젯 3: 일별 질문 생성량
- Type: Time Series
- Metric: Generation Count
- Filter: `name = "question_generation_craft_question"`

#### 위젯 4: 평균 질문 품질
- Type: Metric
- Score: `question_quality`
- Aggregation: Average

### 5.2 알림 설정

1. **Settings** → **Alerts**
2. **New Alert** 클릭
3. 다음 알림 생성:

| Alert Name | Condition | Threshold | Action |
|------------|-----------|-----------|--------|
| Low Evidence Grounding | `evidence_grounding` avg < | 70 | Email/Slack |
| High Hallucination Rate | `hallucination_risk` = "high" | >20% | Email/Slack |
| Error Rate Spike | Error count | >10/hour | Email/Slack |

---

## 6. 통합 설정

### 6.1 Slack 연동

1. **Settings** → **Integrations** → **Slack**
2. **Add to Slack** 클릭
3. 채널 선택: `#vantict-alerts`
4. 알림 유형 선택:
   - [ ] All traces
   - [x] Errors
   - [x] Score threshold alerts

### 6.2 Webhook 설정

외부 시스템 연동:

1. **Settings** → **Webhooks** → **New**
2. **URL**: `https://your-backend.com/api/langfuse-webhook`
3. **Events**:
   - [x] `trace.created`
   - [x] `score.created`
   - [x] `generation.created`
4. **Headers**:
   ```
   Authorization: Bearer your-webhook-secret
   ```

---

## 7. 팀 관리

### 7.1 팀원 초대

1. **Settings** → **Team**
2. **Invite Member**
3. 역할:
   - **Admin**: 전체 설정 접근
   - **Member**: 데이터 조회, 프롬프트 수정
   - **Viewer**: 읽기 전용

### 7.2 역할별 권한

| 기능 | Admin | Member | Viewer |
|------|-------|--------|--------|
| 트레이스 조회 | ✅ | ✅ | ✅ |
| 프롬프트 수정 | ✅ | ✅ | ❌ |
| 평가 생성 | ✅ | ✅ | ❌ |
| 설정 변경 | ✅ | ❌ | ❌ |
| API 키 관리 | ✅ | ❌ | ❌ |

---

## 8. 환경 설정 체크리스트

### 개발 환경 (Development)
- [ ] Langfuse 로컬 인스턴스 실행 확인
- [ ] API 키 `.env.development` 설정
- [ ] 샘플링 100% 설정
- [ ] 모든 프롬프트 `development` 라벨

### 스테이징 환경 (Staging)
- [ ] Langfuse Cloud 또는 별도 인스턴스
- [ ] 샘플링 50% 설정
- [ ] A/B 테스트 프롬프트 `staging` 라벨
- [ ] 알림 설정 (Slack #vantict-staging)

### 프로덕션 환경 (Production)
- [ ] Langfuse Cloud 프로덕션 프로젝트
- [ ] 샘플링 10-30% 설정
- [ ] `production` 라벨 프롬프트만 활성화
- [ ] 모든 알림 활성화
- [ ] 대시보드 모니터링 설정

---

## 9. 트러블슈팅

### 9.1 API 키 오류

```
Error: Langfuse authentication failed
```

**해결**:
1. `.env` 파일 확인
2. 키 복사 시 공백 제거
3. `LANGFUSE_HOST` URL 확인 (끝에 `/` 없어야 함)

### 9.2 프롬프트 로드 실패

```
Error: Prompt not found: question_generation_craft_question
```

**해결**:
1. Langfuse UI에서 프롬프트 이름 확인
2. `production` 라벨 확인
3. 코드에서 YAML 폴백 활성화 확인

### 9.3 트레이스 누락

**해결**:
1. 샘플링 레이트 확인 (100%로 테스트)
2. `langfuse.flush()` 호출 확인
3. 네트워크 연결 확인

---

## 10. 다음 단계

1. **프롬프트 등록**: 위 섹션 2 완료
2. **평가 기준 설정**: 위 섹션 4 완료
3. **대시보드 구성**: 위 섹션 5 완료
4. **알림 설정**: 위 섹션 5.2 완료
5. **테스트 실행**: `docker exec iaas-backend-1 python -m pytest tests/test_prompts.py -v`

질문이 있으면 [Langfuse 문서](https://langfuse.com/docs)를 참조하세요.
