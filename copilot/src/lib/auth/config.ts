/** Local mock OIDC settings (navikt mock-oauth2-server). */

export function oidcIssuer(): string {
  return (
    process.env.OIDC_ISSUER?.trim() || 'http://127.0.0.1:8090/default'
  ).replace(/\/$/, '');
}

export function oidcClientId(): string {
  return process.env.OIDC_CLIENT_ID?.trim() || 'mila-copilot';
}

/** Configured public origin (fallback when the request host is unavailable). */
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

/**
 * Origin the browser used for this request (Honors Host / X-Forwarded-*).
 * Prefer this for OIDC redirect_uri + post-login redirects so cookies set on
 * `localhost` are not lost when the callback hits `127.0.0.1` (or vice versa).
 */
export function requestOrigin(req: Request): string {
  const url = new URL(req.url);
  const proto =
    req.headers.get('x-forwarded-proto')?.split(',')[0]?.trim() ||
    url.protocol.replace(/:$/, '') ||
    'http';
  const host =
    req.headers.get('x-forwarded-host')?.split(',')[0]?.trim() ||
    req.headers.get('host')?.trim() ||
    url.host;
  if (!host) return appOrigin();
  return `${proto}://${host}`.replace(/\/$/, '');
}

export function authSecret(): string {
  const secret = process.env.AUTH_SECRET?.trim();
  if (secret) return secret;
  // Local-only fallback so `yarn dev:copilot` works without extra env.
  return 'mila-local-dev-auth-secret-change-me';
}

export const SESSION_COOKIE = 'mila_session';
export const OIDC_STATE_COOKIE = 'mila_oidc_state';
