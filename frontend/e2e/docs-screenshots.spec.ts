import path from 'node:path';
import type { Page } from '@playwright/test';
import { test, expect } from '@playwright/test';
import { createGame } from './support/game-flow';

/**
 * Not a correctness gate -- this spec drives the real UI through each screen
 * and saves screenshots for the end-user guide (docs/user-guide.md). Kept as
 * a real Playwright spec (not a throwaway script) so the captured states stay
 * honest: if a selector or flow breaks, this fails loudly like any other e2e
 * spec instead of silently capturing a stale/broken screen.
 */
const SHOTS_DIR = path.join(__dirname, '..', '..', 'docs', 'images', 'user-guide');

/**
 * `toBeVisible()`/DOM presence don't guarantee the browser has actually
 * composited a frame yet -- newly-inserted `position: fixed` elements (the
 * winner overlay) in particular can be captured mid-paint, silently showing
 * the page underneath. A short settle delay avoids that flake.
 */
async function screenshot(page: Page, filename: string): Promise<void> {
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(SHOTS_DIR, filename) });
}

test.describe('Documentation screenshots', () => {
  test('capture the full desktop walkthrough', async ({ page, context }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop', 'one consistent viewport for the main walkthrough');

    await page.goto('/');
    await screenshot(page, '01-home.png');

    await page.getByTestId('game-name-input').fill('PyCon Ireland 2026');
    await screenshot(page, '02-home-filled.png');

    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await page.getByTestId('create-game-submit').click();
    await expect(page.getByTestId('share-link')).toBeVisible();
    await screenshot(page, '03-share-screen.png');

    const joinUrl = await page.getByTestId('share-link').getAttribute('href');
    await page.goto(joinUrl!);
    await screenshot(page, '04-join.png');

    await page.getByTestId('player-name-input').fill('Christian');
    await page.getByTestId('join-game-submit').click();
    await expect(page.getByTestId('cell-0')).toBeVisible();
    await screenshot(page, '05-board-fresh.png');

    // Mark a couple of cells that are NOT part of the row we complete below.
    await page.getByTestId('cell-6').click();
    await expect(page.getByTestId('cell-6')).toHaveClass(/marked/);
    await page.getByTestId('cell-7').click();
    await expect(page.getByTestId('cell-7')).toHaveClass(/marked/);
    await screenshot(page, '06-board-marked.png');

    // Complete row 0 (positions 0-4) for the win.
    for (const position of [0, 1, 2, 3]) {
      await page.getByTestId(`cell-${position}`).click();
      await expect(page.getByTestId(`cell-${position}`)).toHaveClass(/marked/);
    }
    await page.getByTestId('cell-4').click();
    await expect(page.getByTestId('winner-overlay')).toBeVisible();
    await screenshot(page, '07-winner-overlay.png');

    await page.getByTestId('celebrate-dismiss').click();
    await expect(page.getByTestId('winner-overlay')).toBeHidden();
    await screenshot(page, '08-board-won-readonly.png');

    await page.getByTestId('theme-toggle').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await screenshot(page, '09-dark-mode.png');
  });

  test('capture dead-end states', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop', 'one consistent viewport for the main walkthrough');

    await page.goto('/board/00000000-0000-0000-0000-000000000000/');
    await expect(page.getByTestId('not-found-notice')).toBeVisible();
    await screenshot(page, '10-not-found.png');

    const { joinUrl } = await createGame(page, 'Already Finished Game');
    await page.goto(joinUrl);
    await page.getByTestId('player-name-input').fill('Speedy');
    await page.getByTestId('join-game-submit').click();
    for (const position of [0, 1, 2, 3, 4]) {
      await page.getByTestId(`cell-${position}`).click();
    }
    await expect(page.getByTestId('winner-overlay')).toBeVisible();

    await page.goto(joinUrl);
    await expect(page.getByTestId('game-finished-notice')).toBeVisible();
    await screenshot(page, '11-join-finished.png');
  });

  test('capture mobile home and board views', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'mobile-specific illustrations only');

    await page.goto('/');
    await screenshot(page, '12-mobile-home.png');

    const { joinUrl } = await createGame(page, 'Mobile Demo Game');
    await page.goto(joinUrl);
    await page.getByTestId('player-name-input').fill('Mobile Player');
    await page.getByTestId('join-game-submit').click();
    await expect(page.getByTestId('cell-0')).toBeVisible();
    await screenshot(page, '13-mobile-board.png');
  });
});
