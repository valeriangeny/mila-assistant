'use client';

import { useAgent } from '@copilotkit/react-core/v2';
import { useEffect, useRef } from 'react';

import { readMessageCache, writeMessageCache } from '@/lib/chat/message-cache';

const AGENT_ID = 'mila_agent';
/** Don't let a short connectAgent replay shrink the durable cache. */
const PROTECT_MS = 8_000;

type Props = {
  threadId: string;
  /** Fires when the live transcript is empty vs non-empty (for welcome suppression). */
  onHasMessages?: (hasMessages: boolean) => void;
};

/**
 * localStorage is the durable transcript across OIDC full-page navigations.
 * CopilotKit connectAgent often clears or partially rebuilds the agent after
 * mount; whenever the live transcript is shorter than the cache, re-apply it.
 */
export function ThreadMessageCache({ threadId, onHasMessages }: Props) {
  const { agent } = useAgent({ agentId: AGENT_ID });
  const mountedAtRef = useRef(0);
  const applyingRef = useRef(false);

  useEffect(() => {
    mountedAtRef.current = Date.now();
    applyingRef.current = false;
  }, [threadId]);

  useEffect(() => {
    const applyCacheIfNeeded = () => {
      if (applyingRef.current) return;
      const cached = readMessageCache(threadId);
      if (!cached.length) return;

      const liveLen = agent.messages?.length ?? 0;
      if (liveLen >= cached.length) return;

      applyingRef.current = true;
      try {
        agent.setMessages(cached as typeof agent.messages);
      } catch {
        // Ignore setMessages rejection.
      } finally {
        window.setTimeout(() => {
          applyingRef.current = false;
        }, 100);
      }
    };

    applyCacheIfNeeded();
    const timers = [200, 500, 1000, 2000, 4000, 7000].map((ms) =>
      window.setTimeout(applyCacheIfNeeded, ms)
    );
    return () => timers.forEach((t) => window.clearTimeout(t));
  }, [agent, threadId]);

  // useAgent re-renders on message changes — heal if connect wiped / shortened us.
  useEffect(() => {
    if (applyingRef.current) return;
    const cached = readMessageCache(threadId);
    if (!cached.length) return;
    const liveLen = agent.messages?.length ?? 0;
    if (liveLen >= cached.length) return;

    applyingRef.current = true;
    try {
      agent.setMessages(cached as typeof agent.messages);
    } catch {
      // ignore
    } finally {
      window.setTimeout(() => {
        applyingRef.current = false;
      }, 100);
    }
  }, [agent, agent.messages, threadId]);

  useEffect(() => {
    const messages = agent.messages ?? [];
    const cachedLen = readMessageCache(threadId).length;
    onHasMessages?.(messages.length > 0 || cachedLen > 0);

    if (!messages.length) return;

    const allowShrink = Date.now() - mountedAtRef.current >= PROTECT_MS;
    writeMessageCache(threadId, messages, { allowShrink });
  }, [agent.messages, threadId, onHasMessages]);

  return null;
}
