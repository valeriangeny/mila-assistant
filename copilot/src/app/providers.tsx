'use client';

import { CopilotKit } from '@copilotkit/react-core/v2';
import { CopilotSidebar } from '@copilotkit/react-ui';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';

import { ChatAuthDemo } from '@/components/ChatAuthDemo';
import { createChatThreadHeader } from '@/components/ChatThreadHeader';
import { FlushThreadOnLogin } from '@/components/FlushThreadOnLogin';
import { MuiProvider } from '@/components/MuiProvider';
import { ThreadMessageCache } from '@/components/ThreadMessageCache';
import { UserBar } from '@/components/UserBar';
import { useAuthUser } from '@/hooks/useAuthUser';
import { usePersistentThreadId } from '@/hooks/usePersistentThreadId';
import { agentProperties, deriveAuthMode } from '@/lib/auth/mode';
import { hasCachedThreadMessages } from '@/lib/chat/thread';

import '@copilotkit/react-ui/styles.css';

/**
 * CopilotKit always prepends `labels.initial` to the transcript. Keep it
 * auth-agnostic (identity lives in the header / UserBar) and omit it entirely
 * once a thread has real messages — otherwise an OIDC return swaps in
 * "Signed in as …" on top of the restored history.
 */
const STABLE_WELCOME =
  'Ask about aliM policies, docs, or teams. Use Sign in in the top bar, or say “sign me in”.';

export function Providers({ children }: { children: ReactNode }) {
  const { user, setUser, loading } = useAuthUser();
  const [incognito, setIncognito] = useState(false);
  const { threadId, startNewThread } = usePersistentThreadId();
  const [hasMessages, setHasMessages] = useState(false);

  useEffect(() => {
    if (user) setIncognito(false);
  }, [user]);

  useEffect(() => {
    if (!threadId) {
      setHasMessages(false);
      return;
    }
    setHasMessages(hasCachedThreadMessages(threadId));
  }, [threadId]);

  const onHasMessages = useCallback((next: boolean) => {
    setHasMessages(next);
  }, []);

  const onContinueIncognito = useCallback(() => {
    setIncognito(true);
  }, []);

  const authMode = deriveAuthMode(user, incognito);

  const Header = useMemo(
    () => (threadId ? createChatThreadHeader(threadId, startNewThread) : undefined),
    [threadId, startNewThread]
  );

  return (
    <MuiProvider>
      <div className="mila-shell">
        <UserBar
          user={user}
          authMode={authMode}
          loading={loading}
          onUserChange={(next) => {
            setUser(next);
            if (!next) setIncognito(false);
          }}
        />
        {threadId ? (
          <CopilotKit
            key={threadId}
            runtimeUrl="/api/copilotkit"
            agent="mila_agent"
            threadId={threadId}
            useSingleEndpoint={false}
            properties={agentProperties(user, authMode)}
          >
            <ThreadMessageCache threadId={threadId} onHasMessages={onHasMessages} />
            <FlushThreadOnLogin threadId={threadId} />
            <ChatAuthDemo
              user={user}
              authMode={authMode}
              onContinueIncognito={onContinueIncognito}
            />
            <CopilotSidebar
              defaultOpen
              Header={Header}
              labels={{
                title:
                  authMode === 'authenticated' && user
                    ? `Mila · ${user.name}`
                    : authMode === 'incognito'
                      ? 'Mila · incognito'
                      : 'Mila assistant',
                // undefined → makeInitialMessages returns [] (no fake assistant turn)
                initial: hasMessages ? undefined : STABLE_WELCOME
              }}
            >
              {children}
            </CopilotSidebar>
          </CopilotKit>
        ) : (
          children
        )}
      </div>
    </MuiProvider>
  );
}
