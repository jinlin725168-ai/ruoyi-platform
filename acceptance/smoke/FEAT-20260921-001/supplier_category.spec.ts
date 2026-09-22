// FEAT-20260921-001 供应商分类：前端核心流程冒烟（A8 A12 A15 A20 A39 A40 A43 A44 A48 A52 A56 A59）。
// 登录、菜单、查询区、表格和弹窗的定位器与文案沿用 acceptance/ui/supplier-management 的已验证计划和用例。
// 测试数据经后端接口准备，分类字段名不绑定实现（候选别名）。接口要求分类必填，无法产生分类为空的历史供应商，
// 因此经冒烟执行器使用的 MySQL 容器（ruoyi-mysql）把刚新增的供应商的分类列置空来模拟历史数据。
// 准备数据时，雪花 ID 生成器偶发的 Clock moved backwards 属于环境时钟抖动，稍等后重试。
import { expect, test, type Locator, type Page } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { statSync } from 'node:fs';

const API = (process.env.SMOKE_BASE_URL || '').trim();
const CLIENT_ID = process.env.SMOKE_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';
const BASE = '/biz/supplier';
const DICT_NAME = '供应商分类';
const UNCATEGORIZED = '未分类';
const CATEGORY_ALIASES = [
  'supplierCategory', 'category', 'supplierType', 'categoryCode', 'supplierCategoryCode',
  'categoryValue', 'supplierClass', 'supplierClassify', 'classify'
];
const BASE_COLUMNS = new Set([
  'supplier_id', 'supplier_code', 'supplier_name', 'contact_name', 'contact_phone', 'status', 'remark',
  'del_flag', 'create_dept', 'create_by', 'create_time', 'update_by', 'update_time', 'tenant_id'
]);
const MYSQL = ['exec', '-i', 'ruoyi-mysql', 'mysql', '--default-character-set=utf8mb4', '-uroot', '-proot', '-N', '-B'];

type Backend = { token: string; dictType: string; values: Record<string, string> };
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
  return payload?.rows ?? payload?.data?.rows ?? [];
}

async function dictItems(token: string, dictType: string): Promise<any[]> {
  const query = new URLSearchParams({ dictType, pageNum: '1', pageSize: '200' });
  return rowsOf(await api('GET', `/system/dict/data/list?${query}`, token));
}

async function discover(): Promise<Backend> {
  expect(API, 'SMOKE_BASE_URL 未设置').not.toBe('');
  const login = await api('POST', '/auth/login', undefined, {
    clientId: CLIENT_ID, grantType: 'password', tenantId: '000000', username: 'admin', password: 'admin123'
  });
  expect(login.code, JSON.stringify(login)).toBe(200);
  const token: string = login.data.access_token;
  const query = new URLSearchParams({ dictName: DICT_NAME, pageNum: '1', pageSize: '50' });
  const types = rowsOf(await api('GET', `/system/dict/type/list?${query}`, token));
  const dictType: string = types.find((t) => t.dictName === DICT_NAME)?.dictType;
  expect(dictType, `缺少『${DICT_NAME}』字典`).toBeTruthy();
  const values: Record<string, string> = {};
  for (const item of await dictItems(token, dictType)) values[item.dictLabel] ??= item.dictValue;
  for (const label of ['原材料', '服务', '设备']) expect(values[label], `字典缺少 ${label}`).toBeTruthy();
  return { token, dictType, values };
}

function ctx(): Promise<Backend> {
  backend ??= discover();
  return backend;
}

async function createSupplier(code: string, name: string, category: string): Promise<void> {
  const { token } = await ctx();
  const body: Record<string, string> = { supplierCode: code, supplierName: name, contactName: '界面联系人', status: '0' };
  for (const alias of CATEGORY_ALIASES) body[alias] = category;
  const result = await post(BASE, token, body);
  expect(result.code, JSON.stringify(result)).toBe(200);
}

async function createWithLabel(code: string, name: string, label: string): Promise<void> {
  const { values } = await ctx();
  await createSupplier(code, name, values[label]);
}

function mysql(statement: string, database?: string): string[][] {
  const out = execFileSync('docker', [...MYSQL, ...(database ? [database] : []), '-e', statement], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe']
  });
  return out.split('\n').filter(Boolean).map((line) => line.split('\t'));
}

