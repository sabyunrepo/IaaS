import type { Page, Route } from '@playwright/test';
import sampleResult from './sample-result.json';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MockApiOptions {
  /** Override the default sample result with a custom payload. */
  resultOverride?: Record<string, unknown>;
  /** HTTP status code to return for the result endpoint. Default: 200. */
  statusCode?: number;
  /** Artificial delay in milliseconds before responding. Default: 0. */
  delay?: number;
}

// ---------------------------------------------------------------------------
// Default mock data
// ---------------------------------------------------------------------------

/** The sample AnalysisResult used for all mocked API calls by default. */
export const SAMPLE_RESULT = sampleResult;

/** Job / candidate IDs used in test routes. */
export const TEST_JOB_ID = 'test-job-001';
export const TEST_CANDIDATE_ID = 'test-candidate-001';

/** The analysis page path used in tests. */
export const ANALYSIS_PATH = `/jobs/${TEST_JOB_ID}/candidates/${TEST_CANDIDATE_ID}/analysis`;

// ---------------------------------------------------------------------------
// Mock API setup
// ---------------------------------------------------------------------------

/**
 * Intercept all `/api/jobs/*/result` requests via `page.route()`.
 *
 * Usage:
 * ```ts
 * test.beforeEach(async ({ page }) => {
 *   await setupMockApi(page);
 * });
 * ```
 */
export async function setupMockApi(
  page: Page,
  options: MockApiOptions = {},
): Promise<void> {
  const {
    resultOverride,
    statusCode = 200,
    delay = 0,
  } = options;

  const body = resultOverride ?? SAMPLE_RESULT;

  await page.route('**/api/jobs/*/result', async (route: Route) => {
    if (delay > 0) {
      await new Promise((resolve) => setTimeout(resolve, delay));
    }

    await route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

/**
 * Mock the API to return a specific HTTP error status.
 *
 * Useful for testing error states (404, 500, etc.).
 */
export async function setupMockApiError(
  page: Page,
  statusCode: number,
  message?: string,
): Promise<void> {
  await page.route('**/api/jobs/*/result', async (route: Route) => {
    await route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: message ?? `Error ${statusCode}`,
      }),
    });
  });
}
