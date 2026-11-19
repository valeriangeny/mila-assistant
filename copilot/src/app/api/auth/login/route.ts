import { NextResponse } from 'next/server';

import { OIDC_STATE_COOKIE, requestOrigin } from '@/lib/auth/config';
import { buildAuthorizeUrl, createPkce, createState } from '@/lib/auth/oidc';
import { sessionCookieOptions } from '@/lib/auth/session';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const returnTo = url.searchParams.get('returnTo') || '/';
  // Bind redirect_uri + PKCE cookie to the Host the browser actually used
  // (localhost vs 127.0.0.1 must match or callback loses the cookie).
  const origin = requestOrigin(req);
  const redirectUri = `${origin}/api/auth/callback`;

  const state = createState();
  const pkce = createPkce();
  const authorizeUrl = await buildAuthorizeUrl({
    state,
    challenge: pkce.challenge,
    redirectUri
  });

  const res = NextResponse.redirect(authorizeUrl);
  res.cookies.set(
    OIDC_STATE_COOKIE,
    JSON.stringify({
      state,
      verifier: pkce.verifier,
      returnTo,
      redirectUri
    }),
    { ...sessionCookieOptions(600), httpOnly: true }
  );
  return res;
}
