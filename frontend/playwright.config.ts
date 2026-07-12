import { defineConfig, devices } from '@playwright/test';

// A distinctive default port, deliberately not 8000 -- local dev setups
// (e.g. `tilt up`) commonly forward the "real" dev server to 8000, and this
// suite must never accidentally exercise that shared database.
const PORT = process.env.PORT ?? '8173';
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  globalSetup: './e2e/support/global-setup.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'mobile',
      testDir: 'e2e',
      use: { ...devices['Pixel 7'] },
    },
    {
      name: 'desktop',
      testDir: 'e2e',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1024, height: 800 } },
    },
    {
      name: 'unit',
      testDir: 'tests/unit',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    // --insecure: `config.settings.test` sets DEBUG=False, and Django's
    // staticfiles app only auto-serves static files under `runserver`
    // without this flag when DEBUG=True -- the e2e suite needs the compiled
    // copy-link.js and bingo.css served for real.
    command: `uv run backend/manage.py runserver --insecure ${PORT}`,
    cwd: '..',
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: {
      DJANGO_SETTINGS_MODULE: 'config.settings.test',
      DJANGO_ALLOWED_HOSTS: 'localhost,127.0.0.1',
      DJANGO_SECRET_KEY: process.env.DJANGO_SECRET_KEY ?? 'e2e-test-secret-key',
    },
  },
});
