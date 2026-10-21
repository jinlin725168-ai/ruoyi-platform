// FEAT-20261021-002 验收用例共用的步骤。登录、菜单、退出的定位器沿用 acceptance/smoke/purchase-order 与
// acceptance/ui/supplier-management 已验证的写法。测试夹具账号取自既有辅助工具
// acceptance/tools/ruoyi_client.py 中 Client.login 的默认参数，本套件不另行保存任何口令；
// 口令框只按长度断言，避免把口令值打进失败日志。
import { expect, type Locator, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import path from 'node:path';

export const BRAND_FULL = '红魔业务工作台';
export const BRAND_SHORT = '红魔';

type Account = { username: string; password: string };
let account: Account | undefined;

export function fixtureAccount(): Account {
  if (account) return account;
  const file = path.resolve(process.cwd(), 'acceptance/tools/ruoyi_client.py');
  const source = readFileSync(file, 'utf-8');
  const match = /def login\(\s*self,\s*username:\s*str\s*=\s*"([^"]+)",\s*password:\s*str\s*=\s*"([^"]+)"/.exec(source);
  if (!match) throw new Error(`无法从 ${file} 读取测试夹具账号`);
  account = { username: match[1], password: match[2] };
  return account;
}

type CaptchaResponse = { code: number; data: { captchaEnabled: boolean } };

/** 监听本次导航的 GET 验证码请求，等待响应体完整接收并验证返回包裹。 */
async function navigateAuthPage(page: Page, navigate: () => Promise<unknown>): Promise<CaptchaResponse> {
  // 先销毁旧文档，再监听新导航，避免捕获退出登录触发的旧验证码响应。
  await page.goto('about:blank');
  const [response] = await Promise.all([
    page.waitForResponse((r) =>
      r.request().method() === 'GET' &&
      /\/auth\/code$/.test(new URL(r.url()).pathname),
    { timeout: 30_000 }),
    navigate()
  ]);
  const failure = await response.finished();
  if (failure) throw new Error('验证码配置响应未完整接收');
  if (!response.ok()) throw new Error(`验证码配置接口 HTTP 状态异常：${response.status()}`);
  const body: unknown = await response.json();
  if (typeof body !== 'object' || body === null || Array.isArray(body)) {
    throw new Error('验证码配置响应必须为对象');
  }
  const envelope = body as { code?: unknown; data?: unknown };
  if (envelope.code !== 200) throw new Error('验证码配置接口未返回成功业务状态');
  if (typeof envelope.data !== 'object' || envelope.data === null || Array.isArray(envelope.data)) {
    throw new Error('验证码配置响应缺少 data 对象');
  }
  if (typeof (envelope.data as { captchaEnabled?: unknown }).captchaEnabled !== 'boolean') {
    throw new Error('验证码配置响应 data.captchaEnabled 必须为布尔值');
  }
  await expect(page.locator('form').first()).toBeVisible({ timeout: 30_000 });
  return body as CaptchaResponse;
}

/** 在认证页 origin 清存储，再隔离旧文档并明确导航到目标路由。 */
export async function openAuthPage(page: Page, route: '/login' | '/register', clearStorage = false): Promise<CaptchaResponse> {
  const initial = await navigateAuthPage(page, () => page.goto(route));
  if (!clearStorage) return initial;
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  return navigateAuthPage(page, () => page.goto(route));
}

export function usernameBox(page: Page): Locator {
  return page.getByRole('textbox', { name: '用户名' });
}

export function passwordBox(page: Page): Locator {
  return page.getByRole('textbox', { name: '密码' });
}

export async function expectPasswordEmpty(page: Page): Promise<void> {
  await expect
    .poll(async () => (await passwordBox(page).inputValue()).length, { message: '口令框应为空（只比较长度，值不输出）' })
    .toBe(0);
}

export async function login(page: Page, remember = false): Promise<void> {
  const { username, password } = fixtureAccount();
  await openAuthPage(page, '/login');
  await usernameBox(page).fill(username);
  await passwordBox(page).fill(password);
  if (remember) {
    await page.locator('.el-checkbox').filter({ hasText: '记住我' }).click();
    await expect(page.getByRole('checkbox', { name: '记住我' })).toBeChecked();
  }
  await page.getByRole('button', { name: '登 录' }).click();
  await expect(page).toHaveURL(/\/index$/, { timeout: 30_000 });
}

export async function logout(page: Page): Promise<void> {
  await page.locator('.avatar-wrapper').click();
  await page.getByRole('menuitem', { name: '退出登录' }).click();
  await page.getByRole('dialog').getByRole('button', { name: '确定' }).click();
  await expect(page).toHaveURL(/\/login(\?|$)/, { timeout: 30_000 });
}

/** 首页主内容区（layout/components/AppMain.vue），等到首个标题渲染出来再返回。 */
export async function homeMain(page: Page): Promise<Locator> {
  const main = page.locator('section.app-main');
  await expect(main.getByRole('heading').first()).toBeVisible({ timeout: 30_000 });
  return main;
}

/** 侧栏品牌标识：侧栏容器里的第一个链接（Logo 渲染在菜单之前）。 */
export function sidebarBrand(page: Page): Locator {
  return page.locator('.sidebar-shell').getByRole('link').first();
}
