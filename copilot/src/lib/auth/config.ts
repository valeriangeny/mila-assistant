/** Local mock OIDC settings (navikt mock-oauth2-server). */

export function oidcIssuer(): string {
  return (
    process.env.OIDC_ISSUER?.trim() || 'http://127.0.0.1:8090/default'
  ).replace(/\/$/, '');
}

export function oidcClientId(): string {
  return process.env.OIDC_CLIENT_ID?.trim() || 'mila-copilot';
}

/** Public origin of this Next app (used for redirect_uri). */
export function appOrigin(): string {
  return (
    process.env.APP_ORIGIN?.trim() ||
    process.env.NEXT_PUBLIC_APP_ORIGIN?.trim() ||
    'http://127.0.0.1:4000'
  ).replace(/\/$/, '');
}

export function oidcRedirectUri(): string {
  return `${appOrigin()}/api/auth/callback`;
}

export function authSecret(): string {
  const secret = process.env.AUTH_SECRET?.trim();
  if (secret) return secret;
  // Local-only fallback so `yarn dev:copilot` works without extra env.
  return 'mila-local-dev-auth-secret-change-me';
}

export const SESSION_COOKIE = 'mila_session';
export const OIDC_STATE_COOKIE = 'mila_oidc_state';
