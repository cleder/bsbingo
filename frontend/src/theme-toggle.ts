export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'bingo-theme';

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export interface MediaQueryLike {
  matches: boolean;
}

function realPrefersDarkQuery(): MediaQueryLike {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : { matches: false };
}

function isTheme(value: string | null): value is Theme {
  return value === 'light' || value === 'dark';
}

/** Read the persisted theme choice, or `null` if none is stored (yet). */
export function getStoredTheme(storage: StorageLike): Theme | null {
  try {
    const value = storage.getItem(STORAGE_KEY);
    return isTheme(value) ? value : null;
  } catch {
    // Storage blocked (e.g. private browsing) -- treat as "no choice made".
    return null;
  }
}

/** Persist the user's explicit theme choice. */
export function setStoredTheme(storage: StorageLike, theme: Theme): void {
  try {
    storage.setItem(STORAGE_KEY, theme);
  } catch {
    // Storage blocked or full -- the toggle still works visually for this
    // page view, it just won't persist across visits.
  }
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

/**
 * The theme actually in effect: an explicit prior choice if one was made,
 * otherwise the OS's `prefers-color-scheme`.
 */
function currentTheme(root: HTMLElement, prefersDarkQuery: MediaQueryLike): Theme {
  const explicit = root.getAttribute('data-theme');
  if (isTheme(explicit)) {
    return explicit;
  }
  return prefersDarkQuery.matches ? 'dark' : 'light';
}

function applyTheme(root: HTMLElement, button: HTMLElement, theme: Theme): void {
  root.setAttribute('data-theme', theme);
  button.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
}

/**
 * Wire up the light/dark toggle button: clicking it flips the theme and
 * persists the choice. On load, only the button's `aria-pressed` is synced
 * to whatever theme is actually showing (an explicit prior choice, or the
 * OS preference) -- `data-theme` is deliberately left unset until the user
 * makes an explicit choice, so the CSS `prefers-color-scheme` fallback
 * still applies for first-time visitors instead of being silently
 * overridden to "light".
 */
export function initThemeToggle(
  doc: Document,
  storage: StorageLike,
  prefersDarkQuery: MediaQueryLike = realPrefersDarkQuery(),
): void {
  const target = findThemeToggleTarget(doc);
  if (!target) {
    return;
  }
  const { button, root } = target;
  button.setAttribute(
    'aria-pressed',
    currentTheme(root, prefersDarkQuery) === 'dark' ? 'true' : 'false',
  );

  button.addEventListener('click', () => {
    const next: Theme = currentTheme(root, prefersDarkQuery) === 'dark' ? 'light' : 'dark';
    applyTheme(root, button, next);
    setStoredTheme(storage, next);
  });
}
