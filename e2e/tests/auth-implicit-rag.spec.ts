import { expect, test } from '@playwright/test';

import { ensureSignedOut, pickMockPersona, sendChat } from './helpers/auth';

/**
 * Flow 3 — Implicit auth via RAG: knowledge question while unauthenticated
 * → retrieve returns auth_required → agent calls prompt_sign_in.
 * Requires Agent Server + Gemini + (ideally) Qdrant index.
 */
test.describe('auth flow: implicit RAG gate', () => {
  test('knowledge question while unauthenticated surfaces sign-in card', async ({
    page
  }) => {
    test.setTimeout(180_000);
    await ensureSignedOut(page);

    await sendChat(
      page,
      'What does the company-wide welcome handbook say about remote work?'
    );

    const card = page.getByTestId('chat-auth-card');
    await expect(card).toBeVisible({ timeout: 120_000 });
    await expect(page.getByTestId('chat-auth-primary')).toBeEnabled();

    // Complete sign-in so the flow is end-to-end, not just the prompt.
    await page.getByTestId('chat-auth-primary').click();
    await pickMockPersona(page, 'alice');
    await expect(page.getByTestId('user-bar-role')).toHaveText('employee');
  });
});
