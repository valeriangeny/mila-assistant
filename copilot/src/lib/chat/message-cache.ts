import { messagesStorageKey } from '@/lib/chat/thread';

export type CachedMessage = {
  id?: string;
  role?: string;
  content?: unknown;
  [key: string]: unknown;
};

export function readMessageCache(threadId: string): CachedMessage[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(messagesStorageKey(threadId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed) || parsed.length === 0) return [];
    return parsed as CachedMessage[];
  } catch {
    return [];
  }
}

/**
 * Persist messages, but never replace a richer cache with a shorter transcript
 * during the post-mount protect window (connectAgent often clears then
 * partially rebuilds after OIDC).
 */
export function writeMessageCache(
  threadId: string,
  messages: unknown[],
  opts?: { allowShrink?: boolean }
): void {
  if (typeof window === 'undefined') return;
  if (!Array.isArray(messages) || messages.length === 0) return;

  const existing = readMessageCache(threadId);
  if (!opts?.allowShrink && existing.length > messages.length) {
    return;
  }

  try {
    window.localStorage.setItem(messagesStorageKey(threadId), JSON.stringify(messages));
  } catch {
    // Quota / private mode — non-fatal.
  }
}
