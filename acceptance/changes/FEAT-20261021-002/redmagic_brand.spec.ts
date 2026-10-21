// FEAT-20261021-002 新行为（实现前必须失败）：红魔品牌统一、浏览器标题、侧栏展开/折叠标识、
// 登录表单不预填、首页替换上游推广内容。
import { expect, test } from '@playwright/test';
import {
  BRAND_FULL, BRAND_SHORT, expectPasswordEmpty, homeMain, login, openAuthPage, sidebarBrand, usernameBox
} from './redmagic_support';

const UPSTREAM_PROMO = ['Plus UI Workspace', '企业级后台管理系统'];

test('A1 A4 登录页表单主标题与浏览器标题为品牌全称，不出现上游推广文案', async ({ page }) => {
  await openAuthPage(page, '/login', true);
  await expect(page.locator('form').first().getByRole('heading').first()).toHaveText(BRAND_FULL);
  await expect(page).toHaveTitle(BRAND_FULL);
  await expect(page.locator('body')).not.toContainText('企业级后台管理系统');
});

test('A6 注册页表单主标题与浏览器标题为品牌全称', async ({ page }) => {
  await openAuthPage(page, '/register', true);
  await expect(page.locator('form').first().getByRole('heading').first()).toHaveText(BRAND_FULL);
  await expect(page).toHaveTitle(BRAND_FULL);
});

test('A7 没有记住的账号时登录表单账号和口令都为空', async ({ page }) => {
  await openAuthPage(page, '/login', true);
  await expect(page.getByRole('button', { name: '登 录' })).toBeVisible();
  await expect(usernameBox(page)).toHaveValue('');
  await expectPasswordEmpty(page);
});

test('A2 动态标题开启：登录/注册无页面名为品牌全称，首页与业务页为“页面名 - 品牌全称”', async ({ page }) => {
  await openAuthPage(page, '/login', true);
  await expect(page).toHaveTitle(BRAND_FULL);
  await openAuthPage(page, '/register');
  await expect(page).toHaveTitle(BRAND_FULL);
  await openAuthPage(page, '/login');
  await expect(page).toHaveTitle(BRAND_FULL);
  await login(page);
  await expect(page).toHaveTitle(`首页 - ${BRAND_FULL}`);
  await page.getByRole('menuitem', { name: '业务管理' }).click();
  await page.getByRole('link', { name: '采购单管理' }).click();
  await expect(page.getByRole('heading', { name: '采购单列表' })).toBeVisible({ timeout: 30_000 });
  await expect(page).toHaveTitle(`采购单管理 - ${BRAND_FULL}`);
});

test('A2 动态标题关闭：任何页面的浏览器标题都只是品牌全称', async ({ page }) => {
  await login(page);
  const stored = await page.evaluate(() => localStorage.getItem('layout-setting'));
  expect(stored, '布局设置 layout-setting 应已写入本地存储').not.toBeNull();
  await page.evaluate((raw) => {
    const setting = JSON.parse(raw as string);
    setting.dynamicTitle = false;
    localStorage.setItem('layout-setting', JSON.stringify(setting));
  }, stored);
  await page.goto('/index');
  await homeMain(page);
  await expect(page).toHaveTitle(BRAND_FULL);
  await page.getByRole('menuitem', { name: '业务管理' }).click();
  await page.getByRole('link', { name: '采购单管理' }).click();
  await expect(page.getByRole('heading', { name: '采购单列表' })).toBeVisible({ timeout: 30_000 });
  await expect(page).toHaveTitle(BRAND_FULL);
});

test('A1 A5 侧栏展开时标识文字含短名，折叠后标识仍可见且可访问名称含短名', async ({ page }) => {
  await login(page);
  await homeMain(page);
  const brand = sidebarBrand(page);
  await expect(page.locator('.sidebar-shell .el-menu--collapse')).toHaveCount(0);
  await expect(brand).toBeVisible();
  await expect(brand).toContainText(BRAND_SHORT);
  await page.locator('#hamburger-container').click();
  await expect(page.locator('.sidebar-shell .el-menu--collapse')).toBeVisible();
  await expect(sidebarBrand(page)).toBeVisible();
  await expect(sidebarBrand(page)).toHaveAccessibleName(new RegExp(BRAND_SHORT));
});

test('A3 登录、注册、侧栏、首页的品牌名称一致且不再显示上游推广文案', async ({ page }) => {
  for (const route of ['/login', '/register'] as const) {
    await openAuthPage(page, route, route === '/login');
    await expect(page.locator('form').first().getByRole('heading').first()).toHaveText(BRAND_FULL);
    for (const text of UPSTREAM_PROMO) await expect(page.locator('body'), `${route} 仍有 ${text}`).not.toContainText(text);
  }
  await login(page);
  const main = await homeMain(page);
  await expect(main.getByRole('heading').first()).toContainText(BRAND_FULL);
  await expect(sidebarBrand(page)).toContainText(BRAND_SHORT);
  await page.locator('#hamburger-container').click();
  await expect(page.locator('.sidebar-shell .el-menu--collapse')).toBeVisible();
  await expect(sidebarBrand(page)).toHaveAccessibleName(new RegExp(BRAND_SHORT));
  await expect(page).toHaveTitle(`首页 - ${BRAND_FULL}`);
});

test('B1 首页主标题含品牌全称，正文介绍供应商管理和采购单管理', async ({ page }) => {
  await login(page);
  const main = await homeMain(page);
  await expect(main.getByRole('heading').first()).toContainText(BRAND_FULL);
  await expect(main).toContainText('供应商管理');
  await expect(main).toContainText('采购单管理');
});

test('B2 首页主内容区没有上游项目矩阵、源码、更新日志等推广内容和入口', async ({ page }) => {
  await login(page);
  const main = await homeMain(page);
  for (const text of ['RuoYi-Cloud-Plus', '项目矩阵', '查看源码', '更新日志']) {
    await expect(main, `首页仍有“${text}”`).not.toContainText(text);
  }
  const domains = ['gitee.com/dromara', 'github.com/dromara', 'plus-doc.dromara.org'];
  for (const domain of domains) {
    await expect(main.locator(`a[href*="${domain}"]`), `首页仍有指向 ${domain} 的链接`).toHaveCount(0);
  }
  const html = await main.innerHTML();
  for (const domain of domains) expect(html.includes(domain), `首页标记里仍有 ${domain}`).toBe(false);
});
