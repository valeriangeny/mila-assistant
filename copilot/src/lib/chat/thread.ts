/** Stable CopilotKit / LangGraph thread id across OIDC redirects. */

export const THREAD_STORAGE_KEY = 'mila.copilot.threadId';
export const THREAD_QUERY_PARAM = 'thread';

export const messagesStorageKey = (threadId: string) =>
  `mila.copilot.messages.${threadId}`;

/** True when localStorage already holds a non-empty transcript for this thread. */
export function hasCachedThreadMessages(threadId: string): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const raw = window.localStorage.getItem(messagesStorageKey(threadId));
    if (!raw) return false;
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) && parsed.length > 0;
  } catch {
    return false;
  }
}

/** Call immediately before OIDC redirect so the latest turn is on disk. */
export function flushThreadMessages(threadId: string | null | undefined, messages: unknown): void {
  if (!threadId || !Array.isArray(messages) || messages.length === 0) return;
  try {
    window.localStorage.setItem(messagesStorageKey(threadId), JSON.stringify(messages));
  } catch {
    // ignore
  }
}

function newThreadId(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `thread-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/** Prefer `?thread=` (OIDC returnTo), then localStorage, else create. */
export function getOrCreateThreadId(): string {
  if (typeof window === 'undefined') {
    throw new Error('getOrCreateThreadId is browser-only');
  }

  const fromUrl = new URL(window.location.href).searchParams
    .get(THREAD_QUERY_PARAM)
    ?.trim();
  if (fromUrl) {
    window.localStorage.setItem(THREAD_STORAGE_KEY, fromUrl);
    return fromUrl;
  }

  const existing = window.localStorage.getItem(THREAD_STORAGE_KEY)?.trim();
  if (existing) return existing;

  const id = newThreadId();
  window.localStorage.setItem(THREAD_STORAGE_KEY, id);
  return id;
}

export function peekThreadId(): string | null {
  if (typeof window === 'undefined') return null;
  const fromUrl = new URL(window.location.href).searchParams
    .get(THREAD_QUERY_PARAM)
    ?.trim();
  if (fromUrl) return fromUrl;
  return window.localStorage.getItem(THREAD_STORAGE_KEY)?.trim() || null;
}

/** Path (+ query) for OIDC returnTo so the callback remounts the same thread. */
export function loginReturnTo(threadId?: string | null): string {
  const id =
    threadId?.trim() ||
    (typeof window !== 'undefined' ? peekThreadId() : null) ||
    '';
  if (!id) return '/';
  return `/?${THREAD_QUERY_PARAM}=${encodeURIComponent(id)}`;
}

export function authLoginHref(threadId?: string | null): string {
  return `/api/auth/login?returnTo=${encodeURIComponent(loginReturnTo(threadId))}`;
}

export function clearThreadId(): void {
  if (typeof window === 'undefined') return;
  const id = window.localStorage.getItem(THREAD_STORAGE_KEY)?.trim();
  window.localStorage.removeItem(THREAD_STORAGE_KEY);
  if (id) window.localStorage.removeItem(messagesStorageKey(id));
  // Drop ?thread= so the next mount does not resurrect the old conversation.
  const url = new URL(window.location.href);
  if (url.searchParams.has(THREAD_QUERY_PARAM)) {
    url.searchParams.delete(THREAD_QUERY_PARAM);
    window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
  }
}

/**
 * Wipe client chat continuity after sign-out / switch-user.
 * Auth itself is not stored on the thread — it is re-sent each run via
 * CopilotKit properties — but message history is thread-keyed and can retain
 * privileged answers, so the thread must go too.
 */
export function destroyClientThreadState(): void {
  clearThreadId();
}

/** Mint a new thread, point storage + URL at it (keeps prior thread caches). */
export function beginNewThread(): string {
  if (typeof window === 'undefined') {
    throw new Error('beginNewThread is browser-only');
  }
  const id = newThreadId();
  window.localStorage.setItem(THREAD_STORAGE_KEY, id);
  const url = new URL(window.location.href);
  url.searchParams.set(THREAD_QUERY_PARAM, id);
  window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
  return id;
}

/** Short label for chrome; full id stays in title / data attributes. */
export function shortThreadId(threadId: string, keep = 8): string {
  const id = threadId.trim();
  if (id.length <= keep) return id;
  return id.slice(0, keep);
}