function clearCategory(code: string): void {
  const schemas = mysql("select table_schema from information_schema.tables where table_name = 'biz_supplier' and table_schema like 'ry_smoke_%'").map((r) => r[0]);
  const database = schemas.find((s) => mysql(`select count(*) from biz_supplier where supplier_code = '${code}'`, s)[0]?.[0] === '1');
  expect(database, `冒烟数据库中找不到编码为 ${code} 的供应商`).toBeTruthy();
  const columns = mysql(`select column_name from information_schema.columns where table_schema = '${database}' and table_name = 'biz_supplier'`, database)
    .map((r) => r[0].toLowerCase()).filter((c) => !BASE_COLUMNS.has(c));
  const column = ['categ', 'class', 'type'].map((w) => columns.find((c) => c.includes(w))).find(Boolean)
    ?? (columns.length === 1 ? columns[0] : undefined);
  expect(column, `biz_supplier 中找不到分类列: ${columns.join(',')}`).toBeTruthy();
  try {
    mysql(`update biz_supplier set \`${column}\` = null where supplier_code = '${code}'`, database);
  } catch {
    mysql(`update biz_supplier set \`${column}\` = '' where supplier_code = '${code}'`, database);
  }
}

async function createHistorical(code: string, name: string): Promise<void> {
  await createWithLabel(code, name, '原材料');
  clearCategory(code);
}

async function createWithDeletedCategory(code: string, name: string): Promise<void> {
  const { token, dictType } = await ctx();
  const t = uid();
  const value = `smk${t}`;
  const added = await post('/system/dict/data', token, {
    dictType, dictLabel: `临时分类${t}`, dictValue: value, dictSort: 99, listClass: 'default', isDefault: 'N'
  });
  expect(added.code, JSON.stringify(added)).toBe(200);
  const item = (await dictItems(token, dictType)).find((i) => i.dictValue === value);
  expect(item, '新增的临时分类查询不到').toBeTruthy();
  await createSupplier(code, name, value);
  const removed = await api('DELETE', `/system/dict/data/${item.dictCode}`, token);
  expect(removed.code, JSON.stringify(removed)).toBe(200);
}

async function openSupplierPage(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByRole('textbox', { name: '用户名' }).fill('admin');
  await page.getByRole('textbox', { name: '密码' }).fill('admin123');
  await page.getByRole('button', { name: '登 录' }).click();
  await expect(page).toHaveURL(/\/index$/, { timeout: 30_000 });
  await page.getByRole('menuitem', { name: '业务管理' }).click();
  await page.getByRole('link', { name: '供应商管理' }).click();
  await expect(page).toHaveURL(/\/biz\/supplier$/);
  await expect(page.getByRole('heading', { name: '供应商列表' })).toBeVisible({ timeout: 30_000 });
}

function tableRows(page: Page): Locator {
  return page.locator('.el-table__body tr.el-table__row');
}

async function pickOption(page: Page, select: Locator, label: string): Promise<void> {
  await select.click();
  await page.locator('.el-select-dropdown__item:visible').getByText(label, { exact: true }).first().click();
}

async function search(page: Page, opts: { name?: string; category?: string }): Promise<void> {
  const form = page.locator('form.el-form--inline').first();
  await form.getByPlaceholder('请输入供应商名称').fill(opts.name ?? '');
  if (opts.category) {
    await pickOption(page, form.locator('.el-form-item').filter({ hasText: '分类' }).locator('.el-select').first(), opts.category);
  }
  await Promise.all([
    page.waitForResponse((r) => r.url().includes(`${BASE}/list`)),
    form.getByRole('button', { name: '搜索' }).click()
  ]);
  // Element Plus 的遮罩过渡期间可能同时存在两个遮罩元素，只等可见的遮罩全部消失
  await expect(page.locator('.el-table .el-loading-mask:visible')).toHaveCount(0, { timeout: 15_000 });
}

async function categoryColumn(page: Page): Promise<number> {
  const headers = (await page.locator('.el-table__header-wrapper th').allInnerTexts()).map((t) => t.trim());
  const index = headers.findIndex((t) => t.includes('分类'));
  expect(index, `表头没有分类列: ${headers.join(' | ')}`).toBeGreaterThanOrEqual(0);
  return index;
}

