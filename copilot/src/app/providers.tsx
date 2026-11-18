'use client';

import { CopilotKit } from '@copilotkit/react-core/v2';
import { CopilotSidebar } from '@copilotkit/react-ui';
import type { ReactNode } from 'react';

import '@copilotkit/react-ui/styles.css';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="mila_agent" useSingleEndpoint={false}>
      <CopilotSidebar
        defaultOpen
        labels={{
          title: 'Mila assistant',
          initial: 'Ask about aliM AI Institute policies, docs, or teams. (Knowledge index lands in Phase 2.)'
        }}
      >
        {children}
      </CopilotSidebar>
    </CopilotKit>
  );
}
