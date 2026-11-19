import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { SESSION_COOKIE, unsealSession } from '@/lib/auth/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  const jar = await cookies();
  const user = unsealSession(jar.get(SESSION_COOKIE)?.value);
  if (!user) {
    return NextResponse.json({ user: null });
  }
  return NextResponse.json({ user });
}
