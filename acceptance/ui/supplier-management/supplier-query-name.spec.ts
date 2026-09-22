// spec: specs/plan.md
// seed: tests/seed.spec.ts
// NOTE: written from the plan's documented page structure; the app was unreachable during generation, so this has not been run yet.

import { test, expect } from '@playwright/test';

test.describe('S1 业务管理目录与供应商管理菜单', () => {
  test('按供应商名称查询', async ({ page }) => {
    const ts = `AUTO_${Date.now()}`;
    const suppliers = [
      { code: `Q_${ts}_1`, name: `查询甲${ts}` },
      { code: `Q_${ts}_2`, name: `查询乙${ts}` },
    ];
    // 搜索框在页面前部；弹窗打开过后会留在 DOM 末尾，所以取 first()
    const searchName = page.getByPlaceholder('请输入供应商名称').first();
    const searchButton = page.getByRole('button', { name: '搜索' });
    const bodyRows = page.locator('.el-table__body-wrapper tbody tr');

    // 1. 登录后进入供应商管理，新增 2 条数据
    await page.goto('/login');
    await page.getByRole('textbox', { name: '用户名' }).fill('admin');
    await page.getByRole('textbox', { name: '密码' }).fill('admin123');
    await page.getByRole('button', { name: '登 录' }).click();
    await expect(page).toHaveURL(/\/index/);

    await page.goto('/biz/supplier');
    await expect(page.getByText('供应商列表')).toBeVisible();

    for (const s of suppliers) {
      await page.getByRole('button', { name: '新增' }).click();
      const dialog = page.getByRole('dialog', { name: '添加供应商' });
      await expect(dialog).toBeVisible();
      await dialog.getByPlaceholder('请输入供应商编码').fill(s.code);
      await dialog.getByPlaceholder('请输入供应商名称').fill(s.name);
      // 供应商分类为必填项，选择字典中的第一个分类
      await dialog.locator('.el-form-item').filter({ hasText: '供应商分类' }).locator('.el-select__wrapper').click();
      await page.locator('.el-select-dropdown__item:visible').first().click();
      await dialog.getByRole('button', { name: '确 定' }).click();
      await expect(page.getByText('操作成功').last()).toBeVisible();
      await expect(dialog).toBeHidden();
    }

    // 2. 在「供应商名称」框输入「查询甲<ts>」，点击「搜索」
    await searchName.fill(suppliers[0].name);
    await searchButton.click();
    await expect(bodyRows).toHaveCount(1);
    await expect(bodyRows.first()).toContainText(suppliers[0].name);
    await expect(page.getByText('共 1 条', { exact: true })).toBeVisible();

    // 3. 输入部分关键字「<ts>」后搜索
    await searchName.fill(ts);
    await searchButton.click();
    await expect(bodyRows).toHaveCount(2);
    await expect(bodyRows.filter({ hasText: suppliers[0].name })).toHaveCount(1);
    await expect(bodyRows.filter({ hasText: suppliers[1].name })).toHaveCount(1);
    await expect(page.getByText('共 2 条', { exact: true })).toBeVisible();

    // 4. 输入不存在的名称「不存在_<ts>」后搜索
    await searchName.fill(`不存在_${ts}`);
    await searchButton.click();
    await expect(page.getByText('暂无数据')).toBeVisible();
    await expect(bodyRows).toHaveCount(0);
    // total 为 0 时分页组件被 v-show 隐藏，改为校验列表标题中的总数
    await expect(page.getByText(/^共 0 条记录/)).toBeVisible();

    // 清理：删除本场景创建的 2 条数据
    await searchName.fill(ts);
    await searchButton.click();
    await expect(bodyRows).toHaveCount(2);
    for (const s of suppliers) {
      // el-checkbox 的原生 input 被隐藏，点击可见的包装元素
      const row = bodyRows.filter({ hasText: s.code });
      await row.locator('.el-checkbox').click();
      await expect(row.getByRole('checkbox')).toBeChecked();
    }
    await page.getByRole('button', { name: '删除' }).click();
    await page.getByRole('dialog').getByRole('button', { name: /确\s*定/ }).click();
    await expect(page.getByText('删除成功')).toBeVisible();
    await expect(bodyRows).toHaveCount(0);
  });
});
