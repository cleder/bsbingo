import { test, expect } from '@playwright/test';

test.describe('Light/dark theme toggle (shared across every screen)', () => {
  test('defaults to light, switches to dark on click, and persists across reload', async ({
    page,
  }) => {
    await page.goto('/');

    const html = page.locator('html');
    const toggle = page.getByTestId('theme-toggle');
    await expect(html).not.toHaveAttribute('data-theme', 'dark');
    await expect(toggle).toHaveAttribute('aria-pressed', 'false');

    await toggle.click();
    await expect(html).toHaveAttribute('data-theme', 'dark');
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');

    await page.reload();
    await expect(html).toHaveAttribute('data-theme', 'dark');
    await expect(page.getByTestId('theme-toggle')).toHaveAttribute('aria-pressed', 'true');
  });

  test('toggling back to light persists too', async ({ page }) => {
    await page.goto('/');
    const html = page.locator('html');
    const toggle = page.getByTestId('theme-toggle');

    await toggle.click();
    await expect(html).toHaveAttribute('data-theme', 'dark');
    await toggle.click();
    await expect(html).toHaveAttribute('data-theme', 'light');

    await page.reload();
    await expect(html).toHaveAttribute('data-theme', 'light');
  });

  test('is reachable and operable using only the keyboard (FR-011)', async ({ page }) => {
    await page.goto('/');
    const toggle = page.getByTestId('theme-toggle');

    await toggle.focus();
    await page.keyboard.press('Enter');

    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  });

  test('is present on the join, board, and not-found screens too', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('game-name-input').fill('Theme Toggle Everywhere');
    await page.getByTestId('create-game-submit').click();
    const joinUrl = await page.getByTestId('share-link').getAttribute('href');

    await page.goto(joinUrl!);
    await expect(page.getByTestId('theme-toggle')).toBeVisible();

    await page.getByTestId('player-name-input').fill('Auditor');
    await page.getByTestId('join-game-submit').click();
    await expect(page.getByTestId('theme-toggle')).toBeVisible();

    await page.goto('/board/00000000-0000-0000-0000-000000000000/');
    await expect(page.getByTestId('theme-toggle')).toBeVisible();
  });
});
