import { test, expect } from '@playwright/test';

test.describe('Create and share a game (US1)', () => {
  test('autofocuses the game name field on load', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('game-name-input')).toBeFocused();
  });

  test('submits with the Enter key, same as tapping the button', async ({ page }) => {
    await page.goto('/');
    const nameInput = page.getByTestId('game-name-input');
    await nameInput.fill('Enter Key Game');
    await nameInput.press('Enter');

    await expect(page.getByTestId('share-link')).toBeVisible();
  });

  test('shows an inline validation error for a blank/whitespace name', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('game-name-input').fill('   ');
    await page.getByTestId('create-game-submit').click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByTestId('game-name-input')).toBeVisible();
  });

  test('shows a share screen with a working Copy Link action after creation', async ({
    page,
    context,
  }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await page.goto('/');
    await page.getByTestId('game-name-input').fill('Share Screen Game');
    await page.getByTestId('create-game-submit').click();

    const shareLink = page.getByTestId('share-link');
    await expect(shareLink).toBeVisible();
    const href = await shareLink.getAttribute('href');
    expect(href).toContain('/join/');

    await page.getByTestId('copy-link-button').click();
    await expect(page.getByRole('status')).toBeVisible();

    const copiedText = await page.evaluate(() => navigator.clipboard.readText());
    expect(copiedText).toBe(href);

    await expect(page.getByTestId('create-another-game')).toBeVisible();
  });

  test('can be completed using only the keyboard (FR-011)', async ({ page }) => {
    await page.goto('/');

    // autofocus (FR-001) already puts focus on the field -- no .click()/
    // .focus() calls anywhere in this test. Tab forward to prove the submit
    // button itself is keyboard-reachable and operable, not just the field.
    await expect(page.getByTestId('game-name-input')).toBeFocused();
    await page.keyboard.type('Keyboard Only Game');
    await page.keyboard.press('Tab');
    await expect(page.getByTestId('create-game-submit')).toBeFocused();
    await page.keyboard.press('Enter');

    await expect(page.getByTestId('share-link')).toBeVisible();
  });
});
