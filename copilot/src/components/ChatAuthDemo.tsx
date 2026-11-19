'use client';

import { ToolCallStatus, useFrontendTool } from '@copilotkit/react-core/v2';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { useCallback, useState } from 'react';
import { z } from 'zod';

import type { AuthUser } from '@/lib/auth/mode';
import type { AuthMode } from '@/lib/auth/mode';
import { authLoginHref, destroyClientThreadState } from '@/lib/chat/thread';

type Props = {
  user: AuthUser | null;
  authMode: AuthMode;
  onContinueIncognito: () => void;
};

function AuthCard({
  title,
  reason,
  primaryLabel,
  secondaryLabel,
  onPrimary,
  onSecondary,
  footnote,
  testId = 'chat-auth-card'
}: {
  title: string;
  reason?: string;
  primaryLabel: string;
  secondaryLabel: string;
  onPrimary: () => void;
  onSecondary: () => void;
  footnote?: string;
  testId?: string;
}) {
  return (
    <Paper variant="outlined" sx={{ p: 2, maxWidth: 360, my: 1 }} data-testid={testId}>
      <Typography variant="overline" color="text.secondary">
        Feature demo · in-chat auth
      </Typography>
      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {reason?.trim() ||
          'Redirects to the mock IdP persona picker, then returns here with a verified role.'}
      </Typography>
      <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
        <Button
          size="small"
          variant="contained"
          data-testid="chat-auth-primary"
          onClick={onPrimary}
        >
          {primaryLabel}
        </Button>
        <Button
          size="small"
          variant="outlined"
          data-testid="chat-auth-secondary"
          onClick={onSecondary}
        >
          {secondaryLabel}
        </Button>
      </Stack>
      {footnote ? (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {footnote}
        </Typography>
      ) : null}
    </Paper>
  );
}

function StatusCard({
  title,
  body,
  testId
}: {
  title: string;
  body: string;
  testId?: string;
}) {
  return (
    <Paper variant="outlined" sx={{ p: 2, maxWidth: 360, my: 1 }} data-testid={testId}>
      <Typography variant="overline" color="text.secondary">
        Feature demo · in-chat auth
      </Typography>
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {body}
      </Typography>
    </Paper>
  );
}

/** Frontend tools: Sign-in / Switch-user. Secondary on sign-in → incognito (public). */
export function ChatAuthDemo({ user, authMode, onContinueIncognito }: Props) {
  const [dismissedSignIn, setDismissedSignIn] = useState<Record<string, boolean>>({});
  const [dismissedSwitch, setDismissedSwitch] = useState<Record<string, boolean>>({});

  const goLogin = useCallback(() => {
    window.location.href = authLoginHref();
  }, []);

  const switchUser = useCallback(async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    // Drop prior thread so the next persona does not see privileged history.
    destroyClientThreadState();
    window.location.href = authLoginHref();
  }, []);

  // CopilotKit expects "enabled" | "disabled" (boolean false does NOT disable).
  const signInAvailable = authMode !== 'authenticated' ? 'enabled' : 'disabled';
  const switchAvailable = authMode === 'authenticated' ? 'enabled' : 'disabled';

  useFrontendTool(
    {
      name: 'prompt_sign_in',
      agentId: 'mila_agent',
      description:
        'Show an in-chat Sign-in card for the mock OIDC IdP. Use when the user asks to ' +
        'sign in, or when retrieve_knowledge returns auth_required. Secondary action ' +
        'continues as incognito (public role). Do not invent credentials.',
      parameters: z.object({
        reason: z
          .string()
          .optional()
          .describe('Short explanation shown on the card (why sign-in is needed).')
      }),
      available: signInAvailable,
      handler: async ({ reason }) =>
        JSON.stringify({
          status: 'card_shown',
          action: 'awaiting_user_click',
          reason: reason ?? null
        }),
      render: ({ args, status, toolCallId }) => {
        const reason = typeof args.reason === 'string' ? args.reason : undefined;
        const id = toolCallId || 'sign-in';
        if (dismissedSignIn[id]) {
          return (
            <StatusCard
              testId="chat-auth-incognito"
              title="Continuing as incognito"
              body="Role public — company-wide public docs only. Ask again or sign in anytime."
            />
          );
        }
        return (
          <AuthCard
            title="Sign in to continue"
            reason={reason}
            primaryLabel="Sign in with mock IdP"
            secondaryLabel="Continue as incognito"
            onPrimary={goLogin}
            onSecondary={() => {
              setDismissedSignIn((prev) => ({ ...prev, [id]: true }));
              onContinueIncognito();
            }}
            footnote={
              status === ToolCallStatus.InProgress ? 'Loading card… buttons are ready.' : undefined
            }
          />
        );
      }
    },
    // Do not depend on dismissedSignIn / render closures — that re-registers the
    // tool on every card dismiss and can drop it mid-run for the LangGraph agent.
    [signInAvailable, goLogin, onContinueIncognito]
  );

  useFrontendTool(
    {
      name: 'prompt_switch_user',
      agentId: 'mila_agent',
      description:
        'Show an in-chat card to switch identity: signs out and redirects to the mock IdP. ' +
        'Use when the user asks to switch user, change role, or sign in as someone else.',
      parameters: z.object({
        reason: z.string().optional().describe('Short explanation shown on the card.')
      }),
      available: switchAvailable,
      handler: async ({ reason }) =>
        JSON.stringify({
          status: 'card_shown',
          action: 'awaiting_user_click',
          reason: reason ?? null
        }),
      render: ({ args, status, toolCallId }) => {
        const reason =
          (typeof args.reason === 'string' && args.reason.trim()) ||
          `Signed in as ${user?.name} (${user?.role}). Switch to another mock persona?`;
        const id = toolCallId || 'switch-user';
        if (dismissedSwitch[id]) {
          return (
            <StatusCard
              title="Staying signed in"
              body={`Still ${user?.name} (${user?.role}).`}
            />
          );
        }
        return (
          <AuthCard
            title="Switch user"
            reason={reason}
            primaryLabel="Switch via mock IdP"
            secondaryLabel="Stay signed in"
            onPrimary={() => {
              void switchUser();
            }}
            onSecondary={() => setDismissedSwitch((prev) => ({ ...prev, [id]: true }))}
            footnote={
              status === ToolCallStatus.InProgress ? 'Loading card… buttons are ready.' : undefined
            }
          />
        );
      }
    },
    [switchAvailable, authMode, user, switchUser]
  );

  return null;
}
