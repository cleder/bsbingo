export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'bingo-theme';

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

function isTheme(value: string | null): value is Theme {
  return value === 'light' || value === 'dark';
}

/** Read the persisted theme choice, or `null` if none is stored (yet). */
export function getStoredTheme(storage: StorageLike): Theme | null {
  const value = storage.getItem(STORAGE_KEY);
  return isTheme(value) ? value : null;
}

/** Persist the user's explicit theme choice. */
export function setStoredTheme(storage: StorageLike, theme: Theme): void {
  storage.setItem(STORAGE_KEY, theme);
}

interface ThemeToggleTarget {
  button: HTMLElement;
  root: HTMLElement;
}

function findThemeToggleTarget(doc: Document): ThemeToggleTarget | null {
  const button = doc.querySelector<HTMLElement>('[data-testid="theme-toggle"]');
  if (!button) {
    return null;
  }
  return { button, root: doc.documentElement };
}

function currentTheme(root: HTMLElement): Theme {
  return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

function applyTheme(root: HTMLElement, button: HTMLElement, theme: Theme): void {
  root.setAttribute('data-theme', theme);
  button.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
}

/**
 * Wire up the light/dark toggle button: clicking it flips the theme,
 * persists the choice, and keeps the button's `aria-pressed` state in sync
 * -- including with whatever theme an inline boot script already applied to
 * `<html>` before this module loaded (to avoid a flash of the wrong theme).
 */
export function initThemeToggle(doc: Document, storage: StorageLike): void {
  const target = findThemeToggleTarget(doc);
  if (!target) {
    return;
  }
  const { button, root } = target;
  applyTheme(root, button, currentTheme(root));

  button.addEventListener('click', () => {
    const next: Theme = currentTheme(root) === 'dark' ? 'light' : 'dark';
    applyTheme(root, button, next);
    setStoredTheme(storage, next);
  });
}
