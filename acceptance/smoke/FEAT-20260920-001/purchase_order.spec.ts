// FEAT-20260920-001 采购单管理：前端核心流程冒烟（A4 A9 A10 A13 A14 A19 A23 A28 A31）。
// 独立外部验收：接口前缀与菜单从『业务管理/采购单管理』推导，测试数据用候选字段别名经后端接口准备。
import { expect, test, type Locator, type Page } from '@playwright/test';

const API = (process.env.SMOKE_BASE_URL || '').trim();
const CLIENT_ID = process.env.SMOKE_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';
const DIR_NAME = '业务管理';
const MENU_NAME = '采购单管理';
const SUPPLIER_MENU_NAME = '供应商管理';
const OTHER_DEPT_ID = '1761000000000000105';
const SUPPLIER_CODE_ALIASES = ['supplierCode', 'code', 'supplierNo'];
const SUPPLIER_NAME_ALIASES = ['supplierName', 'name'];
const MAIN_ALIASES: Record<string, string[]> = {
  supplierId: ['supplierId'],
  supplierName: ['supplierName'],
  orderDate: ['orderDate', 'purchaseDate', 'billDate', 'orderTime', 'orderDay'],
  remark: ['remark']
};
const DETAIL_LIST_KEYS = [
  'details', 'detailList', 'orderDetails', 'orderDetailList', 'purchaseOrderDetails',
  'purchaseOrderDetailList', 'items', 'itemList', 'orderItems', 'detailBoList', 'detailVoList',
  'lines', 'lineList', 'subList', 'children'
];
const DETAIL_ALIASES: Record<string, string[]> = {
  materialName: ['materialName', 'materialsName', 'itemName', 'goodsName', 'productName', 'material', 'name'],
  quantity: ['quantity', 'qty', 'num', 'number', 'count'],
  price: ['price', 'unitPrice', 'itemPrice']
};

type Ctx = { token: string; base: string; supplierBase: string; top: any; menu: any; buttons: any[] };
type Supplier = { id: string; name: string };
type Detail = { materialName: string; quantity: number; price: number };

let ctxPromise: Promise<Ctx> | undefined;
let dateSuffix = '';

