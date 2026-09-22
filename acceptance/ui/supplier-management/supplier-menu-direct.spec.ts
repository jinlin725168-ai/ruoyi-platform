// spec: specs/plan.md
// seed: tests/seed.spec.ts
// NOTE: written from the plan's documented page structure; the app was unreachable during generation, so this has not been run yet.

import { test, expect } from '@playwright/test';

test.describe('S1 业务管理目录与供应商管理菜单', () => {
  test('直接访问 /biz/supplier 并刷新，页面仍能正常显示', async ({ page }) => {
    const suffix = `AUTO_${Date.now()}`;
    const code = `SUP_${suffix}`;
    const name = `供应商_${suffix}`;

    // 登录
    await page.goto('/login');
    await page.getByRole('textbox', { name: '用户名' }).fill('admin');
    await page.getByRole('textbox', { name: '密码' }).fill('admin123');
    await page.getByRole('button', { name: '登 录' }).click();
    await expect(page).toHaveURL(/\/index/);

    // 1. 登录后在地址栏直接打开 /biz/supplier
    await page.goto('/biz/supplier');
    await expect(page).toHaveURL(/\/biz\/supplier/);
    await expect(page.getByText('404', { exact: true })).toHaveCount(0);
    await expect(page.getByText('供应商列表')).toBeVisible();
    await expect(page.getByPlaceholder('请输入供应商名称')).toBeVisible();
    await expect(page.getByRole('button', { name: '新增' })).toBeVisible();

    // 准备数据：新增一条带时间戳后缀的供应商，用于验证刷新后列表重新加载
    await page.getByRole('button', { name: '新增' }).click();
    const dialog = page.getByRole('dialog', { name: '添加供应商' });
    await expect(dialog).toBeVisible();
    await dialog.getByPlaceholder('请输入供应商编码').fill(code);
    await dialog.getByPlaceholder('请输入供应商名称').fill(name);
    // 供应商分类为必填项，选择字典中的第一个分类
    await dialog.locator('.el-form-item').filter({ hasText: '供应商分类' }).locator('.el-select__wrapper').click();
    await page.locator('.el-select-dropdown__item:visible').first().click();
    await dialog.getByRole('button', { name: '确 定' }).click();
    await expect(page.getByText('操作成功')).toBeVisible();
    await expect(dialog).toBeHidden();

    // 2. 刷新浏览器
    await page.reload();
    await expect(page).toHaveURL(/\/biz\/supplier/);
    await expect(page.getByText('404', { exact: true })).toHaveCount(0);
    await expect(page.getByText('供应商列表')).toBeVisible();
    await expect(page.getByText(/共 \d+ 条记录/)).toBeVisible();
    await page.getByPlaceholder('请输入供应商名称').fill(name);
    await page.getByRole('button', { name: '搜索' }).click();
    const row = page.getByRole('row').filter({ hasText: code });
    await expect(row).toBeVisible();
    await expect(row).toContainText(name);

    // 清理：删除本场景创建的数据
    // el-checkbox 的原生 input 被隐藏，点击可见的包装元素
    await row.locator('.el-checkbox').click();
    await expect(row.getByRole('checkbox')).toBeChecked();
    await page.getByRole('button', { name: '删除' }).click();
    await page.getByRole('dialog').getByRole('button', { name: /确\s*定/ }).click();
    await expect(page.getByText('删除成功')).toBeVisible();
    await expect(page.getByRole('row').filter({ hasText: code })).toHaveCount(0);
  });
});
