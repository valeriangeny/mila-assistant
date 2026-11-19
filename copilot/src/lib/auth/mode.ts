export type AuthMode = 'unauthenticated' | 'authenticated' | 'incognito';

export type AuthUser = {
  sub: string;
  email: string;
  name: string;
  role: string;
  title?: string;
  preferred_username?: string;
};

export function deriveAuthMode(
  user: AuthUser | null,
  incognito: boolean
): AuthMode {
  if (user) return 'authenticated';
  if (incognito) return 'incognito';
  return 'unauthenticated';
}

export function effectiveRole(user: AuthUser | null, mode: AuthMode): string {
  if (mode === 'authenticated' && user?.role) return user.role;
  if (mode === 'incognito') return 'public';
  return '—';
}

export function agentProperties(user: AuthUser | null, mode: AuthMode) {
  return {
    config: {
      configurable: {
        auth_mode: mode,
        authenticated: mode === 'authenticated',
        role: mode === 'authenticated' ? user?.role ?? 'employee' : mode === 'incognito' ? 'public' : 'employee',
        mila_user_id: user?.sub ?? '',
        mila_user_name: user?.name ?? ''
      }
    }
  };
}
