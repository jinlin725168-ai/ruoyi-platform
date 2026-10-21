// FEAT-20261021-002 既有行为（实现前后都必须通过）：登录、错误口令、记住账号、第三方入口、验证码关闭、
// 退出登录、上游版权署名、首页不出现编造统计或厂商宣传。
import { expect, test } from '@playwright/test';
import {
  expectPasswordEmpty, fixtureAccount, homeMain, login, logout, openAuthPage, passwordBox, usernameBox
} from './redmagic_support';

test('A8 测试夹具账号登录后进入首页，并能从动态菜单打开采购单页面', async ({ page }) => {
  await login(page);
  await page.getByRole('menuitem', { name: '业务管理' }).click();
  await page.getByRole('link', { name: '采购单管理' }).click();
  await expect(page).toHaveURL(/\/biz\/purchaseOrder$/);
  await expect(page.getByRole('heading', { name: '采购单列表' })).toBeVisible({ timeout: 30_000 });
});

test('A9 错误口令登录停留在登录页并显示后端返回的错误提示', async ({ page }) => {
  await openAuthPage(page, '/login', true);
  await usernameBox(page).fill(fixtureAccount().username);
  await passwordBox(page).fill(`wrong-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`);
  const responsePromise = page.waitForResponse((r) => r.url().includes('/auth/login'), { timeout: 30_000 });
  await page.getByRole('button', { name: '登 录' }).click();
  const body = await (await responsePromise).json();
  expect(body.code, '错误口令应被后端拒绝').not.toBe(200);
  const msg = String(body.msg ?? '').trim();
  expect(msg.length, '后端应返回错误提示').toBeGreaterThan(0);
  await expect(page.locator('.el-message').filter({ hasText: msg })).toBeVisible();
  await expect(page).toHaveURL(/\/login(\?|$)/);
  await expect(page.getByRole('button', { name: '登 录' })).toBeVisible();
});

test('A10 勾选记住我登录并退出后，登录页只回填账号，口令为空，记住我保持勾选', async ({ page }) => {
  await openAuthPage(page, '/login', true);
  await login(page, true);
  await logout(page);
  await openAuthPage(page, '/login');
  await expect(usernameBox(page)).toHaveValue(fixtureAccount().username);
  await expectPasswordEmpty(page);
  await expect(page.getByRole('checkbox', { name: '记住我' })).toBeChecked();
});

test('A11 登录页可见微信、MaxKey、TopIAM、Gitee、GitHub 五个第三方登录入口', async ({ page }) => {
  await openAuthPage(page, '/login', true);
  for (const name of [/微信/, /MaxKey/i, /TopIAM/i, /Gitee/i, /GitHub/i]) {
    await expect(page.getByRole('button', { name })).toBeVisible();
  }
});

test('A12 退出登录回到登录页，再访问首页被重定向到登录页', async ({ page }) => {
  await login(page);
  await homeMain(page);
  await logout(page);
  await expect(page.getByRole('button', { name: '登 录' })).toBeVisible();
  await page.goto('/index');
  await expect(page).toHaveURL(
    (url) => url.pathname === '/login' && url.searchParams.get('redirect') === '/index',
    { timeout: 30_000 }
  );
  await expect(page.getByRole('button', { name: '登 录' })).toBeVisible();
});

test('A13 后端报告验证码关闭时登录页不显示验证码输入框', async ({ page }) => {
  const code = await openAuthPage(page, '/login', true);
  expect(code.data.captchaEnabled, 'smoke 运行档的 /auth/code 应报告验证码关闭').toBe(false);
  await expect(page.getByRole('button', { name: '登 录' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: '验证码' })).toHaveCount(0);
  await expect(page.getByPlaceholder('验证码')).toHaveCount(0);
});

test('A14 登录页和注册页页脚保留上游版权署名', async ({ page }) => {
  const footer = `Copyright © 2018-${new Date().getFullYear()} 疯狂的狮子Li All Rights Reserved.`;
  for (const route of ['/login', '/register'] as const) {
    await openAuthPage(page, route, route === '/login');
    await expect(page.getByText(footer, { exact: false }), `${route} 页脚缺少上游署名`).toBeVisible();
  }
});

test('B3 首页主内容区不出现编造的业务统计或厂商宣传字样', async ({ page }) => {
  await login(page);
  const main = await homeMain(page);
  expect((await main.innerText()).trim().length, '首页主内容区应已渲染').toBeGreaterThan(0);
  for (const word of ['收益', '营收', '利润', '销售额', '成交额', '官方授权', '背书']) {
    await expect(main, `首页出现“${word}”`).not.toContainText(word);
  }
});
