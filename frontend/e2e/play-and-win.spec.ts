import { test, expect } from '@playwright/test';
import { createGame, joinGame } from './support/game-flow';

test.describe('Play the board and feel the win (US3)', () => {
  test('tapping an unmarked cell transitions it to marked', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Play Test Tap');
    await joinGame(page, joinUrl, 'Tapper');

    const cell = page.getByTestId('cell-0');
    await expect(cell).not.toHaveClass(/marked/);
    await cell.click();
    await expect(cell).toHaveClass(/marked/);
  });

  test('tapping a marked cell unmarks it', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Play Test Unmark');
    await joinGame(page, joinUrl, 'Unmarker');

    const cell = page.getByTestId('cell-0');
    await cell.click();
    await expect(cell).toHaveClass(/marked/);
    await cell.click();
    await expect(cell).not.toHaveClass(/marked/);
  });

  test('the free-space cell is always marked and never responds to taps', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Play Test Free Space');
    await joinGame(page, joinUrl, 'FreeSpacer');

    const freeSpace = page.getByTestId('free-space');
    await expect(freeSpace).toHaveClass(/marked/);
    await expect(freeSpace).toBeDisabled();
  });

  test('a rapid double-tap on the same cell only fires one toggle', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Play Test Double Tap');
    await joinGame(page, joinUrl, 'DoubleTapper');

    let toggleRequests = 0;
    page.on('request', (request) => {
      if (request.method() === 'POST' && request.url().includes('/toggle/')) {
        toggleRequests += 1;
      }
    });

    await page.evaluate(() => {
      const cell = document.querySelector('[data-testid="cell-0"]') as HTMLButtonElement;
      cell.click();
      cell.click();
    });
    await page.waitForResponse((response) => response.url().includes('/toggle/'));
    await page.waitForTimeout(200);

    expect(toggleRequests).toBe(1);
  });

  test('applies the pending state synchronously, independent of server latency (SC-002)', async ({
    page,
  }) => {
    const { joinUrl } = await createGame(page, 'Play Test Timing');
    await joinGame(page, joinUrl, 'Speedy');

    await page.route('**/cell/*/toggle/', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.continue();
    });

    const cell = page.getByTestId('cell-0');
    await cell.click();
    // Must already be disabled well before the artificially delayed (500ms)
    // server response arrives -- proving the pending state is applied
    // synchronously on tap, not after the round trip (FR-010/SC-002).
    await expect(cell).toBeDisabled({ timeout: 100 });
  });

  test('can mark a cell using only the keyboard (FR-011)', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Play Test Keyboard');
    await joinGame(page, joinUrl, 'KeyboardPlayer');

    const cell = page.getByTestId('cell-0');
    await cell.focus();
    await page.keyboard.press('Enter');

    await expect(cell).toHaveClass(/marked/);
  });

  test('completing a line shows the celebratory overlay and highlighted line, and dismissing reveals a read-only board underneath', async ({
    page,
  }) => {
    const { joinUrl } = await createGame(page, 'Play Test Win');
    await joinGame(page, joinUrl, 'Winner');

    // Row 0 is positions 0-4 -- none of which is the center free space.
    for (const position of [0, 1, 2, 3]) {
      await page.getByTestId(`cell-${position}`).click();
      await expect(page.getByTestId(`cell-${position}`)).toHaveClass(/marked/);
    }
    await page.getByTestId('cell-4').click();

    const overlay = page.getByTestId('winner-overlay');
    await expect(overlay).toBeVisible();

    for (const position of [0, 1, 2, 3, 4]) {
      await expect(
        page.locator(`[data-testid="cell-${position}"][data-winning-line="true"]`),
      ).toBeVisible();
    }

    await page.getByTestId('celebrate-dismiss').click();
    await expect(overlay).toBeHidden();

    // The whole board -- not just the winning line -- is read-only now
    // (FR-016), and the winning line is still highlighted underneath.
    for (const position of [0, 1, 2, 3, 4]) {
      const winningCell = page.locator(`[data-testid="cell-${position}"][data-winning-line="true"]`);
      await expect(winningCell).toBeVisible();
      await expect(winningCell).toBeDisabled();
    }
    await expect(page.getByTestId('cell-5')).toBeDisabled();
  });
});
