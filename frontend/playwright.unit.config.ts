import { defineConfig, devices } from '@playwright/test';

// Deliberately separate from playwright.config.ts: unit/property tests for
// the TypeScript modules are plain Node-executed test code (no page
// navigation), so this config has no `webServer`/`globalSetup` -- `npm run
// test:unit` must not need a running Django/Postgres to pass.
export default defineConfig({
  testDir: 'tests/unit',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  projects: [
    {
      name: 'unit',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
