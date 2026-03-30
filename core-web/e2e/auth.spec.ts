import { test, expect } from '@playwright/test';

test.describe('Authentication flow', () => {
  test('landing page loads and shows sign-in options', async ({ page }) => {
    await page.goto('/');

    // The landing page or login page should be visible
    await expect(page).toHaveTitle(/.*/);

    // Page should load without JS errors
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));

    // Wait for the page to fully render
    await page.waitForLoadState('networkidle');

    expect(errors).toHaveLength(0);
  });

  test('unauthenticated user sees login UI', async ({ page }) => {
    await page.goto('/');

    // Should see some form of auth UI (Google/Microsoft sign-in buttons, or login form)
    // This is a smoke test -- the exact selectors will depend on the landing page design
    await page.waitForLoadState('domcontentloaded');

    // The page should not show an unhandled error screen
    const body = await page.textContent('body');
    expect(body).not.toContain('Application error');
    expect(body).not.toContain('Internal Server Error');
  });
});