async function categoryCellOf(page: Page, name: string): Promise<Locator> {
  const row = tableRows(page).filter({ hasText: name });
  await expect(row).toHaveCount(1);
  return row.first().locator('td').nth(await categoryColumn(page));
}

async function expectEveryCategory(page: Page, label: string): Promise<void> {
  const cells = tableRows(page).locator(`td:nth-child(${(await categoryColumn(page)) + 1})`);
  await expect(cells.first()).toBeVisible();
  const count = await cells.count();
  await expect(cells).toHaveText(Array(count).fill(label));
}

function dialogItem(dialog: Locator, label: string): Locator {
  return dialog.locator('.el-form-item').filter({ hasText: label });
}

async function openAddDialog(page: Page): Promise<Locator> {
  await page.getByRole('button', { name: '新增' }).first().click();
  const dialog = page.locator('.el-dialog:visible');
  await expect(dialog).toBeVisible();
  return dialog;
}

async function openEditDialog(page: Page, name: string): Promise<Locator> {
  const row = tableRows(page).filter({ hasText: name });
  await expect(row).toHaveCount(1);
  await row.first().locator('.el-checkbox').first().click();
  await page.getByRole('button', { name: '修改' }).first().click();
  const dialog = page.locator('.el-dialog:visible');
  await expect(dialog).toBeVisible();
  await expect(dialogItem(dialog, '供应商名称').locator('input')).toHaveValue(name);
  return dialog;
}

async function confirmSaved(page: Page, dialog: Locator): Promise<void> {
  await dialog.getByRole('button', { name: '确 定' }).click();
  await expect(page.locator('.el-message--success').filter({ hasText: '操作成功' }).first()).toBeVisible();
  await expect(dialog).toBeHidden();
}

test('A8 按名称搜索只显示符合条件的供应商并显示分页', async ({ page }) => {
  const t = uid();
  const hit = `分类搜索命中${t}`;
  await createWithLabel(`GA${t}`, hit, '服务');
  await createWithLabel(`GB${t}`, `分类搜索未中${t}`, '服务');
  await openSupplierPage(page);
  await search(page, { name: hit });
  await expect(tableRows(page)).toHaveCount(1);
  await expect(tableRows(page).first()).toContainText(hit);
  await expect(page.locator('.el-pagination').first()).toBeVisible();
});

test('A12 新增选择了分类的供应商后列表显示所选分类', async ({ page }) => {
  await ctx();
  const t = uid();
  const name = `界面新增分类${t}`;
  await openSupplierPage(page);
  const dialog = await openAddDialog(page);
  await dialogItem(dialog, '供应商编码').locator('input').fill(`GC${t}`);
  await dialogItem(dialog, '供应商名称').locator('input').fill(name);
  await dialogItem(dialog, '联系人').locator('input').fill('界面联系人');
  await dialogItem(dialog, '联系电话').locator('input').fill('13900000000');
  await pickOption(page, dialogItem(dialog, '分类').locator('.el-select').first(), '设备');
  await confirmSaved(page, dialog);
  await search(page, { name });
  await expect(await categoryCellOf(page, name)).toHaveText('设备');
});

test('A39 新增表单的分类可选项包含原材料、服务、设备', async ({ page }) => {
  await ctx();
  await openSupplierPage(page);
  const dialog = await openAddDialog(page);
  await dialogItem(dialog, '分类').locator('.el-select').first().click();
  const options = page.locator('.el-select-dropdown__item:visible');
  for (const label of ['原材料', '服务', '设备']) {
    await expect(options.getByText(label, { exact: true })).toHaveCount(1);
  }
});

test('A40 未选择分类时表单不提交并提示分类必填', async ({ page }) => {
  await ctx();
  const t = uid();
  let posted = false;
  page.on('request', (r) => {
    if (r.method() === 'POST' && new URL(r.url()).pathname.endsWith(BASE)) posted = true;
  });
  await openSupplierPage(page);
  const dialog = await openAddDialog(page);
  await dialogItem(dialog, '供应商编码').locator('input').fill(`GN${t}`);
  await dialogItem(dialog, '供应商名称').locator('input').fill(`未选分类${t}`);
  await dialog.getByRole('button', { name: '确 定' }).click();
  await expect(dialogItem(dialog, '分类').locator('.el-form-item__error')).toBeVisible();
  await page.waitForTimeout(1_000);
  await expect(dialog).toBeVisible();
  expect(posted, '未选分类却发出了新增请求').toBe(false);
});

