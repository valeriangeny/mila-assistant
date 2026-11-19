import { expect, test } from '@playwright/test';

import { ensureSignedOut, pickMockPersona, sendChat } from './helpers/auth';

/**
 * Flow 2 — In-chat “sign me in” → prompt_sign_in card → mock IdP.
 * Requires Agent Server + Gemini (LANGGRAPH_URL).
 */
test.describe('auth flow: in-chat sign-in prompt', () => {
  test('sign me in card redirects to mock IdP (Marcus / engineering)', async ({
    page
  }) => {
    test.setTimeout(180_000);
    await ensureSignedOut(page);

    await sendChat(page, 'sign me in');

    const primary = page.getByTestId('chat-auth-primary');
    await expect(primary).toBeVisible({ timeout: 90_000 });
    await expect(primary).toBeEnabled();
    await primary.click();

    await pickMockPersona(page, 'marcus');
    await expect(page.getByTestId('user-bar-role')).toHaveText('engineering');
    await expect(page.getByTestId('user-bar-name')).toHaveText('Marcus Liu');
  });

  test('continue as incognito sets public role in the top bar', async ({ page }) => {
    test.setTimeout(180_000);
    await ensureSignedOut(page);

    await sendChat(page, 'please sign me in');
    const secondary = page.getByTestId('chat-auth-secondary');
    await expect(secondary).toBeVisible({ timeout: 90_000 });
    await secondary.click();

    await expect(page.getByTestId('user-bar')).toHaveAttribute(
      'data-auth-mode',
      'incognito'
    );
    await expect(page.getByTestId('user-bar-role')).toHaveText('public');
    await expect(page.getByTestId('chat-auth-incognito')).toBeVisible();
  });
});
