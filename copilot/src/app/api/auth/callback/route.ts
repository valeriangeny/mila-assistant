import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { OIDC_STATE_COOKIE, oidcRedirectUri, requestOrigin } from '@/lib/auth/config';
import { exchangeCode, userFromIdToken } from '@/lib/auth/oidc';
import {
  SESSION_COOKIE,
  sealSession,
  sessionCookieOptions
} from '@/lib/auth/session';

export const dynamic = 'force-dynamic';

type StateCookie = {
  state: string;
  verifier: string;
  returnTo?: string;
  redirectUri?: string;
};

function safeReturnTo(value: string | undefined): string {
  if (!value || !value.startsWith('/') || value.startsWith('//')) return '/';
  return value;
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const err = url.searchParams.get('error');
  const origin = requestOrigin(req);

  const jar = await cookies();
  let stored: StateCookie | null = null;
  const raw = jar.get(OIDC_STATE_COOKIE)?.value;
  if (raw) {
    try {
      stored = JSON.parse(raw) as StateCookie;
    } catch {
      stored = null;
    }
  }

  const fail = (message: string) => {
    const res = NextResponse.redirect(
      `${origin}/?authError=${encodeURIComponent(message)}`
    );
    res.cookies.set(OIDC_STATE_COOKIE, '', { ...sessionCookieOptions(0), maxAge: 0 });
    return res;
  };

  if (err) return fail(err);
  if (!code || !state || !stored?.state || !stored.verifier) {
    return fail('missing_code_or_state');
  }
  if (stored.state !== state) return fail('state_mismatch');

  const redirectUri =
    stored.redirectUri || `${origin}/api/auth/callback` || oidcRedirectUri();

  try {
    const tokens = await exchangeCode({
      code,
      verifier: stored.verifier,
      redirectUri
    });
    if (!tokens.id_token) return fail('missing_id_token');
    const user = await userFromIdToken(tokens.id_token);
    const sealed = sealSession(user, tokens.expires_in || 3600);

    const res = NextResponse.redirect(
      `${origin}${safeReturnTo(stored.returnTo)}`
    );
    res.cookies.set(SESSION_COOKIE, sealed, sessionCookieOptions(tokens.expires_in || 3600));
    res.cookies.set(OIDC_STATE_COOKIE, '', { ...sessionCookieOptions(0), maxAge: 0 });
    return res;
  } catch (e) {
    const message = e instanceof Error ? e.message : 'callback_failed';
    return fail(message);
  }
}
