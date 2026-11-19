import { createHash, randomBytes } from 'node:crypto';

import { createRemoteJWKSet, jwtVerify } from 'jose';

import { oidcClientId, oidcIssuer, oidcRedirectUri } from './config';
import { personaFromTokenClaims } from './personas';
import type { SessionUser } from './session';

export type OidcDiscovery = {
  authorization_endpoint: string;
  token_endpoint: string;
  jwks_uri: string;
  issuer: string;
};

export type PkcePair = {
  verifier: string;
  challenge: string;
};

let discoveryCache: { at: number; doc: OidcDiscovery } | null = null;

export async function fetchDiscovery(): Promise<OidcDiscovery> {
  const now = Date.now();
  if (discoveryCache && now - discoveryCache.at < 60_000) {
    return discoveryCache.doc;
  }
  const res = await fetch(`${oidcIssuer()}/.well-known/openid-configuration`, {
    cache: 'no-store'
  });
  if (!res.ok) {
    throw new Error(`OIDC discovery failed: ${res.status}`);
  }
  const doc = (await res.json()) as OidcDiscovery;
  discoveryCache = { at: now, doc };
  return doc;
}

export function createPkce(): PkcePair {
  const verifier = randomBytes(32).toString('base64url');
  const challenge = createHash('sha256').update(verifier).digest('base64url');
  return { verifier, challenge };
}

export function createState(): string {
  return randomBytes(24).toString('base64url');
}

export async function buildAuthorizeUrl(opts: {
  state: string;
  challenge: string;
}): Promise<string> {
  const discovery = await fetchDiscovery();
  const url = new URL(discovery.authorization_endpoint);
  url.searchParams.set('client_id', oidcClientId());
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('redirect_uri', oidcRedirectUri());
  url.searchParams.set('scope', 'openid profile email');
  url.searchParams.set('state', opts.state);
  url.searchParams.set('code_challenge', opts.challenge);
  url.searchParams.set('code_challenge_method', 'S256');
  return url.toString();
}

type TokenResponse = {
  id_token?: string;
  access_token?: string;
  token_type?: string;
  expires_in?: number;
};

export async function exchangeCode(opts: {
  code: string;
  verifier: string;
}): Promise<TokenResponse> {
  const discovery = await fetchDiscovery();
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code: opts.code,
    redirect_uri: oidcRedirectUri(),
    client_id: oidcClientId(),
    code_verifier: opts.verifier
  });
  const res = await fetch(discovery.token_endpoint, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Token exchange failed (${res.status}): ${text}`);
  }
  return (await res.json()) as TokenResponse;
}

export async function userFromIdToken(idToken: string): Promise<SessionUser> {
  const discovery = await fetchDiscovery();
  const jwks = createRemoteJWKSet(new URL(discovery.jwks_uri));
  // Mock IdP may omit or vary `aud`; verify signature + issuer, then enrich.
  const { payload } = await jwtVerify(idToken, jwks, {
    issuer: discovery.issuer
  });

  const persona = personaFromTokenClaims({
    sub: typeof payload.sub === 'string' ? payload.sub : undefined,
    preferred_username:
      typeof payload.preferred_username === 'string'
        ? payload.preferred_username
        : undefined,
    role: typeof payload.role === 'string' ? payload.role : undefined,
    email: typeof payload.email === 'string' ? payload.email : undefined,
    name: typeof payload.name === 'string' ? payload.name : undefined,
    title: typeof payload.title === 'string' ? payload.title : undefined
  });
  if (!persona) {
    throw new Error('id_token subject is not a known Mila persona');
  }

  return {
    sub: persona.sub,
    role: persona.role,
    email: persona.email,
    name: persona.name,
    title: persona.title,
    preferred_username: persona.username
  };
}
