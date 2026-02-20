# Phase 5: 출력 + 프론트엔드

> 원본 설계서: `plan/2026-02-15-v5-final-design.md`
> Linear 티켓: JIT-111 ~ JIT-119

## Linear 티켓 매핑

| 티켓 | 제목 | 참조 섹션 |
|------|------|----------|
| JIT-111 | OutputAssembler (IntelBrief + DeepAnalysis + DecisionSupport 생성) | §6.2 Phase 5 |
| JIT-112 | 4대 지표 산출 + DB 저장 (candidate_scores 테이블 연동) | §11, §15.5 |
| JIT-113 | FourAxisRadar.tsx (4대 지표 레이더 차트, D3.js) | §16.1 |
| JIT-114 | ComplexityTreemap.tsx (파일별 복잡도 드릴다운, D3.js) | §16.1 |
| JIT-115 | AICodeHeatmap.tsx (Human vs AI 생성 비율 히트맵, D3.js) | §16.1 |
| JIT-116 | AgentProgressFlow.tsx (HMAS 에이전트 실행 흐름 실시간, WebSocket) | §16.1, §16.4 |
| JIT-117 | Overview Tab (3초 요약 카드 + 신호등 UI) | §16.2 Tab 1, §16.3 |
| JIT-118 | Code Deep Dive Tab (Treemap + Heatmap + Timeline 통합) | §16.2 Tab 3 |
| JIT-119 | Interview Tab 강화 (3전략 그룹핑 + 카드형 UI + 평가 버튼) | §16.2 Tab 4 |

---

## §16. 프론트엔드 설계

### 16.1 새로운 시각화 컴포넌트

| 컴포넌트 | 기술 | 데이터 소스 | 용도 |
|----------|------|-----------|------|
| `FourAxisRadar.tsx` | D3.js | 4대 지표 | 논리력/전문성/안정성/진정성 레이더 |
| `ComplexityTreemap.tsx` | D3.js | W7 결과 | 파일별 복잡도 드릴다운 |
| `AuthenticityGauge.tsx` | D3.js | W3+W5 결과 | 진정성 게이지 (WPM + 표절률) |
| `AICodeHeatmap.tsx` | D3.js | W3 결과 | 파일별 Human vs AI 생성 비율 히트맵 |
| `SkillHeatmap.tsx` | D3.js | W9 결과 | 기술스택 히트맵 (JD 매칭) |
| `CommitTimeline.tsx` | D3.js | W1 결과 | Git 커밋 타임라인 |
| `AgentProgressFlow.tsx` | React | WebSocket | HMAS 에이전트 실행 흐름 실시간 |

### 16.2 탭 구조

```
ResultPage 탭:
+-- Tab 1: Overview (3초 요약)
|   +-- 신호등 카드 (Green/Yellow/Red) + 종합 등급 (예: B+)
|   +-- 한 줄 평: "기본기 탄탄(Green), 최신 스택 부족(Yellow), 보안 취약(Red)"
|   +-- 신뢰도 지표: "AI 생성 의심 구간 12%"
|   +-- FourAxisRadar.tsx (4대 지표)
|
+-- Tab 2: Intel Brief (기존 유지 + 강화)
|   +-- + 진정성 검증 섹션 추가
|
+-- Tab 3: Code Deep Dive (신규)
|   +-- ComplexityTreemap.tsx (파일 클릭 -> 상세 팝업)
|   +-- AICodeHeatmap.tsx (Human vs AI 비율)
|   +-- SkillHeatmap.tsx (JD 매칭)
|   +-- CommitTimeline.tsx
|
+-- Tab 4: Interview (기존 유지 + 강화)
|   +-- 3전략별 질문 그룹핑 (Negative/Complexity/Evolution)
|   +-- 카드형 UI (Q + 의도 + 체크리스트 + 평가 버튼)
|   +-- 파생 질문 (Follow-up) 자동 표시
|
+-- Tab 5: Decision (기존 유지 + 강화)
    +-- + 4대 지표 기반 종합 판단 근거
```

