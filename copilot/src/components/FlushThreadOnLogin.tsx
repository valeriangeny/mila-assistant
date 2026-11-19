'use client';

import { useAgent } from '@copilotkit/react-core/v2';
import { useEffect } from 'react';

import { flushThreadMessages } from '@/lib/chat/thread';

const AGENT_ID = 'mila_agent';

/**
 * Ensure the latest transcript is written before a full-page OIDC navigation
 * (click on Sign in / in-chat login links).
 */
export function FlushThreadOnLogin({ threadId }: { threadId: string }) {
  const { agent } = useAgent({ agentId: AGENT_ID });

  useEffect(() => {
    const flush = () => flushThreadMessages(threadId, agent.messages ?? []);

    const onPointerDown = (event: PointerEvent) => {
      const el = event.target as HTMLElement | null;
      if (!el) return;
      const anchor = el.closest('a[href*="/api/auth/login"], button[data-testid="sign-in"], button[data-testid="chat-auth-primary"]');
      if (anchor) flush();
    };

    const onPageHide = () => flush();

    document.addEventListener('pointerdown', onPointerDown, true);
    window.addEventListener('pagehide', onPageHide);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown, true);
      window.removeEventListener('pagehide', onPageHide);
    };
  }, [agent, threadId]);

  return null;
}
