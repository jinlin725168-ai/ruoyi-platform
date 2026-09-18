// FEAT-20260918-001 供应商管理：前端核心流程冒烟（A2 A8 A12 A15 A18 A20）。
// 独立外部验收：接口前缀从『业务管理/供应商管理』菜单权限串推导，测试数据用候选字段别名经后端接口准备。
import { expect, test, type Locator, type Page } from '@playwright/test';
import { statSync } from 'node:fs';

const API = (process.env.SMOKE_BASE_URL || '').trim();
const CLIENT_ID = process.env.SMOKE_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';
const ALIASES: Record<string, string[]> = {
  code: ['supplierCode', 'code', 'supplierNo'],
  name: ['supplierName', 'name'],
  contact: ['contactName', 'contactPerson', 'contacts', 'contact', 'linkman', 'linkMan', 'contactUser'],
  phone: ['contactPhone', 'phone', 'telephone', 'contactTel', 'contactNumber', 'tel', 'mobile']
};

type Backend = { token: string; base: string };
let backend: Promise<Backend> | undefined;

function uid(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

async function api(method: string, path: string, token?: string, body?: unknown): Promise<any> {
  const headers: Record<string, string> = { Accept: 'application/json', clientid: CLIENT_ID };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const res = await fetch(new URL(path, API), { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  return res.json();
}

async function discover(): Promise<Backend> {
  expect(API, 'SMOKE_BASE_URL 未设置').not.toBe('');
  const login = await api('POST', '/auth/login', undefined, {
    clientId: CLIENT_ID, grantType: 'password', tenantId: '000000', username: 'admin', password: 'admin123'
  });
  expect(login.code, JSON.stringify(login)).toBe(200);
  const token: string = login.data.access_token;
  const menus: any[] = (await api('GET', '/system/menu/list', token)).data ?? [];
  const top = menus.find((m) => m.menuName === '业务管理' && String(m.parentId) === '0');
  expect(top, '缺少顶级目录『业务管理』').toBeTruthy();
  const menu = menus.find((m) => m.menuName === '供应商管理' && String(m.parentId) === String(top.menuId));
  expect(menu, '缺少『供应商管理』菜单').toBeTruthy();
  const perms = [menu, ...menus.filter((m) => String(m.parentId) === String(menu.menuId))].map((m) => String(m.perms ?? ''));
  const feature = perms.map((p) => p.split(':')).find((p) => p.length === 3 && p[0] === 'biz' && p[1])?.[1];
  expect(feature, '缺少 biz:<feature>:* 权限串').toBeTruthy();
  return { token, base: `/biz/${feature}` };
}

function backendCtx(): Promise<Backend> {
  backend ??= discover();
  return backend;
}

async function createSupplier(fields: Record<string, string>): Promise<void> {
  const { token, base } = await backendCtx();
  const body: Record<string, string> = {};
  for (const [logical, value] of Object.entries(fields)) {
    for (const alias of ALIASES[logical]) body[alias] = value;
  }
  const result = await api('POST', base, token, body);
  expect(result.code, JSON.stringify(result)).toBe(200);
}

async function openSupplierPage(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByPlaceholder(/用户名|username/i).fill('admin');
  await page.getByPlaceholder(/密码|password/i).fill('admin123');
  await page.locator('button.submit-button').click();
  await expect(page).toHaveURL(/index/, { timeout: 30_000 });
  const sidebar = page.locator('.sidebar-container');
  await sidebar.getByText('业务管理', { exact: true }).click();
  await sidebar.getByText('供应商管理', { exact: true }).click();
  await expect(page).not.toHaveURL(/index$/);
  await expect(page.locator('.el-table').first()).toBeVisible({ timeout: 30_000 });
}

function tableRows(page: Page): Locator {
  return page.locator('.el-table__body tr.el-table__row');
}

async function searchByName(page: Page, name: string): Promise<void> {
  const form = page.locator('form.el-form--inline').first();
  await form.locator('.el-form-item').filter({ hasText: '名称' }).locator('input').first().fill(name);
  await form.getByRole('button', { name: /搜 ?索/ }).click();
}

function dialogField(dialog: Locator, label: string): Locator {
  return dialog.locator('.el-form-item').filter({ hasText: label }).locator('input, textarea').first();
}

async function expectSuccess(page: Page): Promise<void> {
  await expect(page.locator('.el-message--success').filter({ hasText: '成功' }).first()).toBeVisible();
}

// 行内操作按钮可能是带文字的按钮，也可能是生成器风格的“图标按钮 + tooltip”。
async function clickRowAction(page: Page, row: Locator, label: string): Promise<void> {
  const named = row.getByRole('button', { name: label });
  if ((await named.count()) > 0) {
    await named.first().click();
    return;
  }
  const buttons = row.locator('button');
  const total = await buttons.count();
  for (let i = 0; i < total; i += 1) {
    const button = buttons.nth(i);
    await button.hover();
    try {
      await page.getByRole('tooltip').filter({ hasText: label }).first().waitFor({ state: 'visible', timeout: 2_000 });
    } catch {
      continue;
    }
    await button.click();
    return;
  }
  throw new Error(`行内没有"${label}"按钮`);
}

test('A2 展开业务管理后点击供应商管理打开供应商列表', async ({ page }) => {
  await backendCtx();
  await openSupplierPage(page);
  const header = page.locator('.el-table__header').first();
  await expect(header).toContainText('编码');
  await expect(header).toContainText('名称');
});

test('A8 按名称搜索只显示匹配的供应商并显示分页', async ({ page }) => {
  const t = uid();
  const hit = `搜索命中${t}`;
  await createSupplier({ code: `UA${t}`, name: hit });
  await createSupplier({ code: `UB${t}`, name: `搜索未中${t}` });
  await openSupplierPage(page);
  await searchByName(page, hit);
  await expect(tableRows(page)).toHaveCount(1);
  await expect(tableRows(page).first()).toContainText(hit);
  await expect(page.locator('.el-pagination').first()).toBeVisible();
});

test('A12 新增供应商后弹窗关闭、提示成功、列表出现新记录', async ({ page }) => {
  await backendCtx();
  const t = uid();
  const name = `界面新增${t}`;
  await openSupplierPage(page);
  await page.getByRole('button', { name: '新增' }).first().click();
  const dialog = page.locator('.el-dialog:visible');
  await expect(dialog).toBeVisible();
  await dialogField(dialog, '编码').fill(`UC${t}`);
  await dialogField(dialog, '名称').fill(name);
  await dialogField(dialog, '联系人').fill('界面联系人');
  await dialogField(dialog, '电话').fill('13900000000');
  await dialog.getByRole('button', { name: /确 ?定/ }).click();
  await expectSuccess(page);
  await expect(dialog).toBeHidden();
  await searchByName(page, name);
  await expect(tableRows(page).filter({ hasText: name })).toHaveCount(1);
});

test('A15 修改行内供应商名称后列表显示新名称', async ({ page }) => {
  const t = uid();
  const oldName = `待修改${t}`;
  const newName = `已修改${t}`;
  await createSupplier({ code: `UE${t}`, name: oldName });
  await openSupplierPage(page);
  await searchByName(page, oldName);
  const row = tableRows(page).filter({ hasText: oldName });
  await expect(row).toHaveCount(1);
  await clickRowAction(page, row.first(), '修改');
  const dialog = page.locator('.el-dialog:visible');
  const nameInput = dialogField(dialog, '名称');
  await expect(nameInput).toHaveValue(oldName);
  await nameInput.fill(newName);
  await dialog.getByRole('button', { name: /确 ?定/ }).click();
  await expectSuccess(page);
  await expect(dialog).toBeHidden();
  await searchByName(page, newName);
  await expect(tableRows(page).filter({ hasText: newName })).toHaveCount(1);
});

test('A18 确认删除后提示成功且供应商从列表消失', async ({ page }) => {
  const t = uid();
  const name = `待删除${t}`;
  await createSupplier({ code: `UD${t}`, name });
  await openSupplierPage(page);
  await searchByName(page, name);
  const row = tableRows(page).filter({ hasText: name });
  await expect(row).toHaveCount(1);
  await clickRowAction(page, row.first(), '删除');
  const box = page.locator('.el-message-box');
  await expect(box).toBeVisible();
  await box.locator('.el-message-box__btns .el-button--primary').click();
  await expectSuccess(page);
  await expect(tableRows(page).filter({ hasText: name })).toHaveCount(0);
});

test('A20 点击导出下载 Excel 文件', async ({ page }) => {
  const t = uid();
  await createSupplier({ code: `UX${t}`, name: `导出${t}` });
  await openSupplierPage(page);
  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 60_000 }),
    page.getByRole('button', { name: '导出' }).first().click()
  ]);
  expect(download.suggestedFilename()).toMatch(/[.]xlsx?$/i);
  expect(await download.failure()).toBeNull();
  expect(statSync(await download.path()).size).toBeGreaterThan(0);
});
