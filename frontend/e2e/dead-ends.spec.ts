import { execFileSync } from 'node:child_process';
import { test, expect } from '@playwright/test';
import { createGame, joinGame } from './support/game-flow';

function setBuzzwordsActive(active: boolean): void {
  const flag = active ? '--active' : '--inactive';
  execFileSync('uv', ['run', 'backend/manage.py', 'set_buzzwords_active', flag], {
    cwd: '..',
    env: {
      ...process.env,
      DJANGO_SETTINGS_MODULE: 'config.settings.test',
      DJANGO_SECRET_KEY: process.env.DJANGO_SECRET_KEY ?? 'e2e-test-secret-key',
    },
  });
}

// Serial: the "no active buzzwords" scenario mutates the buzzword pool,
// which is global (admin-managed, not scoped per game) -- serializing this
// file avoids that test racing its own siblings. Run the full e2e suite
// with a single worker (see T035/CI) to avoid it also racing *other* spec
// files' joins, since there is no player-facing way to scope the pool.
test.describe.configure({ mode: 'serial' });

test.describe('Never hit a dead end (US4)', () => {
  test('a non-winning participant sees the finished notice and a read-only board', async ({
    page,
    context,
  }) => {
    const { joinUrl } = await createGame(page, 'Dead Ends Finished Board');
    await joinGame(page, joinUrl, 'Winner');

    const otherPage = await context.newPage();
    await joinGame(otherPage, joinUrl, 'Loser');
    const loserBoardUrl = otherPage.url();

    for (const position of [0, 1, 2, 3]) {
      await page.getByTestId(`cell-${position}`).click();
      await expect(page.getByTestId(`cell-${position}`)).toHaveClass(/marked/);
    }
    await page.getByTestId('cell-4').click();
    await expect(page.getByTestId('winner-overlay')).toBeVisible();

    await otherPage.goto(loserBoardUrl);

    await expect(otherPage.getByTestId('board-readonly')).toBeVisible();
    await expect(otherPage.getByText('Game Finished')).toBeVisible();
    await expect(otherPage.getByText('Winner', { exact: false })).toBeVisible();
    await expect(otherPage.getByTestId('cell-5')).toBeDisabled();
  });

  test('joining a link for an already-finished game shows a finished message instead of a form', async ({
    page,
  }) => {
    const { joinUrl } = await createGame(page, 'Dead Ends Finished Join');
    await joinGame(page, joinUrl, 'Winner');

    for (const position of [0, 1, 2, 3, 4]) {
      await page.getByTestId(`cell-${position}`).click();
    }
    await expect(page.getByTestId('winner-overlay')).toBeVisible();

    await page.goto(joinUrl);

    await expect(page.getByTestId('game-finished-notice')).toBeVisible();
    await expect(page.getByTestId('player-name-input')).toHaveCount(0);
  });

  test('attempting to join with no active buzzwords shows its own message', async ({ page }, testInfo) => {
    // desktop-only: this mutates the (global, unscoped) buzzword pool, and
    // running it under both projects at once would race one project's
    // reactivate against the other's still-needed deactivate.
    test.skip(testInfo.project.name !== 'desktop', 'runs once to avoid racing the global buzzword pool across projects');

    setBuzzwordsActive(false);
    try {
      const { joinUrl } = await createGame(page, 'Dead Ends No Buzzwords');
      await page.goto(joinUrl);
      await page.getByTestId('player-name-input').fill('Hopeful');
      await page.getByTestId('join-game-submit').click();

      await expect(page.getByTestId('no-buzzwords-notice')).toBeVisible();
    } finally {
      setBuzzwordsActive(true);
    }
  });

  test('a nonexistent board link shows a not-found message', async ({ page }) => {
    const response = await page.goto(
      '/board/00000000-0000-0000-0000-000000000000/',
    );
    expect(response?.status()).toBe(404);
    await expect(page.getByTestId('not-found-notice')).toBeVisible();
  });

  test('a nonexistent game link shows a not-found message', async ({ page }) => {
    const response = await page.goto(
      '/game/00000000-0000-0000-0000-000000000000/join/',
    );
    expect(response?.status()).toBe(404);
    await expect(page.getByTestId('not-found-notice')).toBeVisible();
  });
});
