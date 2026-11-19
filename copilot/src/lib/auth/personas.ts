/**
 * Local persona table mirroring instructions/users.json + mock IdP login.html.
 * mock-oauth2-server interactive login sets `sub` to the username (alice, …)
 * but tokenCallbacks only match token-request params, so we enrich claims here.
 */

export type Persona = {
  username: string;
  sub: string;
  email: string;
  name: string;
  role: string;
  title: string;
};

export const PERSONAS: Persona[] = [
  {
    username: 'alice',
    sub: 'u_alice',
    email: 'alice.chen@alim.example',
    name: 'Alice Chen',
    role: 'employee',
    title: 'Senior Research Engineer'
  },
  {
    username: 'priya',
    sub: 'u_priya',
    email: 'priya.shah@alim.example',
    name: 'Priya Shah',
    role: 'hr',
    title: 'VP, People Operations'
  },
  {
    username: 'marcus',
    sub: 'u_marcus',
    email: 'marcus.liu@alim.example',
    name: 'Marcus Liu',
    role: 'engineering',
    title: 'Chief Technology Officer'
  },
  {
    username: 'dana',
    sub: 'u_dana',
    email: 'dana.okafor@alim.example',
    name: 'Dana Okafor',
    role: 'security',
    title: 'Chief Information Security Officer'
  }
];

export function personaFromTokenClaims(claims: {
  sub?: string;
  preferred_username?: string;
  role?: string;
  email?: string;
  name?: string;
  title?: string;
}): Persona | null {
  const key = (claims.preferred_username || claims.sub || '').toLowerCase();
  const byUsername = PERSONAS.find((p) => p.username === key || p.sub === key);
  if (byUsername) return byUsername;

  // Token already carries full claims (non-interactive / future IdP).
  if (claims.sub && claims.role) {
    return {
      username: claims.preferred_username || claims.sub,
      sub: claims.sub,
      email: claims.email || '',
      name: claims.name || claims.sub,
      role: claims.role,
      title: claims.title || ''
    };
  }
  return null;
}
