import { test, expect } from '@playwright/test';
import {
  setupMockApi,
  setupMockApiError,
  ANALYSIS_PATH,
  SAMPLE_RESULT,
} from './fixtures/mock-api';

// =============================================================================
// Result Page — E2E Test Suite
// =============================================================================

test.describe('ResultPage', () => {
  // ---------------------------------------------------------------------------
  // a) Overview Tab Rendering
  // ---------------------------------------------------------------------------

  test.describe('Overview tab', () => {
    test.beforeEach(async ({ page }) => {
      await setupMockApi(page);
      await page.goto(ANALYSIS_PATH);
    });

    test('displays the overall grade', async ({ page }) => {
      // Grade "B+" should be prominently visible
      const gradeText = page.locator('text=B+').first();
      await expect(gradeText).toBeVisible();
    });

    test('displays weighted score and confidence', async ({ page }) => {
      await expect(page.getByText('72.5')).toBeVisible();
      await expect(page.getByText('높음')).toBeVisible();
    });

    test('displays four-axis signal indicators', async ({ page }) => {
      // Axis labels
      await expect(page.getByText('논리력')).toBeVisible();
      await expect(page.getByText('전문성')).toBeVisible();
      await expect(page.getByText('안정성')).toBeVisible();
      await expect(page.getByText('진정성')).toBeVisible();

      // Signal badges — "양호" (green) appears for logic & stability
      const greenBadges = page.getByText('양호');
      await expect(greenBadges.first()).toBeVisible();

      // "주의" (yellow) appears for mastery & authenticity
      const yellowBadges = page.getByText('주의');
      await expect(yellowBadges.first()).toBeVisible();
    });

    test('displays axis scores', async ({ page }) => {
      await expect(page.getByText('78')).toBeVisible(); // logic
      await expect(page.getByText('65')).toBeVisible(); // mastery
      await expect(page.getByText('80')).toBeVisible(); // stability
      await expect(page.getByText('70')).toBeVisible(); // authenticity
    });

    test('renders FourAxisRadar SVG chart', async ({ page }) => {
      // The radar chart renders inside an SVG element
      const radarSection = page.getByText('4축 레이더').locator('..');
      await expect(radarSection).toBeVisible();

      // SVG should be present within the radar section area
      const svgElements = page.locator('svg');
      const svgCount = await svgElements.count();
      expect(svgCount).toBeGreaterThan(0);
    });

    test('displays decision support recommendation', async ({ page }) => {
      await expect(page.getByText('조건부 채용')).toBeVisible();
      await expect(page.getByText('채용 판단')).toBeVisible();
      await expect(
        page.getByText('전반적으로 견고한 코딩 능력을 보여주나'),
      ).toBeVisible();
    });

    test('displays strengths and concerns', async ({ page }) => {
      await expect(page.getByText('강점')).toBeVisible();
      await expect(
        page.getByText('일관된 코드 스타일과 네이밍 컨벤션 유지'),
      ).toBeVisible();

      await expect(page.getByText('우려 사항')).toBeVisible();
      await expect(
        page.getByText('일부 유틸리티 파일의 높은 AI 코드 의심률'),
      ).toBeVisible();
    });

    test('displays risk factors', async ({ page }) => {
      await expect(page.getByText('리스크 요인')).toBeVisible();
      await expect(
        page.getByText('AI 코드 의존도가 핵심 비즈니스 로직까지 확장될 가능성'),
      ).toBeVisible();
    });

    test('displays AI code suspicion percentage', async ({ page }) => {
      await expect(page.getByText('AI 코드 의심률')).toBeVisible();
      await expect(page.getByText('12.3%')).toBeVisible();
    });
  });

  // ---------------------------------------------------------------------------
  // b) Code Deep Dive Tab
  // ---------------------------------------------------------------------------

  test.describe('Code Deep Dive tab', () => {
    test.beforeEach(async ({ page }) => {
      await setupMockApi(page);
      await page.goto(ANALYSIS_PATH);
      // Click the Code Deep Dive tab
      await page.getByRole('button', { name: '코드 심층 분석' }).click();
    });

    test('renders statistics cards', async ({ page }) => {
      // Files analyzed
      await expect(page.getByText('분석 파일 수')).toBeVisible();
      await expect(page.getByText('42')).toBeVisible();

      // Average cyclomatic complexity
      await expect(page.getByText('평균 순환 복잡도')).toBeVisible();
      await expect(page.getByText('4.2')).toBeVisible();

      // Average maintainability index
      await expect(page.getByText('평균 유지보수성')).toBeVisible();
      await expect(page.getByText('72.8')).toBeVisible();

      // Detected tech stack count
      await expect(page.getByText('감지된 기술 스택')).toBeVisible();
      await expect(page.getByText('12')).toBeVisible();
    });

    test('renders AuthenticityGauge SVG', async ({ page }) => {
      await expect(page.getByText('진정성 게이지')).toBeVisible();

      // The gauge renders an SVG
      const svgElements = page.locator('svg');
      const svgCount = await svgElements.count();
      expect(svgCount).toBeGreaterThan(0);
    });

    test('renders ComplexityTreemap SVG', async ({ page }) => {
      await expect(page.getByText('복잡도 트리맵')).toBeVisible();
      await expect(
        page.getByText('파일별 복잡도(크기)와 유지보수성(색상)을 시각화합니다'),
      ).toBeVisible();
    });

    test('renders AICodeHeatmap SVG', async ({ page }) => {
      await expect(page.getByText('AI 코드 히트맵')).toBeVisible();
      await expect(
        page.getByText('파일별 AI 코드 의심률을 시각화합니다'),
      ).toBeVisible();
    });

    test('displays logic and stack summaries', async ({ page }) => {
      await expect(page.getByText('논리 분석 요약')).toBeVisible();
      await expect(
        page.getByText('전반적으로 적절한 복잡도를 유지하며'),
      ).toBeVisible();

      await expect(page.getByText('기술 스택 요약')).toBeVisible();
      await expect(
        page.getByText('React + TypeScript 기반으로 현대적인 프론트엔드 아키텍처'),
      ).toBeVisible();
    });
  });

  // ---------------------------------------------------------------------------
  // c) Interview Tab
  // ---------------------------------------------------------------------------

  test.describe('Interview tab', () => {
    test.beforeEach(async ({ page }) => {
      await setupMockApi(page);
      await page.goto(ANALYSIS_PATH);
      // Click the Interview tab
      await page.getByRole('button', { name: '면접 스크립트' }).click();
    });

    test('displays interview script header with question count', async ({ page }) => {
      await expect(page.getByText('면접 스크립트')).toBeVisible();
      await expect(page.getByText('총 6개 질문')).toBeVisible();
      await expect(page.getByText('3개 전략')).toBeVisible();
    });

    test('renders question cards', async ({ page }) => {
      // First question from negative_selection strategy
      await expect(
        page.getByText('utils/helpers.ts에서 AI 코드 의심률이 82%로 높게 나왔는데'),
      ).toBeVisible();

      // Question from intentional_complexity strategy
      await expect(
        page.getByText('payment 서비스의 복잡도가 높은데'),
      ).toBeVisible();
    });

    test('displays strategy group headers', async ({ page }) => {
      await expect(page.getByText('네거티브 선별')).toBeVisible();
      await expect(page.getByText('의도적 복잡성')).toBeVisible();
      await expect(page.getByText('코드 진화')).toBeVisible();
    });

    test('filters questions by strategy', async ({ page }) => {
      // Click on "네거티브 선별" filter button
      // The filter buttons show count in parentheses
      await page.getByRole('button', { name: /네거티브 선별/ }).click();

      // Should show negative_selection questions
      await expect(
        page.getByText('utils/helpers.ts에서 AI 코드 의심률이 82%로 높게 나왔는데'),
      ).toBeVisible();

      // Should NOT show intentional_complexity questions
      await expect(
        page.getByText('Dashboard 컴포넌트에서 상태 관리를 어떻게 설계하셨나요?'),
      ).not.toBeVisible();

      // Click "전체" to reset filter
      await page.getByRole('button', { name: '전체' }).click();

      // Now all questions should be visible again
      await expect(
        page.getByText('Dashboard 컴포넌트에서 상태 관리를 어떻게 설계하셨나요?'),
      ).toBeVisible();
    });

    test('expands and collapses question card details', async ({ page }) => {
      // Find the first "상세" button and click it to expand
      const expandButton = page.getByRole('button', { name: '상세' }).first();
      await expandButton.click();

      // Expanded content should show checklist items
      await expect(
        page.getByText('구현 동기를 구체적으로 설명하는지 확인'),
      ).toBeVisible();

      // Should show follow-up questions
      await expect(
        page.getByText('이 파일을 리팩토링한다면 어떻게 개선하시겠습니까?'),
      ).toBeVisible();

      // Should show code reference
      await expect(page.getByText('코드 참조')).toBeVisible();
      await expect(page.getByText('utils/helpers.ts:15-42')).toBeVisible();

      // Click "접기" to collapse
      const collapseButton = page.getByRole('button', { name: '접기' }).first();
      await collapseButton.click();

      // Expanded content should be hidden
      await expect(
        page.getByText('구현 동기를 구체적으로 설명하는지 확인'),
      ).not.toBeVisible();
    });

    test('displays difficulty badges', async ({ page }) => {
      await expect(page.getByText('심화').first()).toBeVisible();
      await expect(page.getByText('보통').first()).toBeVisible();
      await expect(page.getByText('기본').first()).toBeVisible();
    });

    test('displays question intent', async ({ page }) => {
      await expect(
        page.getByText('AI 코드 사용 여부를 직접적으로 확인합니다.'),
      ).toBeVisible();
    });
  });

  // ---------------------------------------------------------------------------
  // d) Error States
  // ---------------------------------------------------------------------------

  test.describe('Error states', () => {
    test('shows error message on API 404', async ({ page }) => {
      await setupMockApiError(page, 404, '분석 결과를 찾을 수 없습니다.');
      await page.goto(ANALYSIS_PATH);

      await expect(page.getByText('오류 발생')).toBeVisible();
      await expect(page.getByText('분석 결과를 찾을 수 없습니다.')).toBeVisible();
    });

    test('shows error message on API 500 with retry button', async ({ page }) => {
      await setupMockApiError(page, 500, 'Internal Server Error');
      await page.goto(ANALYSIS_PATH);

      await expect(page.getByText('오류 발생')).toBeVisible();

      // Retry button should be visible
      const retryButton = page.getByRole('button', { name: '다시 시도' });
      await expect(retryButton).toBeVisible();
    });

    test('retry button triggers a new API request', async ({ page }) => {
      // First load: return error
      let callCount = 0;
      await page.route('**/api/jobs/*/result', async (route) => {
        callCount++;
        if (callCount === 1) {
          // First request: return 500
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Server Error' }),
          });
        } else {
          // Subsequent requests: return success
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(SAMPLE_RESULT),
          });
        }
      });

      await page.goto(ANALYSIS_PATH);

      // Error state should be shown
      await expect(page.getByText('오류 발생')).toBeVisible();

      // Click retry
      await page.getByRole('button', { name: '다시 시도' }).click();

      // After retry, the result page should render successfully
      await expect(page.getByText('B+')).toBeVisible();
    });
  });

  // ---------------------------------------------------------------------------
  // e) Loading State
  // ---------------------------------------------------------------------------

  test.describe('Loading state', () => {
    test('shows loading spinner while API is pending', async ({ page }) => {
      // Set up a delayed response to observe the loading state
      await setupMockApi(page, { delay: 3000 });

      await page.goto(ANALYSIS_PATH);

      // Loading indicator text
      await expect(page.getByText('분석 결과를 불러오는 중...')).toBeVisible();

      // The spinner element (animate-spin class on a div)
      const spinner = page.locator('.animate-spin');
      await expect(spinner).toBeVisible();
    });

    test('loading state transitions to content after API responds', async ({ page }) => {
      await setupMockApi(page, { delay: 500 });

      await page.goto(ANALYSIS_PATH);

      // Initially shows loading
      await expect(page.getByText('분석 결과를 불러오는 중...')).toBeVisible();

      // Wait for the content to appear
      await expect(page.getByText('B+')).toBeVisible({ timeout: 10_000 });

      // Loading indicator should be gone
      await expect(page.getByText('분석 결과를 불러오는 중...')).not.toBeVisible();
    });
  });

  // ---------------------------------------------------------------------------
  // Tab Navigation
  // ---------------------------------------------------------------------------

  test.describe('Tab navigation', () => {
    test.beforeEach(async ({ page }) => {
      await setupMockApi(page);
      await page.goto(ANALYSIS_PATH);
    });

    test('defaults to Overview tab', async ({ page }) => {
      // Overview tab content should be visible by default
      await expect(page.getByText('종합 등급')).toBeVisible();
      await expect(page.getByText('B+')).toBeVisible();
    });

    test('switches between tabs correctly', async ({ page }) => {
      // Navigate to Code Deep Dive
      await page.getByRole('button', { name: '코드 심층 분석' }).click();
      await expect(page.getByText('분석 파일 수')).toBeVisible();
      await expect(page.getByText('종합 등급')).not.toBeVisible();

      // Navigate to Interview
      await page.getByRole('button', { name: '면접 스크립트' }).click();
      await expect(page.getByText('총 6개 질문')).toBeVisible();
      await expect(page.getByText('분석 파일 수')).not.toBeVisible();

      // Navigate back to Overview
      await page.getByRole('button', { name: '개요' }).click();
      await expect(page.getByText('종합 등급')).toBeVisible();
    });
  });

  // ---------------------------------------------------------------------------
  // Header
  // ---------------------------------------------------------------------------

  test.describe('Header', () => {
    test('displays job and version info', async ({ page }) => {
      await setupMockApi(page);
      await page.goto(ANALYSIS_PATH);

      await expect(page.getByText('분석 결과')).toBeVisible();
      await expect(page.getByText(/test-job-001/)).toBeVisible();
      await expect(page.getByText(/5\.0\.0/)).toBeVisible();
    });

    test('displays completion status badge', async ({ page }) => {
      await setupMockApi(page);
      await page.goto(ANALYSIS_PATH);

      await expect(page.getByText('완료')).toBeVisible();
    });
  });
});
