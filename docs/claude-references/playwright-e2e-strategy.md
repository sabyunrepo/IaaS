# Playwright E2E 테스트 전략 (상세)

> CLAUDE.md에서 분리된 상세 문서. 핵심 요약은 CLAUDE.md 본문 참조.

## 테스트 피라미드

```
         /  E2E (Playwright)  \          ← 3-5 Critical User Flows
        /  Integration (Vitest+RTL) \    ← 컴포넌트 조합 테스트 (추가 예정)
       /  Unit (Vitest)              \   ← 순수 로직 함수 (추가 예정)
      /  Static (TypeScript + ESLint)  \ ← 컴파일 타임 검증
```

## E2E 테스트 시퀀스 (5개)

### Sequence 1: 인증 플로우
```
1. LoginPage 렌더링 확인
2. OAuth 버튼 존재 확인 (Google)
3. 토큰 직접 주입 (localStorage) → 인증 우회
4. /jobs 리다이렉트 확인
5. 비인증 상태 → /login 리다이렉트 확인
```

### Sequence 2: Job 생성 플로우
```
1. CreateJobPage 렌더링 확인
2. 필수 필드 입력: JD, experience_level, output_language
3. 선택 필드: LinkedIn URL, GitHub URL, portfolio PDF
4. 질문 수 슬라이더 (5-25) 조작
5. 제출 → API 호출 확인 → JobStatusPage 리다이렉트
6. 폼 유효성 검사 (빈 필드 제출 시 에러)
```

### Sequence 3: Result 페이지 4탭 순회 (핵심)
```
1. ResultPage 로딩 → API mock 주입 (/api/v1/results/{id})
2. Intel Brief 탭:
   - 후보자 이름, 직함, 요약 렌더링 확인
   - Competency 매칭 카드 존재 확인
3. Deep Analysis 탭:
   - RadarChart SVG 렌더링 확인
   - 스킬 매칭 테이블 행 수 확인
   - Engineering DNA 섹션 존재 확인
4. Live Interview 탭:
   - 질문 카드 렌더링 (최소 5개)
   - 카테고리별 배분 확인
   - 질문 클릭 → 상세 패널 열림
   - follow-up 질문 존재 확인
5. Decision 탭:
   - 종합 점수 렌더링
   - 추천/비추천 배지 확인
   - 위험 평가 항목 존재
6. 전 탭 콘솔 에러 0개 확인
7. 스크린샷 캡처 → 이전 버전과 비교
```

### Sequence 4: 에러 핸들링 & 엣지 케이스
```
1. 404 페이지 렌더링 확인
2. API 500 에러 시 ErrorBoundary 동작 확인
3. 네트워크 오프라인 시 graceful degradation
4. 빈 결과 데이터 시 빈 상태 UI 확인
5. 긴 텍스트 오버플로우 처리 확인
6. 모바일 뷰포트 (375px) 레이아웃 깨짐 확인
```

### Sequence 5: 접근성 & 성능
```
1. 키보드 네비게이션 (Tab, Enter, Escape)
2. ARIA 라벨 존재 확인
3. 색상 대비 비율 (WCAG 2.1 AA)
4. LCP < 2.5s, CLS < 0.1 측정
5. 번들 사이즈 확인 (초기 로딩 < 300KB)
```

## E2E 테스트 실행 명령

```bash
# 전체 E2E 테스트
cd frontend && npx playwright test

# 특정 시퀀스만
npx playwright test result-page.spec.ts
npx playwright test create-job.spec.ts

# 시각적 확인 (headed 모드)
npx playwright test --headed

# 디버그 모드
npx playwright test --debug

# HTML 리포트
npx playwright show-report
```

## Flyweight 패턴 적용 (테스트 데이터)

E2E 테스트에서 mock 데이터를 Flyweight 패턴으로 관리:

```typescript
// e2e/fixtures/mock-data.ts — 공유 테스트 데이터 풀
export const SHARED_CANDIDATE = {
  name: "Alex Kim",
  title: "Senior AI Engineer",
  experience_years: 8,
  // ... 모든 테스트에서 공유
};

export const SHARED_QUESTIONS = [
  { id: 1, category: "technical_depth", text: "..." },
  // ... 20개 질문 풀
];

// 테스트별로 필요한 부분만 확장 (intrinsic + extrinsic 분리)
export function createMockResult(overrides?: Partial<ResultData>): ResultData {
  return { ...SHARED_CANDIDATE, ...SHARED_QUESTIONS, ...overrides };
}
```

## Playwright 기반 프론트엔드 에러 탐지

**자동화된 에러 탐지 파이프라인:**
```
1. Playwright 테스트 실행 → 2. 콘솔 에러 수집 → 3. 에러 분류 → 4. 이슈 생성 → 5. 수정 + 재테스트
```

| 에러 유형 | 탐지 방법 | 대응 패턴 |
|----------|----------|----------|
| Hook 순서 위반 | 콘솔 에러 + Playwright | 조건부 렌더링 전에 모든 Hook 호출 |
| undefined 프로퍼티 접근 | Playwright + TypeScript | optional chaining `?.` + nullish coalescing `??` |
| API 데이터 타입 불일치 | Playwright + type guard | 런타임 검증 또는 type guard 함수 |
| i18n 누락 | Playwright 텍스트 검증 | `t()` 함수 + 번역 키 자동 추출 |
