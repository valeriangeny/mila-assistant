import { expect, test } from '@playwright/test';

import { ensureSignedOut, pickMockPersona } from './helpers/auth';

/**
 * Flow 1 — Top bar Sign in → mock IdP → authenticated role in the bar.
 */
test.describe('auth flow: top bar', () => {
  test('sign in as Priya (hr) via top bar', async ({ page }) => {
    await ensureSignedOut(page);
    await expect(page.getByTestId('user-bar-role')).toHaveText('—');

    await page.getByTestId('sign-in').click({ timeout: 15_000 });
    await pickMockPersona(page, 'priya');

    await expect(page.getByTestId('user-bar-name')).toHaveText('Priya Shah');
    await expect(page.getByTestId('user-bar-role')).toHaveText('hr');
    await expect(page.getByTestId('sign-out')).toBeVisible();
  });
});
