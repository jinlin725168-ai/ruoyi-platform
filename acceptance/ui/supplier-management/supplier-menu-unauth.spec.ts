// spec: specs/plan.md
// seed: tests/seed.spec.ts
// NOTE: written from the plan's documented page structure; the app was unreachable during generation, so this has not been run yet.

import { test, expect } from '@playwright/test';

test.describe('S1 业务管理目录与供应商管理菜单', () => {
  test('未登录访问供应商管理页会跳转到登录页', async ({ browser }) => {
    // 全新浏览器上下文，不携带任何登录态
    const context = await browser.newContext({ storageState: { cookies: [], origins: [] } });
    const page = await context.newPage();

    // 1. 在未登录的全新浏览器上下文中打开 /biz/supplier
    await page.goto('/biz/supplier');
    await expect(page).toHaveURL(/\/login\?redirect=.*biz(%2F|\/)supplier/);
    await expect(page.getByRole('button', { name: '登 录' })).toBeVisible();

    // 2. 用 admin/admin123 登录
    await page.getByRole('textbox', { name: '用户名' }).fill('admin');
    await page.getByRole('textbox', { name: '密码' }).fill('admin123');
    await page.getByRole('button', { name: '登 录' }).click();
    await expect(page).toHaveURL(/\/biz\/supplier$/);
    await expect(page.getByText('供应商列表')).toBeVisible();
    await expect(page.getByPlaceholder('请输入供应商名称')).toBeVisible();

    await context.close();
  });
});
