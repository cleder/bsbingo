import { execFileSync } from 'node:child_process';

/**
 * Migrate and seed the database the `webServer`-spawned Django process
 * talks to, so every e2e spec can join a fresh game without ever needing
 * to pre-configure buzzwords by hand (no direct DB fixtures -- research.md).
 */
export default function globalSetup(): void {
  const env = {
    ...process.env,
    DJANGO_SETTINGS_MODULE: 'config.settings.test',
    DJANGO_SECRET_KEY: process.env.DJANGO_SECRET_KEY ?? 'e2e-test-secret-key',
  };
  const runManagementCommand = (...args: string[]): void => {
    execFileSync('uv', ['run', 'backend/manage.py', ...args], {
      cwd: '..',
      env,
      stdio: 'inherit',
    });
  };

  runManagementCommand('migrate', '--noinput');
  runManagementCommand('seed_buzzwords');
}
