import type { Page } from '@playwright/test';

export interface CreatedGame {
  joinUrl: string;
}

/**
 * Create a new game through the real UI (home screen) and return its
 * shareable join link, resolved to an absolute URL.
 */
export async function createGame(page: Page, name: string): Promise<CreatedGame> {
  await page.goto('/');
  await page.getByTestId('game-name-input').fill(name);
  await page.getByTestId('create-game-submit').click();

  const shareLink = page.getByTestId('share-link');
  const href = await shareLink.getAttribute('href');
  if (!href) {
    throw new Error('share-link element has no href attribute');
  }

  return { joinUrl: new URL(href, page.url()).toString() };
}

/**
 * Join an existing game through the real UI (join screen) and wait until
 * the player lands on their own board.
 */
export async function joinGame(page: Page, joinUrl: string, playerName: string): Promise<void> {
  await page.goto(joinUrl);
  await page.getByTestId('player-name-input').fill(playerName);
  await page.getByTestId('join-game-submit').click();
  await page.waitForURL(/\/board\//);
}