function uid(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function todayStr(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function amountOf(text: string): number {
  const match = text.replace(/[,\s]/g, '').match(/-?\d+(\.\d+)?/);
  expect(match, `单元格里没有金额: ${text}`).toBeTruthy();
  return Number(match![0]);
}

async function api(method: string, path: string, token?: string, body?: unknown): Promise<any> {
  const headers: Record<string, string> = { Accept: 'application/json', clientid: CLIENT_ID };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const res = await fetch(new URL(path, API), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    return { code: res.status, msg: text.slice(0, 300) };
  }
}

function featureOf(menus: any[]): string | undefined {
  for (const menu of menus) {
    const parts = String(menu?.perms ?? '').split(':');
    if (parts.length === 3 && parts[0] === 'biz' && parts[1]) return parts[1];
  }
  return undefined;
}

async function discover(): Promise<Ctx> {
  expect(API, 'SMOKE_BASE_URL 未设置').not.toBe('');
  const login = await api('POST', '/auth/login', undefined, {
    clientId: CLIENT_ID, grantType: 'password', tenantId: '000000', username: 'admin', password: 'admin123'
  });
  expect(login.code, JSON.stringify(login)).toBe(200);
  const token: string = login.data.access_token;
  const menus: any[] = (await api('GET', '/system/menu/list', token)).data ?? [];
  const top = menus.find((m) => m.menuName === DIR_NAME && String(m.parentId) === '0');
  expect(top, `缺少顶级目录『${DIR_NAME}』`).toBeTruthy();
  const menu = menus.find((m) => m.menuName === MENU_NAME && String(m.parentId) === String(top.menuId));
  expect(menu, `『${DIR_NAME}』下缺少『${MENU_NAME}』菜单`).toBeTruthy();
  const buttons = menus.filter((m) => String(m.parentId) === String(menu.menuId));
  const feature = featureOf([menu, ...buttons]);
  expect(feature, '采购单管理菜单缺少 biz:<feature>:* 权限串').toBeTruthy();
  const supplierMenu = menus.find((m) => m.menuName === SUPPLIER_MENU_NAME);
  const supplierFeature = supplierMenu
    ? featureOf([supplierMenu, ...menus.filter((m) => String(m.parentId) === String(supplierMenu.menuId))])
    : undefined;
  return { token, base: `/biz/${feature}`, supplierBase: `/biz/${supplierFeature ?? 'supplier'}`, top, menu, buttons };
}

function ctx(): Promise<Ctx> {
  ctxPromise ??= discover();
  return ctxPromise;
}

async function createSupplier(status: string): Promise<Supplier> {
  const c = await ctx();
  const t = uid();
  const name = `采购前端供应商${t}`;
  const body: Record<string, unknown> = { status };
  for (const alias of SUPPLIER_CODE_ALIASES) body[alias] = `PF${t}`;
  for (const alias of SUPPLIER_NAME_ALIASES) body[alias] = name;
  const created = await api('POST', c.supplierBase, c.token, body);
  expect(created.code, JSON.stringify(created)).toBe(200);
  const list = await api(
    'GET',
    `${c.supplierBase}/list?pageNum=1&pageSize=200&supplierName=${encodeURIComponent(name)}`,
    c.token
  );
  const row = (list.data?.rows ?? []).find((r: any) => Object.values(r).some((v) => String(v) === name));
  expect(row, `新建的供应商 ${name} 查询不到`).toBeTruthy();
  const idKey = ['supplierId', 'id'].find((k) => row[k]) ?? Object.keys(row).find((k) => k.endsWith('Id') && row[k]);
  expect(idKey, `供应商记录没有主键字段: ${JSON.stringify(row)}`).toBeTruthy();
  return { id: String(row[idKey!]), name };
}

async function createOrder(supplier: Supplier, details: Detail[], remark?: string): Promise<{ remark: string; orderNo: string }> {
  const c = await ctx();
  const note = remark ?? `前端冒烟${uid()}`;
  const build = (suffix: string) => {
    const body: Record<string, unknown> = {};
    const put = (aliases: string[], value: unknown) => {
      for (const alias of aliases) body[alias] = value;
    };
    put(MAIN_ALIASES.supplierId, supplier.id);
    put(MAIN_ALIASES.supplierName, supplier.name);
    put(MAIN_ALIASES.orderDate, todayStr() + suffix);
    put(MAIN_ALIASES.remark, note);
    const items = details.map((detail) => {
      const item: Record<string, unknown> = {};
      for (const [logical, value] of Object.entries(detail)) {
        for (const alias of DETAIL_ALIASES[logical]) item[alias] = value;
      }
      return item;
    });
    for (const key of DETAIL_LIST_KEYS) body[key] = items;
    return body;
  };
  let result = await api('POST', c.base, c.token, build(dateSuffix));
  if (result.code !== 200 && dateSuffix === '') {
    dateSuffix = ' 00:00:00';
    result = await api('POST', c.base, c.token, build(dateSuffix));
    if (result.code !== 200) dateSuffix = '';
  }
  expect(result.code, `准备采购单失败: ${JSON.stringify(result)}`).toBe(200);
  const list = await api('GET', `${c.base}/list?pageNum=1&pageSize=200`, c.token);
  const row = (list.data?.rows ?? []).find((r: any) => Object.values(r).some((v) => String(v) === note));
  expect(row, `备注为 ${note} 的采购单查询不到`).toBeTruthy();
  const orderNo = Object.values(row).map(String).find((v) => /^PO\d{8}/.test(v));
  expect(orderNo, `采购单没有『PO+日期+流水号』单号: ${JSON.stringify(row)}`).toBeTruthy();
  return { remark: note, orderNo: String(orderNo) };
}

async function createReadonlyUser(): Promise<{ username: string; password: string }> {
  const c = await ctx();
  const t = uid();
  const roleKey = `po_ui_${t}`;
  const menuIds = [c.top.menuId, c.menu.menuId,
    ...c.buttons.filter((b) => /:(list|query)$/.test(String(b.perms ?? ''))).map((b) => b.menuId)];
  const role = await api('POST', '/system/role', c.token, {
    roleName: `采购只读${t}`, roleKey, roleSort: 99, status: '0', dataScope: '3',
    menuCheckStrictly: true, deptCheckStrictly: true, menuIds
  });
  expect(role.code, JSON.stringify(role)).toBe(200);
  const roles = await api('GET', `/system/role/list?pageNum=1&pageSize=10&roleKey=${roleKey}`, c.token);
  const roleId = (roles.data?.rows ?? []).find((r: any) => r.roleKey === roleKey)?.roleId;
  expect(roleId, `创建的测试角色 ${roleKey} 查询不到`).toBeTruthy();
  const username = `poui${t}`;
  const password = `Smoke#${t}`;
  const user = await api('POST', '/system/user', c.token, {
    userName: username, nickName: `采购只读${t}`, password, deptId: OTHER_DEPT_ID,
    roleIds: [roleId], status: '0'
  });
  expect(user.code, JSON.stringify(user)).toBe(200);
  return { username, password };
}

async function openOrderPage(page: Page, username = 'admin', password = 'admin123'): Promise<void> {
  await page.goto('/login');
  await page.getByPlaceholder(/用户名|username/i).fill(username);
  await page.getByPlaceholder(/密码|password/i).fill(password);
  await page.locator('button.submit-button').click();
  await expect(page).toHaveURL(/index/, { timeout: 30_000 });
  const sidebar = page.locator('.sidebar-container');
  await sidebar.getByText(DIR_NAME, { exact: true }).click();
  await sidebar.getByText(MENU_NAME, { exact: true }).click();
  await expect(page).not.toHaveURL(/index$/);
  await expect(mainTable(page)).toBeVisible({ timeout: 30_000 });
}

function mainTable(page: Page): Locator {
  return page.locator('.el-table').first();
}

function rowsOf(table: Locator): Locator {
  return table.locator('.el-table__body tr.el-table__row');
}

async function headerIndex(table: Locator, label: string): Promise<number> {
  const headers = await table.locator('.el-table__header th').allInnerTexts();
  const index = headers.findIndex((h) => h.replace(/\s/g, '').includes(label));
  expect(index, `表头缺少“${label}”列: ${JSON.stringify(headers)}`).toBeGreaterThanOrEqual(0);
  return index;
}

function cell(row: Locator, index: number): Locator {
  return row.locator('td').nth(index);
}

async function filterBy(page: Page, label: string, value: string): Promise<void> {
  const form = page.locator('form.el-form--inline').first();
  const item = form.locator('.el-form-item').filter({ hasText: label }).first();
  await expect(item, `查询区缺少“${label}”筛选项`).toHaveCount(1);
  if (await item.locator('.el-select').count()) {
    await item.locator('.el-select').first().click();
    const option = page.locator('.el-select-dropdown__item').filter({ hasText: value }).first();
    await expect(option, `“${label}”下拉里没有 ${value}`).toBeVisible({ timeout: 15_000 });
    await option.click();
  } else {
    await item.locator('input, textarea').first().fill(value);
  }
  await form.getByRole('button', { name: /搜 ?索/ }).click();
  await page.waitForTimeout(800);
}

function dialogOf(page: Page): Locator {
  return page.locator('.el-dialog:visible');
}

function dialogItem(dialog: Locator, label: string): Locator {
  return dialog.locator('.el-form-item').filter({ hasText: label }).first();
}

async function chooseInDialog(page: Page, dialog: Locator, label: string, value: string): Promise<void> {
  const item = dialogItem(dialog, label);
  await expect(item, `弹窗缺少“${label}”表单项`).toHaveCount(1);
  await item.locator('.el-select').first().click();
  const option = page.locator('.el-select-dropdown__item').filter({ hasText: value }).first();
  await expect(option, `“${label}”下拉里没有 ${value}`).toBeVisible({ timeout: 15_000 });
  await option.click();
}

async function fillInDialog(page: Page, dialog: Locator, label: string, value: string): Promise<void> {
  const item = dialogItem(dialog, label);
  await expect(item, `弹窗缺少“${label}”表单项`).toHaveCount(1);
  await item.locator('input, textarea').first().fill(value);
  await page.keyboard.press('Enter');
}

async function fillCell(page: Page, row: Locator, index: number, value: string): Promise<void> {
  const input = cell(row, index).locator('input, textarea').first();
  await expect(input, `明细行第 ${index} 列没有输入框`).toBeVisible();
  await input.fill(value);
  await input.press('Enter');
}

// 行内操作按钮可能是带文字的按钮，也可能是生成器风格的“图标按钮 + tooltip”。
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

async function clickRowAction(page: Page, row: Locator, label: string): Promise<void> {
  const button = await findRowAction(page, row, label);
  expect(button, `行内没有“${label}”按钮`).not.toBeNull();
  await button!.click();
}

async function rowActionUsable(page: Page, row: Locator, label: string): Promise<boolean> {
  const button = await findRowAction(page, row, label);
  if (!button) return false;
  return (await button.isVisible()) && !(await button.isDisabled());
}

async function expectSuccess(page: Page): Promise<void> {
  await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 20_000 });
}

