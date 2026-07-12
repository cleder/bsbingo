export interface ClipboardLike {
  writeText(text: string): Promise<void>;
}

/**
 * Copy `link` to the clipboard, resolving to whether the write succeeded.
 */
export async function copyLink(link: string, clipboard: ClipboardLike): Promise<boolean> {
  try {
    await clipboard.writeText(link);
    return true;
  } catch {
    return false;
  }
}

interface CopyLinkTarget {
  button: HTMLElement;
  link: HTMLElement;
  status: HTMLElement;
}

function findCopyLinkTarget(doc: Document): CopyLinkTarget | null {
  const button = doc.querySelector<HTMLElement>('[data-testid="copy-link-button"]');
  const link = doc.querySelector<HTMLElement>('[data-testid="share-link"]');
  const status = doc.querySelector<HTMLElement>('[data-testid="copy-status"]');
  if (!button || !link || !status) {
    return null;
  }
  return { button, link, status };
}

/**
 * Wire up the "Copy Link" button (FR-003): on click, copy the share link to
 * the clipboard and show a visible confirmation. If the required markup is
 * missing or the Clipboard API is unavailable, this is a no-op and the link
 * text itself stays visible/selectable so it can still be copied by hand
 * (spec Assumptions).
 */
export function initCopyLink(doc: Document, nav: Navigator): void {
  const target = findCopyLinkTarget(doc);
  if (!target || !nav.clipboard) {
    return;
  }

  const { button, link, status } = target;
  const shareLink = link.getAttribute('data-share-link') ?? '';

  button.addEventListener('click', () => {
    void copyLink(shareLink, nav.clipboard).then((ok) => {
      status.textContent = ok
        ? 'Link copied to clipboard.'
        : 'Could not copy automatically — select and copy the link text above.';
    });
  });
}
