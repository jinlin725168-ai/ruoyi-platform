// 系统冒烟：采购单管理页面按单号查询、按供应商分类筛选（来自 FEAT-20260923-001 的核心界面流程）。
// 登录与菜单的定位器沿用 acceptance/ui/supplier-management 已验证的写法；查询区占位符与表格结构沿用已验收的
// 采购单管理页面。测试数据经后端接口准备（fetch 带 clientid 头），雪花 ID 偶发的 Clock moved backwards 稍等后重试。
import { expect, test, type Locator, type Page } from '@playwright/test';

const API = (process.env.SMOKE_BASE_URL || '').trim();
const CLIENT_ID = process.env.SMOKE_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';
const ORDER_BASE = '/biz/purchaseOrder';
const SUPPLIER_BASE = '/biz/supplier';
const CATEGORY_DICT = 'biz_supplier_category';

type Ctx = { token: string; values: Record<string, string> };
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

function rowsOf(payload: any): any[] {
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
  for (const item of rowsOf(await api('GET', `/system/dict/data/list?${query}`, token))) values[item.dictLabel] ??= item.dictValue;
  for (const label of ['原材料', '服务', '设备']) expect(values[label], `供应商分类字典缺少 ${label}`).toBeTruthy();
  return { token, values };
}

function ctx(): Promise<Ctx> {
  ctxPromise ??= discover();
  return ctxPromise;
}

async function createSupplier(name: string, label: string): Promise<string> {
  const { token, values } = await ctx();
  const code = `UC${uid()}`;
  const created = await post(SUPPLIER_BASE, token, {
    supplierCode: code, supplierName: name, supplierCategory: values[label], status: '0'
  });
  expect(created.code, `准备供应商失败: ${JSON.stringify(created)}`).toBe(200);
  const query = new URLSearchParams({ supplierName: name, pageNum: '1', pageSize: '50' });
  const row = rowsOf(await api('GET', `${SUPPLIER_BASE}/list?${query}`, token)).find((r: any) => r.supplierCode === code);
  expect(row, `新建的供应商 ${name} 查询不到`).toBeTruthy();
  return String(row.supplierId);
}

async function createOrder(supplierId: string, supplierName: string): Promise<string> {
  const { token } = await ctx();
  const remark = `分类界面${uid()}`;
  const created = await post(ORDER_BASE, token, {
    supplierId, orderDate: todayStr(), remark, details: [{ materialName: `物料${uid()}`, quantity: 1, price: 10 }]
  });
  expect(created.code, `准备采购单失败: ${JSON.stringify(created)}`).toBe(200);
  const query = new URLSearchParams({ supplierName, pageNum: '1', pageSize: '200' });
  const row = rowsOf(await api('GET', `${ORDER_BASE}/list?${query}`, token)).find((r: any) => r.remark === remark);
  expect(row, `备注为 ${remark} 的采购单查询不到`).toBeTruthy();
  return String(row.orderNo);
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

function tableRows(page: Page): Locator {
  return page.locator('.el-table__body tr.el-table__row');
}

async function search(page: Page, opts: { orderNo?: string; supplier?: string; category?: string }): Promise<void> {
  const form = page.locator('form.el-form--inline').first();
  if (opts.orderNo !== undefined) await form.getByPlaceholder('请输入采购单号').fill(opts.orderNo);
  if (opts.supplier !== undefined) await form.getByPlaceholder('请输入供应商名称').fill(opts.supplier);
  if (opts.category) {
    const item = form.locator('.el-form-item').filter({ hasText: '分类' }).first();
    await expect(item, '查询区缺少“供应商分类”筛选项').toBeVisible();
    await item.locator('.el-select').first().click();
    await page.locator('.el-select-dropdown__item:visible').getByText(opts.category, { exact: true }).first().click();
  }
  await Promise.all([
    page.waitForResponse((r) => r.url().includes(`${ORDER_BASE}/list`)),
    form.getByRole('button', { name: '搜索' }).click()
  ]);
  await expect(page.locator('.el-table .el-loading-mask:visible')).toHaveCount(0, { timeout: 15_000 });
}

async function columnIndex(page: Page, label: string): Promise<number> {
  const headers = (await page.locator('.el-table__header-wrapper th').allInnerTexts()).map((t) => t.trim());
  const index = headers.findIndex((t) => t.includes(label));
  expect(index, `表头缺少“${label}”列: ${headers.join(' | ')}`).toBeGreaterThanOrEqual(0);
  return index;
}

async function expectEveryCategory(page: Page, label: string): Promise<void> {
  const cells = tableRows(page).locator(`td:nth-child(${(await columnIndex(page, '供应商分类')) + 1})`);
  await expect(cells.first()).toBeVisible();
  const count = await cells.count();
  await expect(cells).toHaveText(Array(count).fill(label));
}

test('按单号查询只展示匹配的单据并带供应商分类等核心列', async ({ page }) => {
  const name = `分类单号${uid()}`;
  const supplierId = await createSupplier(name, '服务');
  const wanted = await createOrder(supplierId, name);
  const other = await createOrder(supplierId, name);
  await openOrderPage(page);
  await search(page, { orderNo: wanted });
  const rows = tableRows(page);
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText(wanted);
  await expect(rows.first()).not.toContainText(other);
  for (const label of ['单号', '供应商', '供应商分类', '下单日期', '状态', '合计金额']) {
    await columnIndex(page, label);
  }
  await expect(rows.first().locator('td').nth(await columnIndex(page, '供应商分类'))).toHaveText('服务');
});

test('按供应商分类查询时表格只展示该分类的单据', async ({ page }) => {
  const token = `分类筛选${uid()}`;
  const serviceName = `${token}S`;
  const equipName = `${token}E`;
  const serviceOrder = await createOrder(await createSupplier(serviceName, '服务'), serviceName);
  const equipOrder = await createOrder(await createSupplier(equipName, '设备'), equipName);
  await openOrderPage(page);
  await search(page, { category: '服务' });
  await expectEveryCategory(page, '服务');
  await search(page, { supplier: token });
  const rows = tableRows(page);
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText(serviceOrder);
  await expect(rows.first()).not.toContainText(equipOrder);
  await expectEveryCategory(page, '服务');
});
