import { NextResponse } from 'next/server';

import { OIDC_STATE_COOKIE, appOrigin } from '@/lib/auth/config';
import { SESSION_COOKIE, sessionCookieOptions } from '@/lib/auth/session';

export const dynamic = 'force-dynamic';

export async function POST() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, '', { ...sessionCookieOptions(0), maxAge: 0 });
  res.cookies.set(OIDC_STATE_COOKIE, '', { ...sessionCookieOptions(0), maxAge: 0 });
  return res;
}

export async function GET() {
  const res = NextResponse.redirect(`${appOrigin()}/`);
  res.cookies.set(SESSION_COOKIE, '', { ...sessionCookieOptions(0), maxAge: 0 });
  res.cookies.set(OIDC_STATE_COOKIE, '', { ...sessionCookieOptions(0), maxAge: 0 });
  return res;
}
