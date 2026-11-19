import { NextResponse } from 'next/server';

import { OIDC_STATE_COOKIE } from '@/lib/auth/config';
import { buildAuthorizeUrl, createPkce, createState } from '@/lib/auth/oidc';
import { sessionCookieOptions } from '@/lib/auth/session';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const returnTo = url.searchParams.get('returnTo') || '/';

  const state = createState();
  const pkce = createPkce();
  const authorizeUrl = await buildAuthorizeUrl({
    state,
    challenge: pkce.challenge
  });

  const res = NextResponse.redirect(authorizeUrl);
  res.cookies.set(
    OIDC_STATE_COOKIE,
    JSON.stringify({ state, verifier: pkce.verifier, returnTo }),
    { ...sessionCookieOptions(600), httpOnly: true }
  );
  return res;
}
