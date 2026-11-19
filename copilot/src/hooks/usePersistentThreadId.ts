'use client';

import { useCallback, useEffect, useState } from 'react';

import { beginNewThread, getOrCreateThreadId } from '@/lib/chat/thread';

/** SSR-safe: null until mounted, then a stable localStorage-backed thread id. */
export function usePersistentThreadId(): {
  threadId: string | null;
  startNewThread: () => void;
} {
  const [threadId, setThreadId] = useState<string | null>(null);

  useEffect(() => {
    setThreadId(getOrCreateThreadId());
  }, []);

  const startNewThread = useCallback(() => {
    setThreadId(beginNewThread());
  }, []);

  return { threadId, startNewThread };
}
