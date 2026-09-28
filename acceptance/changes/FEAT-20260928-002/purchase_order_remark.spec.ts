// FEAT-20260928-002 采购单备注：前端核心流程冒烟（A106 A111 A112）。
// 登录、菜单进入、查询区占位符和表格结构沿用已验收的采购单管理页面用例（acceptance/changes/FEAT-20260924-002、
// acceptance/smoke/FEAT-20260920-001）；弹窗表单项按标签文字定位，行内图标按钮按 tooltip 文字定位。
// 测试数据经后端接口准备（fetch 带 clientid 头），雪花 ID 偶发的 Clock moved backwards 稍等后重试。
import { expect, test, type Locator, type Page } from '@playwright/test';

const API = (process.env.SMOKE_BASE_URL || '').trim();
const CLIENT_ID = process.env.SMOKE_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';
const ORDER_BASE = '/biz/purchaseOrder';
const SUPPLIER_BASE = '/biz/supplier';
const CATEGORY_DICT = 'biz_supplier_category';

type Ctx = { token: string; category: string };
let ctxPromise: Promise<Ctx> | undefined;

function uid(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function todayStr(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

async function api(method: string, path: string, token?: string, body?: unknown): Promise<any> {
  const headers: Record<string, string> = { Accept: 'application/json', clientid: CLIENT_ID };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const res = await fetch(new URL(path, API), { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    return { code: res.status, msg: text.slice(0, 300) };
  }
}

async function post(path: string, token: string, body: unknown): Promise<any> {
  for (let attempt = 0; ; attempt++) {
    const result = await api('POST', path, token, body);
    if (attempt < 5 && result.code !== 200 && String(result.msg ?? '').includes('Clock moved backwards')) {
      await new Promise((resolve) => setTimeout(resolve, 1_000));
      continue;
    }
    return result;
  }
}

function dataRows(payload: any): any[] {
  return payload?.data?.rows ?? payload?.rows ?? [];
}

async function discover(): Promise<Ctx> {
  expect(API, 'SMOKE_BASE_URL 未设置').not.toBe('');
  const login = await api('POST', '/auth/login', undefined, {
    clientId: CLIENT_ID, grantType: 'password', tenantId: '000000', username: 'admin', password: 'admin123'
  });
  expect(login.code, JSON.stringify(login)).toBe(200);
  const token: string = login.data.access_token;
  const query = new URLSearchParams({ dictType: CATEGORY_DICT, pageNum: '1', pageSize: '200' });
  const values: Record<string, string> = {};
  for (const item of dataRows(await api('GET', `/system/dict/data/list?${query}`, token))) values[item.dictLabel] ??= item.dictValue;
  const category = values['原材料'] ?? Object.values(values)[0];
  expect(category, '供应商分类字典为空').toBeTruthy();
  return { token, category };
}

function ctx(): Promise<Ctx> {
  ctxPromise ??= discover();
  return ctxPromise;
}

async function createSupplier(name: string): Promise<string> {
  const { token, category } = await ctx();
  const code = `RU${uid()}`;
  const created = await post(SUPPLIER_BASE, token, {
    supplierCode: code, supplierName: name, supplierCategory: category, status: '0'
  });
  expect(created.code, `准备供应商失败: ${JSON.stringify(created)}`).toBe(200);
  const query = new URLSearchParams({ supplierName: name, pageNum: '1', pageSize: '50' });
  const row = dataRows(await api('GET', `${SUPPLIER_BASE}/list?${query}`, token)).find((r: any) => r.supplierCode === code);
  expect(row, `新建的供应商 ${name} 查询不到`).toBeTruthy();
  return String(row.supplierId);
}

/** 为新供应商准备一张带备注的草稿单，返回单号 */
async function createOrder(supplierName: string, remark: string): Promise<string> {
  const supplierId = await createSupplier(supplierName);
  const { token } = await ctx();
  const created = await post(ORDER_BASE, token, {
    supplierId, orderDate: todayStr(), remark, details: [{ materialName: `物料${uid()}`, quantity: 1, price: 10 }]
  });
  expect(created.code, `准备采购单失败: ${JSON.stringify(created)}`).toBe(200);
  const query = new URLSearchParams({ supplierName, pageNum: '1', pageSize: '200' });
  const rows = dataRows(await api('GET', `${ORDER_BASE}/list?${query}`, token));
  expect(rows.length, `供应商 ${supplierName} 的采购单数量不为 1`).toBe(1);
  return String(rows[0].orderNo);
}

async function openOrderPage(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByRole('textbox', { name: '用户名' }).fill('admin');
  await page.getByRole('textbox', { name: '密码' }).fill('admin123');
  await page.getByRole('button', { name: '登 录' }).click();
  await expect(page).toHaveURL(/index$/, { timeout: 30_000 });
  await page.getByRole('menuitem', { name: '业务管理' }).click();
  await page.getByRole('link', { name: '采购单管理' }).click();
  await expect(page.getByRole('heading', { name: '采购单列表' })).toBeVisible({ timeout: 30_000 });
  await expect(page.locator('.el-table .el-loading-mask:visible')).toHaveCount(0, { timeout: 15_000 });
}

/** 列表页的主表格：弹窗挂在 body 末尾，主表格总是第一个 */
function mainTable(page: Page): Locator {
  return page.locator('.el-table').first();
}

function bodyRows(table: Locator): Locator {
  return table.locator('.el-table__body tr.el-table__row');
}

async function headerIndex(table: Locator, label: string): Promise<number> {
  const headers = (await table.locator('.el-table__header-wrapper th').allInnerTexts()).map((t) => t.trim());
  const index = headers.findIndex((t) => t.includes(label));
  expect(index, `表头缺少“${label}”列: ${headers.join(' | ')}`).toBeGreaterThanOrEqual(0);
  return index;
}

async function search(page: Page, opts: { orderNo?: string; supplier?: string }): Promise<void> {
  const form = page.locator('form.el-form--inline').first();
  if (opts.orderNo !== undefined) await form.getByPlaceholder('请输入采购单号').fill(opts.orderNo);
  if (opts.supplier !== undefined) await form.getByPlaceholder('请输入供应商名称').fill(opts.supplier);
  await Promise.all([
    page.waitForResponse((r) => r.url().includes(`${ORDER_BASE}/list`)),
    form.getByRole('button', { name: '搜索' }).click()
  ]);
  await expect(page.locator('.el-table .el-loading-mask:visible')).toHaveCount(0, { timeout: 15_000 });
}

function dialogItem(dialog: Locator, label: string): Locator {
  return dialog.locator('.el-form-item').filter({ hasText: label }).first();
}

// 行内操作按钮是生成器风格的“图标按钮 + tooltip”，也兼容带文字的按钮。
async function findRowAction(page: Page, row: Locator, label: string): Promise<Locator | null> {
  const named = row.getByRole('button', { name: label });
  if (await named.count()) return named.first();
  const buttons = row.locator('button');
  const total = await buttons.count();
  for (let i = 0; i < total; i += 1) {
    const button = buttons.nth(i);
    if (await button.isDisabled()) continue;
    await button.hover();
    try {
      await page.getByRole('tooltip').filter({ hasText: label }).first().waitFor({ state: 'visible', timeout: 1_500 });
    } catch {
      continue;
    }
    return button;
  }
  return null;
}

test('A106 新增表单填写备注保存后列表该行显示所填备注', async ({ page }) => {
  const name = `备注新增${uid()}`;
  await createSupplier(name);
  const remark = `界面备注${uid()}，请于月底前送达`;
  await openOrderPage(page);
  await page.getByRole('button', { name: '新增' }).first().click();
  const dialog = page.locator('.el-dialog:visible');
  await expect(dialog).toBeVisible();

  const supplierItem = dialogItem(dialog, '供应商');
  const keyword = supplierItem.getByPlaceholder('供应商名称');
  if (await keyword.count()) await keyword.fill(name);
  await supplierItem.locator('.el-select').first().click();
  const option = page.locator('.el-select-dropdown__item:visible').filter({ hasText: name }).first();
  await expect(option, `供应商下拉里没有 ${name}`).toBeVisible({ timeout: 15_000 });
  await option.click();

  const dateInput = dialogItem(dialog, '下单日期').locator('input').first();
  await dateInput.fill(todayStr());
  await dateInput.press('Enter');

  const remarkBox = dialogItem(dialog, '备注').locator('textarea, input').first();
  await expect(remarkBox, '新增表单缺少“备注”输入项').toBeVisible();
  await remarkBox.fill(remark);

  const detailTable = dialog.locator('.el-table').first();
  const detailRows = bodyRows(detailTable);
  if ((await detailRows.count()) === 0) await dialog.getByRole('button', { name: /添加/ }).first().click();
  await expect(detailRows).toHaveCount(1);
  const fill = async (label: string, value: string) => {
    const input = detailRows.first().locator('td').nth(await headerIndex(detailTable, label)).locator('input, textarea').first();
    await expect(input, `明细行“${label}”列没有输入框`).toBeVisible();
    await input.fill(value);
  };
  await fill('物料', `备注物料${uid()}`);
  await fill('数量', '2');
  await fill('单价', '10');

  await dialog.getByRole('button', { name: /确 ?定/ }).click();
  await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 20_000 });
  await expect(dialog).toBeHidden();

  await search(page, { supplier: name });
  const rows = bodyRows(mainTable(page));
  await expect(rows).toHaveCount(1);
  await expect(rows.first().locator('td').nth(await headerIndex(mainTable(page), '备注'))).toHaveText(remark);
});

test('A111 按单号查询时表格有备注列并在该行显示备注', async ({ page }) => {
  const remark = `列表界面备注${uid()}`;
  const orderNo = await createOrder(`备注列表${uid()}`, remark);
  await openOrderPage(page);
  await search(page, { orderNo });
  const rows = bodyRows(mainTable(page));
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText(orderNo);
  await expect(rows.first().locator('td').nth(await headerIndex(mainTable(page), '备注'))).toHaveText(remark);
});

test('A112 采购单详情中显示备注', async ({ page }) => {
  const remark = `详情界面备注${uid()}`;
  const orderNo = await createOrder(`备注详情${uid()}`, remark);
  await openOrderPage(page);
  await search(page, { orderNo });
  const rows = bodyRows(mainTable(page));
  await expect(rows).toHaveCount(1);
  const view = await findRowAction(page, rows.first(), '详情');
  expect(view, '行内没有“详情”按钮').not.toBeNull();
  await view!.click();
  const detail = page.locator('.el-dialog:visible').filter({ hasText: '采购单详情' });
  await expect(detail).toBeVisible();
  await expect(detail).toContainText(orderNo);
  const label = detail.locator('.el-descriptions__label').filter({ hasText: '备注' }).first();
  await expect(label, '详情中没有“备注”项').toBeVisible();
  await expect(label.locator('xpath=following-sibling::*[1]')).toHaveText(remark);
});
