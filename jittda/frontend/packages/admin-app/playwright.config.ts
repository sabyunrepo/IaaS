import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration for admin-app.
 *
 * - Tests live in ./e2e/
 * - Dev server runs on port 3001 (matching vite.config.ts)
 * - API calls are mocked via page.route() in fixtures — no real backend needed
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'list',

  use: {
    baseURL: 'http://localhost:3001',
    headless: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'pnpm dev',
    port: 3001,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
