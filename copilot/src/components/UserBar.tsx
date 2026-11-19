'use client';

import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import AppBar from '@mui/material/AppBar';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { useCallback, useEffect, useState } from 'react';

import { type AuthMode, type AuthUser, effectiveRole } from '@/lib/auth/mode';
import { authLoginHref, destroyClientThreadState } from '@/lib/chat/thread';

export type { AuthUser };

type Props = {
  user: AuthUser | null;
  authMode: AuthMode;
  loading?: boolean;
  onUserChange?: (user: AuthUser | null) => void;
};

function identityLabel(user: AuthUser | null, authMode: AuthMode): string {
  if (user) return user.name;
  if (authMode === 'incognito') return 'Incognito';
  return 'Unauthenticated';
}

function secondaryLine(user: AuthUser | null, authMode: AuthMode): string | null {
  if (user?.title) return user.title;
  if (authMode === 'incognito') return 'guest · public docs only';
  if (authMode === 'unauthenticated') return 'sign in for a verified role';
  return null;
}

export function UserBar({ user, authMode, loading, onUserChange }: Props) {
  const [busy, setBusy] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const role = effectiveRole(user, authMode);
  const detail = secondaryLine(user, authMode);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const err = params.get('authError');
    if (!err) return;
    setAuthError(err);
    params.delete('authError');
    const next = `${window.location.pathname}${params.toString() ? `?${params}` : ''}${window.location.hash}`;
    window.history.replaceState({}, '', next);
  }, []);

  const signIn = useCallback(() => {
    window.location.href = authLoginHref();
  }, []);

  const signOut = useCallback(async () => {
    setBusy(true);
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      onUserChange?.(null);
      destroyClientThreadState();
      // Hard navigation remounts CopilotKit without the prior thread.
      window.location.href = '/';
    } finally {
      setBusy(false);
    }
  }, [onUserChange]);

  return (
    <AppBar
      position="sticky"
      color="inherit"
      elevation={0}
      data-testid="user-bar"
      data-auth-mode={authMode}
      sx={{
        // Above Copilot sidebar (z-index ~30) and web-inspector chrome.
        zIndex: (t) => t.zIndex.modal + 1,
        borderBottom: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper'
      }}
    >
      <Toolbar
        sx={{
          gap: 2,
          minHeight: 'var(--mila-userbar-height) !important',
          height: 'var(--mila-userbar-height)',
          px: { xs: 2, sm: 3 }
        }}
      >
        <Stack direction="row" spacing={1} sx={{ alignItems: 'baseline', minWidth: 0 }}>
          <Typography
            variant="h6"
            component="div"
            sx={{ fontWeight: 700, color: 'primary.main', letterSpacing: 0.2 }}
          >
            Mila
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
            assistant
          </Typography>
        </Stack>
        {authError ? (
          <Typography
            variant="caption"
            color="error"
            data-testid="auth-error"
            title={authError}
            sx={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
          >
            Sign-in failed: {authError}. Use http://127.0.0.1:4000 and Sign in again (don’t reuse an old IdP tab).
          </Typography>
        ) : null}

        <Stack
          direction="row"
          spacing={1.5}
          data-testid="user-bar-who"
          sx={{ alignItems: 'center', ml: 'auto', minWidth: 0 }}
        >
          {loading ? (
            <Typography variant="body2" color="text.secondary">
              Checking session…
            </Typography>
          ) : (
            <>
              <Stack
                spacing={0}
                sx={{ alignItems: 'flex-end', minWidth: 0, display: { xs: 'none', sm: 'flex' } }}
              >
                <Typography
                  variant="subtitle2"
                  data-testid="user-bar-name"
                  noWrap
                  sx={{ maxWidth: 220, lineHeight: 1.2 }}
                >
                  {identityLabel(user, authMode)}
                </Typography>
                {detail ? (
                  <Typography variant="caption" color="text.secondary" noWrap sx={{ maxWidth: 220 }}>
                    {detail}
                  </Typography>
                ) : null}
              </Stack>
              <Chip
                size="small"
                label={role}
                color={authMode === 'authenticated' ? 'primary' : 'default'}
                variant={authMode === 'authenticated' ? 'filled' : 'outlined'}
                data-testid="user-bar-role"
                sx={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}
              />
              {user ? (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<LogoutIcon />}
                  disabled={busy}
                  onClick={signOut}
                  aria-label="Sign out"
                  data-testid="sign-out"
                >
                  Sign out
                </Button>
              ) : (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<LoginIcon />}
                  onClick={signIn}
                  aria-label="Sign in"
                  data-testid="sign-in"
                >
                  Sign in
                </Button>
              )}
            </>
          )}
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
