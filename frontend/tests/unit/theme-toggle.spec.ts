import { test, expect } from '@playwright/test';
import fc from 'fast-check';
import {
  getStoredTheme,
  setStoredTheme,
  initThemeToggle,
  type StorageLike,
  type Theme,
  type MediaQueryLike,
} from '../../src/theme-toggle';

function makeFakeStorage(initial: Record<string, string> = {}): StorageLike {
  const store = { ...initial };
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
  };
}

test('setStoredTheme then getStoredTheme round-trips any theme value', () => {
  fc.assert(
    fc.property(fc.constantFrom<Theme>('light', 'dark'), (theme) => {
      const storage = makeFakeStorage();
      setStoredTheme(storage, theme);
      expect(getStoredTheme(storage)).toBe(theme);
    }),
  );
});

test('getStoredTheme returns null for anything that is not a valid theme', () => {
  fc.assert(
    fc.property(
      fc.string().filter((s) => s !== 'light' && s !== 'dark'),
      (value) => {
        const storage = makeFakeStorage({ 'bingo-theme': value });
        expect(getStoredTheme(storage)).toBeNull();
      },
    ),
  );
});

test('getStoredTheme returns null when nothing has been stored yet', () => {
  expect(getStoredTheme(makeFakeStorage())).toBeNull();
});

test('getStoredTheme returns null when storage.getItem throws', () => {
  const throwingStorage: StorageLike = {
    getItem: () => {
      throw new Error('storage blocked');
    },
    setItem: () => {},
  };

  expect(() => getStoredTheme(throwingStorage)).not.toThrow();
  expect(getStoredTheme(throwingStorage)).toBeNull();
});

test('setStoredTheme swallows an error when storage.setItem throws', () => {
  const throwingStorage: StorageLike = {
    getItem: () => null,
    setItem: () => {
      throw new Error('storage full');
    },
  };

  expect(() => setStoredTheme(throwingStorage, 'dark')).not.toThrow();
});

interface FakeButton {
  element: HTMLElement;
  click: () => void;
}

function makeFakeButton(initialAttrs: Record<string, string> = {}): FakeButton {
  let clickHandler: (() => void) | undefined;
  const attrs = { ...initialAttrs };
  const element = {
    addEventListener: (type: string, listener: () => void) => {
      if (type === 'click') {
        clickHandler = listener;
      }
    },
    setAttribute: (name: string, value: string) => {
      attrs[name] = value;
    },
    getAttribute: (name: string) => attrs[name] ?? null,
  } as unknown as HTMLElement;
  return { element, click: () => clickHandler?.() };
}

function makeFakeRoot(initialAttrs: Record<string, string> = {}): HTMLElement {
  const attrs = { ...initialAttrs };
  return {
    setAttribute: (name: string, value: string) => {
      attrs[name] = value;
    },
    getAttribute: (name: string) => attrs[name] ?? null,
  } as unknown as HTMLElement;
}

function makeFakeDoc(button: HTMLElement | null, root: HTMLElement): Document {
  return {
    querySelector: (selector: string) =>
      selector.includes('theme-toggle') ? button : null,
    documentElement: root,
  } as unknown as Document;
}

test('initThemeToggle is a no-op when the toggle button is missing', () => {
  const root = makeFakeRoot();
  const doc = makeFakeDoc(null, root);

  expect(() => initThemeToggle(doc, makeFakeStorage())).not.toThrow();
  expect(root.getAttribute('data-theme')).toBeNull();
});

test('initThemeToggle syncs aria-pressed to whatever theme is already applied on load', () => {
  const fakeButton = makeFakeButton();
  const root = makeFakeRoot({ 'data-theme': 'dark' });
  const doc = makeFakeDoc(fakeButton.element, root);

  initThemeToggle(doc, makeFakeStorage());

  expect(fakeButton.element.getAttribute('aria-pressed')).toBe('true');
});

test('initThemeToggle does not force a data-theme choice, but reflects the OS preference on the button', () => {
  const fakeButton = makeFakeButton();
  const root = makeFakeRoot();
  const doc = makeFakeDoc(fakeButton.element, root);

  initThemeToggle(doc, makeFakeStorage(), { matches: true });

  // No explicit choice was ever made -- must NOT override the CSS
  // prefers-color-scheme fallback by forcing an attribute onto <html>.
  expect(root.getAttribute('data-theme')).toBeNull();
  // But the button itself should still reflect what's actually showing.
  expect(fakeButton.element.getAttribute('aria-pressed')).toBe('true');
});

test('the default prefersDark query falls back to a real window.matchMedia when present', () => {
  const fakeButton = makeFakeButton();
  const root = makeFakeRoot();
  const doc = makeFakeDoc(fakeButton.element, root);

  const globalWithWindow = globalThis as { window?: { matchMedia: (query: string) => MediaQueryLike } };
  const originalWindow = globalWithWindow.window;
  globalWithWindow.window = { matchMedia: () => ({ matches: true }) };
  try {
    // No third argument -- exercises the default parameter's real-browser path.
    initThemeToggle(doc, makeFakeStorage());
    expect(fakeButton.element.getAttribute('aria-pressed')).toBe('true');
  } finally {
    globalWithWindow.window = originalWindow;
  }
});

test('clicking the toggle switches the theme and persists the choice', () => {
  const fakeButton = makeFakeButton();
  const root = makeFakeRoot();
  const doc = makeFakeDoc(fakeButton.element, root);
  const storage = makeFakeStorage();

  initThemeToggle(doc, storage);
  fakeButton.click();

  expect(root.getAttribute('data-theme')).toBe('dark');
  expect(fakeButton.element.getAttribute('aria-pressed')).toBe('true');
  expect(getStoredTheme(storage)).toBe('dark');

  fakeButton.click();

  expect(root.getAttribute('data-theme')).toBe('light');
  expect(fakeButton.element.getAttribute('aria-pressed')).toBe('false');
  expect(getStoredTheme(storage)).toBe('light');
});
