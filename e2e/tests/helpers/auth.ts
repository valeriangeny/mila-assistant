import { expect, type Page } from '@playwright/test';

export type Persona = 'alice' | 'priya' | 'marcus' | 'dana';

const PERSONA_ROLE: Record<Persona, string> = {
  alice: 'employee',
  priya: 'hr',
  marcus: 'engineering',
  dana: 'security'
};

/** Ensure a clean unauthenticated session on the CoAgent origin. */
export async function ensureSignedOut(page: Page) {
  await page.goto('/api/auth/logout', { waitUntil: 'domcontentloaded' });
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  // CopilotKit web inspector sits on the right and intercepts Sign in clicks.
  await page.addStyleTag({
    content: 'cpk-web-inspector, [class*="Inspector"] { display: none !important; }'
  });
  await expect(page.getByTestId('user-bar')).toHaveAttribute(
    'data-auth-mode',
    'unauthenticated',
    { timeout: 15_000 }
  );
}

/** Complete mock IdP persona picker (already on :8090 authorize page). */
export async function pickMockPersona(page: Page, persona: Persona) {
  await expect(page).toHaveURL(/127\.0\.0\.1:8090\/default\/authorize/);
  const label =
    persona === 'alice'
      ? /Alice Chen/
      : persona === 'priya'
        ? /Priya Shah/
        : persona === 'marcus'
          ? /Marcus Liu/
          : /Dana Okafor/;
  await page.getByRole('button', { name: label }).click();
  await page.waitForURL(/127\.0\.0\.1:4000\/?/);
  await expect(page.getByTestId('user-bar')).toHaveAttribute(
    'data-auth-mode',
    'authenticated'
  );
  await expect(page.getByTestId('user-bar-role')).toHaveText(PERSONA_ROLE[persona]);
}

export async function openChat(page: Page) {
  const close = page.getByRole('button', { name: /Close Chat/i });
  if (await close.isVisible().catch(() => false)) return;
  await page.getByRole('button', { name: /Open Chat/i }).click();
  await expect(page.getByPlaceholder(/Type a message/i)).toBeVisible();
}

export async function sendChat(page: Page, text: string) {
  await openChat(page);
  const box = page.getByPlaceholder(/Type a message/i);
  await box.fill(text);
  await page.getByRole('button', { name: /^Send$/i }).click();
}

export { PERSONA_ROLE };