async function confirmIfAny(page: Page): Promise<void> {
  const box = page.locator('.el-message-box');
  try {
    await box.waitFor({ state: 'visible', timeout: 3_000 });
  } catch {
    return;
  }
  await box.locator('.el-message-box__btns .el-button--primary').click();
}

test('A28 业务管理目录下的采购单管理菜单可以打开列表页', async ({ page }) => {
  const c = await ctx();
  await openOrderPage(page);
  await expect(page).toHaveURL(new RegExp(`${c.top.path}/${c.menu.path}`));
  await expect(mainTable(page)).toBeVisible();
});

test('A4 按单号查询只展示匹配的采购单并带核心列', async ({ page }) => {
  const t = uid();
  const supplier = await createSupplier('0');
  const wanted = await createOrder(supplier, [{ materialName: `甲${t}`, quantity: 2, price: 10 }]);
  const other = await createOrder(supplier, [{ materialName: `乙${t}`, quantity: 1, price: 10 }]);
  await openOrderPage(page);
  await filterBy(page, '单号', wanted.orderNo);
  const rows = rowsOf(mainTable(page));
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText(wanted.orderNo);
  await expect(rows.first()).not.toContainText(other.orderNo);
  for (const label of ['单号', '供应商', '下单日期', '状态', '合计金额']) {
    await headerIndex(mainTable(page), label);
  }
});

