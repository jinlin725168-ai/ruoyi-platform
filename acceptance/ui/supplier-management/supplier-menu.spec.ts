// spec: specs/ruoyi-supplier.plan.md
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('S1 业务管理目录与供应商管理菜单', () => {
  test('管理员可通过『业务管理』菜单进入供应商管理页', async ({ page }) => {
    // 1. 打开 /login，账号 admin、密码 admin123，点击「登 录」
    await page.goto('/login');
    await page.getByRole('textbox', { name: '用户名' }).fill('admin');
    await page.getByRole('textbox', { name: '密码' }).fill('admin123');
    await page.getByRole('button', { name: '登 录' }).click();

    // expect: 跳转到 /index，顶部菜单栏出现「业务管理」
    await expect(page).toHaveURL(/\/index$/);
    const bizMenu = page.getByRole('menuitem', { name: '业务管理' });
    await expect(bizMenu).toBeVisible();

    // 2. 点击顶部菜单「业务管理」
    await bizMenu.click();

    // expect: 展开的子菜单中有「供应商管理」（链接 /biz/supplier）
    const supplierMenuLink = page.getByRole('link', { name: '供应商管理' });
    await expect(supplierMenuLink).toBeVisible();
    await expect(supplierMenuLink).toHaveAttribute('href', '/biz/supplier');

    // 3. 点击「供应商管理」
    await supplierMenuLink.click();

    // expect: URL 为 /biz/supplier，页面标题包含「供应商管理」
    await expect(page).toHaveURL(/\/biz\/supplier$/);
    await expect(page).toHaveTitle(/供应商管理/);

    // expect: 面包屑显示 首页 / 业务管理 / 供应商管理
    await expect(page.getByRole('navigation', { name: '面包屑' })).toHaveText(/首页\s*\/\s*业务管理\s*\/\s*供应商管理/);

    // expect: 标签栏新增「供应商管理」页签
    await expect(page.locator('#tags-view-container').getByRole('link', { name: '供应商管理' })).toBeVisible();

    // expect: 可见「筛选条件」「供应商列表」区域，表头依次为 供应商编码、供应商名称、联系人、联系电话、状态、备注、操作
    await expect(page.getByRole('heading', { name: '筛选条件' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '供应商列表' })).toBeVisible();
    await expect(page.getByRole('columnheader').filter({ hasText: /\S/ })).toHaveText([
      '供应商编码',
      '供应商名称',
      '联系人',
      '联系电话',
      '状态',
      '备注',
      '操作',
    ]);
  });
});