### 16.3 CEO용 3초 요약 카드

```
+------------------------------------------+
|  종합 등급: B+ (상위 15%)                 |
|                                          |
|  [Green 논리력 78]  [Yellow 전문성 65]    |
|  [Green 안정성 72]  [Red 진정성 45]       |
|                                          |
|  핵심 요약:                               |
|  "기본기는 탄탄하나, 최신 기술 스택 활용   |
|   경험이 부족하고, AI 생성 코드 의심 12%"  |
|                                          |
|  AI 코드 의심: 12%                        |
+------------------------------------------+
```

**설계 원칙:**
- 비개발자(CEO, HR)가 3초 내에 후보자의 수준을 파악할 수 있어야 함
- 신호등 색상으로 직관적 판단
- 종합 등급은 4대 지표의 가중 평균으로 산출
- AI 코드 의심 비율은 별도 경고로 표시

### 16.4 실시간 스트리밍 (WebSocket)

```typescript
// frontend/src/hooks/useLangGraphStream.ts
export function useLangGraphStream(jobId: string) {
  const [agentStates, setAgentStates] = useState<AgentState[]>([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/jobs/${jobId}/stream`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'agent_started':
          setAgentStates(prev => [...prev, { name: data.agent, status: 'running' }]);
          break;
        case 'agent_completed':
          setAgentStates(prev => prev.map(a =>
            a.name === data.agent ? { ...a, status: 'completed', result: data.result } : a
          ));
          break;
        case 'progress':
          setProgress(data.progress);
          break;
        case 'metric_update':
          // 실시간 지표 업데이트 (레이더 차트 점진적 렌더링)
          break;
      }
    };

    return () => ws.close();
  }, [jobId]);

  return { agentStates, progress };
}
```

**WebSocket 메시지 타입:**

| type | 설명 | payload |
|------|------|---------|
| `agent_started` | Worker/Supervisor 실행 시작 | `{ agent: string }` |
| `agent_completed` | Worker/Supervisor 실행 완료 | `{ agent: string, result: summary }` |
| `progress` | 전체 진행률 업데이트 | `{ progress: float (0-1) }` |
| `metric_update` | 개별 지표 업데이트 | `{ metric: string, value: float }` |
| `error` | 에러 발생 | `{ agent: string, message: string }` |
| `completed` | 전체 분석 완료 | `{ job_id: string }` |

### 16.5 프론트엔드 의존성

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "d3": "^7.9.0",
    "@types/d3": "^7.4.3",
    "@tanstack/react-query": "^5.0.0"
  }
}
```

---

## OutputAssembler 상세 (§6.2 Phase 5 참조)

### 출력 구성요소

```
Phase 5: OutputAssembler
+-- IntelBriefGenerator
|   - 후보자 기술 역량 요약 (비개발자 대상)
|   - 진정성 검증 결과 포함
|   - 신뢰도 표시
|
+-- DeepAnalysisGenerator
|   - 코드 복잡도 상세 분석
|   - 기술 스택 깊이 분석
|   - AI 코드 탐지 결과
|
+-- DecisionSupportGenerator
|   - 4대 지표 기반 종합 판단
|   - 채용 추천/비추천 근거
|   - 리스크 요인 요약
|
+-- FinalScriptAssembler
    - 면접 질문 세트 최종 조립
    - 3전략별 그룹핑
    - 질문 순서 최적화 (쉬운 것부터)
```

### 데이터 흐름

```
4대 지표 (candidate_scores)
         |
         v
  OutputAssembler
         |
    +----+----+----+
    |    |    |    |
    v    v    v    v
  Intel Deep  Dec  Script
  Brief Anal  Sup  Asm
    |    |    |    |
    +----+----+----+
         |
         v
   result_data (JSONB) -> jobs 테이블에 저장
         |
         v
   Frontend에서 탭별 렌더링
```
