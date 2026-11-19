import { createHmac, timingSafeEqual } from 'node:crypto';

import { authSecret, SESSION_COOKIE } from './config';

export type SessionUser = {
  sub: string;
  email: string;
  name: string;
  role: string;
  title?: string;
  preferred_username?: string;
};

type SessionPayload = SessionUser & { exp: number };

function sign(body: string): string {
  return createHmac('sha256', authSecret()).update(body).digest('base64url');
}

export function sealSession(user: SessionUser, maxAgeSec = 3600): string {
  const payload: SessionPayload = {
    ...user,
    exp: Math.floor(Date.now() / 1000) + maxAgeSec
  };
  const body = Buffer.from(JSON.stringify(payload), 'utf8').toString('base64url');
  return `${body}.${sign(body)}`;
}

export function unsealSession(token: string | undefined | null): SessionUser | null {
  if (!token) return null;
  const [body, sig] = token.split('.');
  if (!body || !sig) return null;
  const expected = sign(body);
  try {
    const a = Buffer.from(sig);
    const b = Buffer.from(expected);
    if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  } catch {
    return null;
  }
  try {
    const payload = JSON.parse(
      Buffer.from(body, 'base64url').toString('utf8')
    ) as SessionPayload;
    if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
    if (!payload.sub || !payload.role) return null;
    return {
      sub: payload.sub,
      email: payload.email || '',
      name: payload.name || payload.preferred_username || payload.sub,
      role: payload.role,
      title: payload.title,
      preferred_username: payload.preferred_username
    };
  } catch {
    return null;
  }
}

export function sessionCookieOptions(maxAgeSec = 3600) {
  return {
    httpOnly: true,
    sameSite: 'lax' as const,
    path: '/',
    secure: process.env.NODE_ENV === 'production',
    maxAge: maxAgeSec
  };
}

export { SESSION_COOKIE };