test('A10 新增弹窗的供应商下拉只显示启用状态的供应商', async ({ page }) => {
  const enabled = await createSupplier('0');
  const disabled = await createSupplier('1');
  await openOrderPage(page);
  await page.getByRole('button', { name: '新增' }).first().click();
  const dialog = dialogOf(page);
  await expect(dialog).toBeVisible();
  const item = dialogItem(dialog, '供应商');
  await expect(item, '弹窗缺少“供应商”表单项').toHaveCount(1);
  await item.locator('.el-select').first().click();
  try {
    await item.locator('input').first().fill('采购前端供应商');
    await page.waitForTimeout(800);
  } catch {
    // 下拉不支持搜索时忽略
  }
  const dropdown = page.locator('.el-select-dropdown__item');
  await expect(dropdown.filter({ hasText: enabled.name })).toHaveCount(1);
  await expect(dropdown.filter({ hasText: disabled.name })).toHaveCount(0);
});

test('A9 新增采购单及两行明细后列表出现草稿单据并显示合计金额', async ({ page }) => {
  const t = uid();
  const supplier = await createSupplier('0');
  await openOrderPage(page);
  await page.getByRole('button', { name: '新增' }).first().click();
  const dialog = dialogOf(page);
  await expect(dialog).toBeVisible();
  await chooseInDialog(page, dialog, '供应商', supplier.name);
  await fillInDialog(page, dialog, '日期', todayStr());
  const detailTable = dialog.locator('.el-table').first();
  await expect(detailTable, '弹窗里没有明细表格').toHaveCount(1);
  const detailRows = rowsOf(detailTable);
  const addButton = dialog.getByRole('button', { name: /添加|新增|增加/ }).first();
  await expect(addButton, '弹窗里没有新增明细行的按钮').toHaveCount(1);
  let current = await detailRows.count();
  while (current < 2) {
    await addButton.click();
    current += 1;
    await expect(detailRows).toHaveCount(current);
  }
  const nameCol = await headerIndex(detailTable, '物料');
  const qtyCol = await headerIndex(detailTable, '数量');
  const priceCol = await headerIndex(detailTable, '单价');
  await fillCell(page, detailRows.nth(0), nameCol, `界面物料甲${t}`);
  await fillCell(page, detailRows.nth(0), qtyCol, '2');
  await fillCell(page, detailRows.nth(0), priceCol, '12.5');
  await fillCell(page, detailRows.nth(1), nameCol, `界面物料乙${t}`);
  await fillCell(page, detailRows.nth(1), qtyCol, '3');
  await fillCell(page, detailRows.nth(1), priceCol, '4');
  await dialog.getByRole('button', { name: /确 ?定/ }).click();
  await expectSuccess(page);
  await expect(dialog).toBeHidden();
  await filterBy(page, '供应商', supplier.name);
  const rows = rowsOf(mainTable(page));
  await expect(rows).toHaveCount(1);
  const statusCol = await headerIndex(mainTable(page), '状态');
  const totalCol = await headerIndex(mainTable(page), '合计金额');
  await expect(cell(rows.first(), statusCol)).toContainText('草稿');
  expect(amountOf(await cell(rows.first(), totalCol).innerText())).toBe(37);
});

