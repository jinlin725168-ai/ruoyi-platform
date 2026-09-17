// Executor self-test: the login page renders, admin can sign in and reach the dashboard.
import { expect, test } from '@playwright/test';

test('admin signs in and lands on the dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.getByPlaceholder(/用户名|username/i).fill('admin');
  await page.getByPlaceholder(/密码|password/i).fill('admin123');
  await page.locator('button.submit-button').click();
  await expect(page).toHaveURL(/\/index/, { timeout: 30_000 });
  await expect(page.locator('.navbar, .sidebar-container').first()).toBeVisible({ timeout: 30_000 });
});