test('A43 按分类服务搜索时每一行分类都显示服务', async ({ page }) => {
  const t = uid();
  const name = `按分类服务${t}`;
  await createWithLabel(`GS${t}`, name, '服务');
  await openSupplierPage(page);
  await search(page, { category: '服务' });
  await expectEveryCategory(page, '服务');
  await search(page, { name, category: '服务' });
  await expect(await categoryCellOf(page, name)).toHaveText('服务');
});

test('A44 分类为空的历史供应商在分类列显示未分类', async ({ page }) => {
  const t = uid();
  const name = `历史供应商${t}`;
  await createHistorical(`GH${t}`, name);
  await openSupplierPage(page);
  await search(page, { name });
  await expect(await categoryCellOf(page, name)).toHaveText(UNCATEGORIZED);
});

test('A52 按未分类搜索时每一行都显示未分类且包含历史供应商', async ({ page }) => {
  const t = uid();
  const name = `历史未分类${t}`;
  await createHistorical(`GU${t}`, name);
  await openSupplierPage(page);
  await search(page, { category: UNCATEGORIZED });
  await expectEveryCategory(page, UNCATEGORIZED);
  await search(page, { name, category: UNCATEGORIZED });
  await expect(await categoryCellOf(page, name)).toHaveText(UNCATEGORIZED);
});

test('A56 分类值已从字典删除的供应商在分类列显示未分类', async ({ page }) => {
  const t = uid();
  const name = `已删分类${t}`;
  await createWithDeletedCategory(`GD${t}`, name);
  await openSupplierPage(page);
  await search(page, { name });
  await expect(await categoryCellOf(page, name)).toHaveText(UNCATEGORIZED);
});

test('A59 按名称和未分类搜索能找到分类值已删除的供应商', async ({ page }) => {
  const t = uid();
  const name = `已删分类筛选${t}`;
  await createWithDeletedCategory(`GE${t}`, name);
  await openSupplierPage(page);
  await search(page, { name, category: UNCATEGORIZED });
  await expect(await categoryCellOf(page, name)).toHaveText(UNCATEGORIZED);
});

test('A15 修改分类有效的供应商名称后列表显示新名称', async ({ page }) => {
  const t = uid();
  const oldName = `待修改分类${t}`;
  const newName = `已修改分类${t}`;
  await createWithLabel(`GM${t}`, oldName, '服务');
  await openSupplierPage(page);
  await search(page, { name: oldName });
  const dialog = await openEditDialog(page, oldName);
  await dialogItem(dialog, '供应商名称').locator('input').fill(newName);
  await confirmSaved(page, dialog);
  await search(page, { name: newName });
  await expect(tableRows(page).filter({ hasText: newName })).toHaveCount(1);
});

test('A48 给未分类的历史供应商选择原材料后分类列显示原材料', async ({ page }) => {
  const t = uid();
  const name = `历史补分类${t}`;
  await createHistorical(`GR${t}`, name);
  await openSupplierPage(page);
  await search(page, { name });
  await expect(await categoryCellOf(page, name)).toHaveText(UNCATEGORIZED);
  const dialog = await openEditDialog(page, name);
  await pickOption(page, dialogItem(dialog, '分类').locator('.el-select').first(), '原材料');
  await confirmSaved(page, dialog);
  await search(page, { name });
  await expect(await categoryCellOf(page, name)).toHaveText('原材料');
});

test('A20 点击导出下载 Excel 文件', async ({ page }) => {
  const t = uid();
  await createWithLabel(`GX${t}`, `分类导出${t}`, '设备');
  await openSupplierPage(page);
  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 60_000 }),
    page.getByRole('button', { name: '导出' }).first().click()
  ]);
  expect(download.suggestedFilename()).toMatch(/[.]xlsx?$/i);
  expect(await download.failure()).toBeNull();
  expect(statSync(await download.path()).size).toBeGreaterThan(0);
});
