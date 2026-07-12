import { test, expect } from '@playwright/test';
import { createGame } from './support/game-flow';

test.describe('Join a game (US2)', () => {
  test('shows the game name and autofocuses the name field on load', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Join Test Game');
    await page.goto(joinUrl);

    await expect(page.getByText('Join Test Game')).toBeVisible();
    await expect(page.getByTestId('player-name-input')).toBeFocused();
  });

  test('submits with the Enter key, same as tapping Join Game', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Join Test Game Enter');
    await page.goto(joinUrl);

    const nameInput = page.getByTestId('player-name-input');
    await nameInput.fill('Alice');
    await nameInput.press('Enter');

    await expect(page).toHaveURL(/\/board\//);
  });

  test('shows an inline validation error without losing the game name context', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Join Test Game Blank');
    await page.goto(joinUrl);

    await page.getByTestId('player-name-input').fill('   ');
    await page.getByTestId('join-game-submit').click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByText('Join Test Game Blank')).toBeVisible();
  });

  test('can be completed using only the keyboard (FR-011)', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Join Test Game Keyboard');
    await page.goto(joinUrl);

    await expect(page.getByTestId('player-name-input')).toBeFocused();
    await page.keyboard.type('Keyboard Player');
    await page.keyboard.press('Tab');
    await expect(page.getByTestId('join-game-submit')).toBeFocused();
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\/board\//);
  });

  test('joining and marking the first square takes well under 10 seconds (SC-001)', async ({ page }) => {
    const { joinUrl } = await createGame(page, 'Join Test Game Timing');

    const start = Date.now();
    await page.goto(joinUrl);
    await page.getByTestId('player-name-input').fill('Speedy');
    await page.getByTestId('join-game-submit').click();
    await page.waitForURL(/\/board\//);
    await page.getByTestId('cell-0').click();
    await expect(page.getByTestId('cell-0')).toHaveClass(/marked/);
    const elapsed = Date.now() - start;

    expect(elapsed).toBeLessThan(10_000);
  });
});
