import { test, expect } from '@playwright/test';
import fc from 'fast-check';
import { copyLink, initCopyLink, type ClipboardLike } from '../../src/copy-link';

test('copyLink writes exactly the given string to the clipboard and resolves true', async () => {
  await fc.assert(
    fc.asyncProperty(fc.string({ minLength: 1 }), async (link) => {
      const calls: string[] = [];
      const clipboard: ClipboardLike = {
        writeText: async (text) => {
          calls.push(text);
        },
      };

      const result = await copyLink(link, clipboard);

      expect(result).toBe(true);
      expect(calls).toEqual([link]);
    }),
  );
});

test('copyLink resolves false when the clipboard write rejects', async () => {
  await fc.assert(
    fc.asyncProperty(fc.string({ minLength: 1 }), async (link) => {
      const clipboard: ClipboardLike = {
        writeText: async () => {
          throw new Error('clipboard write denied');
        },
      };

      const result = await copyLink(link, clipboard);

      expect(result).toBe(false);
    }),
  );
});

interface FakeButton {
  element: HTMLElement;
  click: () => void;
}

function makeFakeButton(): FakeButton {
  let clickHandler: (() => void) | undefined;
  const element = {
    addEventListener: (type: string, listener: () => void) => {
      if (type === 'click') {
        clickHandler = listener;
      }
    },
  } as unknown as HTMLElement;
  return {
    element,
    click: () => clickHandler?.(),
  };
}

function makeFakeElement(attributes: Record<string, string> = {}): HTMLElement {
  return {
    getAttribute: (name: string) => attributes[name] ?? null,
    textContent: '',
  } as unknown as HTMLElement;
}

function makeFakeDoc(elements: {
  button?: HTMLElement | null;
  link?: HTMLElement | null;
  status?: HTMLElement | null;
}): Document {
  return {
    querySelector: (selector: string) => {
      if (selector.includes('copy-link-button')) return elements.button ?? null;
      if (selector.includes('share-link')) return elements.link ?? null;
      if (selector.includes('copy-status')) return elements.status ?? null;
      return null;
    },
  } as unknown as Document;
}

test('initCopyLink is a no-op when the required markup is missing', () => {
  const doc = makeFakeDoc({});
  const nav = { clipboard: { writeText: async () => {} } } as unknown as Navigator;

  expect(() => initCopyLink(doc, nav)).not.toThrow();
});

test('initCopyLink is a no-op when the Clipboard API is unavailable', () => {
  const fakeButton = makeFakeButton();
  const doc = makeFakeDoc({
    button: fakeButton.element,
    link: makeFakeElement({ 'data-share-link': 'https://example.test/join/1' }),
    status: makeFakeElement(),
  });
  const nav = {} as unknown as Navigator;

  initCopyLink(doc, nav);
  fakeButton.click();

  // No listener should have been attached, so click() is a harmless no-op.
});

test('clicking the button copies the share link and shows a success status', async () => {
  const fakeButton = makeFakeButton();
  const status = makeFakeElement();
  const writeTextCalls: string[] = [];
  const doc = makeFakeDoc({
    button: fakeButton.element,
    link: makeFakeElement({ 'data-share-link': 'https://example.test/join/42' }),
    status,
  });
  const nav = {
    clipboard: {
      writeText: async (text: string) => {
        writeTextCalls.push(text);
      },
    },
  } as unknown as Navigator;

  initCopyLink(doc, nav);
  fakeButton.click();
  await new Promise((resolve) => setTimeout(resolve, 0));

  expect(writeTextCalls).toEqual(['https://example.test/join/42']);
  expect(status.textContent).toBe('Link copied to clipboard.');
});

test('clicking the button shows a failure status when the clipboard write rejects', async () => {
  const fakeButton = makeFakeButton();
  const status = makeFakeElement();
  const doc = makeFakeDoc({
    button: fakeButton.element,
    link: makeFakeElement(),
    status,
  });
  const nav = {
    clipboard: {
      writeText: async () => {
        throw new Error('denied');
      },
    },
  } as unknown as Navigator;

  initCopyLink(doc, nav);
  fakeButton.click();
  await new Promise((resolve) => setTimeout(resolve, 0));

  expect(status.textContent).toBe('Could not copy automatically — select and copy the link text above.');
});