test('A13 修改弹窗回显采购单主信息与全部明细行', async ({ page }) => {
  const t = uid();
  const supplier = await createSupplier('0');
  const details = [
    { materialName: `回显甲${t}`, quantity: 1, price: 10 },
    { materialName: `回显乙${t}`, quantity: 2, price: 20 },
    { materialName: `回显丙${t}`, quantity: 3, price: 5 }
  ];
  const order = await createOrder(supplier, details);
  await openOrderPage(page);
  await filterBy(page, '供应商', supplier.name);
  const rows = rowsOf(mainTable(page));
  await expect(rows).toHaveCount(1);
  await clickRowAction(page, rows.first(), '修改');
  const dialog = dialogOf(page);
  await expect(dialog).toBeVisible();
  await expect(dialogItem(dialog, '供应商').locator('input').first()).toHaveValue(new RegExp(supplier.name));
  expect(await dialogItem(dialog, '日期').locator('input').first().inputValue()).toContain(todayStr());
  expect(await dialogItem(dialog, '备注').locator('input, textarea').first().inputValue()).toContain(order.remark);
  const detailTable = dialog.locator('.el-table').first();
  const detailRows = rowsOf(detailTable);
  await expect(detailRows).toHaveCount(3);
  const nameCol = await headerIndex(detailTable, '物料');
  const shown: string[] = [];
  for (let i = 0; i < 3; i += 1) {
    const input = cell(detailRows.nth(i), nameCol).locator('input, textarea').first();
    shown.push((await input.count()) ? await input.inputValue() : (await cell(detailRows.nth(i), nameCol).innerText()).trim());
  }
  expect(shown.sort()).toEqual(details.map((d) => d.materialName).sort());
});

test('A14 修改明细单价后列表合计金额按新单价重算', async ({ page }) => {
  const t = uid();
  const supplier = await createSupplier('0');
  await createOrder(supplier, [{ materialName: `调价${t}`, quantity: 2, price: 10 }]);
  await openOrderPage(page);
  await filterBy(page, '供应商', supplier.name);
  const rows = rowsOf(mainTable(page));
  await expect(rows).toHaveCount(1);
  const totalCol = await headerIndex(mainTable(page), '合计金额');
  expect(amountOf(await cell(rows.first(), totalCol).innerText())).toBe(20);
  await clickRowAction(page, rows.first(), '修改');
  const dialog = dialogOf(page);
  await expect(dialog).toBeVisible();
  const detailTable = dialog.locator('.el-table').first();
  const priceCol = await headerIndex(detailTable, '单价');
  await fillCell(page, rowsOf(detailTable).first(), priceCol, '30');
  await dialog.getByRole('button', { name: /确 ?定/ }).click();
  await expectSuccess(page);
  await expect(dialog).toBeHidden();
  await expect(rows).toHaveCount(1);
  await expect.poll(async () => amountOf(await cell(rows.first(), totalCol).innerText()),
    { timeout: 15_000 }).toBe(60);
});

test('A19 勾选两张草稿采购单批量删除后一起从列表消失', async ({ page }) => {
  const t = uid();
  const supplier = await createSupplier('0');
  await createOrder(supplier, [{ materialName: `批删甲${t}`, quantity: 1, price: 10 }]);
  await createOrder(supplier, [{ materialName: `批删乙${t}`, quantity: 2, price: 10 }]);
  await openOrderPage(page);
  await filterBy(page, '供应商', supplier.name);
  const rows = rowsOf(mainTable(page));
  await expect(rows).toHaveCount(2);
  const pagination = page.locator('.el-pagination__total');
  if (await pagination.count()) {
    expect(amountOf(await pagination.first().innerText())).toBe(2);
  }
  await rows.nth(0).locator('.el-checkbox').first().click();
  await rows.nth(1).locator('.el-checkbox').first().click();
  await page.getByRole('button', { name: '删除' }).first().click();
  await confirmIfAny(page);
  await expectSuccess(page);
  await expect(rows).toHaveCount(0);
});

test('A23 提交草稿采购单后状态变为已提交且修改删除按钮不可用', async ({ page }) => {
  const t = uid();
  const supplier = await createSupplier('0');
  await createOrder(supplier, [{ materialName: `提交${t}`, quantity: 2, price: 10 }]);
  await openOrderPage(page);
  await filterBy(page, '供应商', supplier.name);
  const rows = rowsOf(mainTable(page));
  await expect(rows).toHaveCount(1);
  const statusCol = await headerIndex(mainTable(page), '状态');
  await expect(cell(rows.first(), statusCol)).toContainText('草稿');
  await clickRowAction(page, rows.first(), '提交');
  await confirmIfAny(page);
  await expectSuccess(page);
  await expect(cell(rows.first(), statusCol)).toContainText('已提交', { timeout: 15_000 });
  expect(await rowActionUsable(page, rows.first(), '修改'), '已提交单据仍可点击修改').toBe(false);
  expect(await rowActionUsable(page, rows.first(), '删除'), '已提交单据仍可点击删除').toBe(false);
});

test('A31 只有查询权限的用户看得到列表但看不到操作按钮', async ({ page }) => {
  const t = uid();
  const supplier = await createSupplier('0');
  await createOrder(supplier, [{ materialName: `只读${t}`, quantity: 1, price: 10 }]);
  const user = await createReadonlyUser();
  await openOrderPage(page, user.username, user.password);
  const rows = rowsOf(mainTable(page));
  await expect(rows.first()).toBeVisible({ timeout: 20_000 });
  for (const label of ['新增', '修改', '删除', '提交', '导出']) {
    await expect(page.getByRole('button', { name: label }), `无权限却显示了“${label}”按钮`).toHaveCount(0);
  }
  for (const label of ['修改', '删除', '提交']) {
    expect(await rowActionUsable(page, rows.first(), label), `行内仍可操作“${label}”`).toBe(false);
  }
});
