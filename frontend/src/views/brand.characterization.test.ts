import { readFileSync } from 'node:fs';
import ts from 'typescript';
import { describe, expect, it, vi } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');
const login = read('./login.vue');
const register = read('./register.vue');

// Execute existing pure handlers without mounting a component or evaluating form defaults.
function handler(source: string, name: string, bindings: Record<string, unknown>) {
  const script = source.split('<script setup')[1].split('</script>')[0];
  const file = ts.createSourceFile('page.ts', script.slice(script.indexOf('>') + 1), ts.ScriptTarget.Latest, true);
  const statement = file.statements.find(item => ts.isVariableStatement(item)
    && item.declarationList.declarations.some(declaration => declaration.name.getText(file) === name));
  if (!statement) throw new Error(`Missing handler: ${name}`);
  const code = ts.transpileModule(statement.getText(file), { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  return new Function(...Object.keys(bindings), `${code}; return ${name};`)(...Object.values(bindings));
}

describe('authentication behavior preserved during branding', () => {
  it.each([true, false])('login submission preserves redirect and failure handling (success=%s)', async success => {
    const stored = new Map<string, string>([['password', 'obsolete-fixture']]);
    const localStorage = { setItem: (key: string, value: string) => stored.set(key, value),
      removeItem: (key: string) => stored.delete(key) };
    const loginForm = { value: { username: 'warehouse-reader', rememberMe: true } };
    const loading = { value: false };
    const push = vi.fn().mockResolvedValue(undefined);
    const getCode = vi.fn().mockResolvedValue(undefined);
    const loginRequest = vi.fn().mockResolvedValue(undefined);
    let completion: Promise<void> | undefined;
    const loginRef = { value: { validate: (callback: (valid: boolean) => Promise<void>) => { completion = callback(true); } } };
    handler(login, 'handleLogin', { loginRef, loginForm, loading, localStorage,
      userStore: { login: loginRequest }, to: async (result: Promise<void>) => { await result; return [success ? null : new Error('rejected')]; },
      redirect: { value: '/biz/purchaseOrder?filter=mine' }, router: { push }, captchaEnabled: { value: true }, getCode })();
    await completion;
    expect(loginRequest).toHaveBeenCalledWith(loginForm.value);
    expect(stored.get('username')).toBe('warehouse-reader');
    expect(stored.get('rememberMe')).toBe('true');
    expect(stored.has('password')).toBe(false);
    expect(loading.value).toBe(false);
    if (success) {
      expect(push).toHaveBeenCalledWith('/biz/purchaseOrder?filter=mine');
      expect(getCode).not.toHaveBeenCalled();
    } else {
      expect(push).not.toHaveBeenCalled();
      expect(getCode).toHaveBeenCalledOnce();
    }
  });

  it('restores a remembered non-admin account, discards historical password and keeps rememberMe', () => {
    const stored = new Map([['username', 'warehouse-reader'], ['rememberMe', 'true'], ['password', 'obsolete-fixture']]);
    const localStorage = { getItem: (key: string) => stored.get(key) ?? null, removeItem: (key: string) => stored.delete(key) };
    const loginForm = { value: {} };
    handler(login, 'getLoginData', { localStorage, loginForm })();
    expect(loginForm.value).toMatchObject({ username: 'warehouse-reader', password: '', rememberMe: true });
    expect(stored.has('password')).toBe(false);
    expect(stored.get('username')).toBe('warehouse-reader');
  });

  it.each([false, true, undefined])('honors captchaEnabled=%s from the server', async enabled => {
    const captchaEnabled = { value: false };
    const codeUrl = { value: 'unchanged' };
    const loginForm = { value: { code: 'previous', uuid: 'previous' } };
    const getCodeImg = vi.fn().mockResolvedValue({ data: { captchaEnabled: enabled, img: 'fixture-image', uuid: 'fixture-id' } });
    await handler(login, 'getCode', { captchaEnabled, codeUrl, loginForm, getCodeImg })();
    expect(captchaEnabled.value).toBe(enabled !== false);
    expect(loginForm.value).toEqual(enabled === false
      ? { code: 'previous', uuid: 'previous' } : { code: '', uuid: 'fixture-id' });
    expect(codeUrl.value).toBe(enabled === false ? 'unchanged' : 'data:image/gif;base64,fixture-image');
  });

  it('registration rejects mismatched confirmation and accepts a match', () => {
    const registerForm = { value: { password: 'generated-test-value' } };
    const validate = handler(register, 'equalToPassword', { registerForm, t: (key: string) => key });
    const callback = vi.fn();
    validate({}, 'different-test-value', callback);
    expect(callback.mock.calls[0][0].message).toBe('register.rule.confirmPassword.equalToPassword');
    callback.mockClear();
    validate({}, registerForm.value.password, callback);
    expect(callback).toHaveBeenCalledWith();
  });

  it('keeps form bindings, third-party providers and upstream attribution', () => {
    for (const provider of ['wechat', 'maxkey', 'topiam', 'gitee', 'github']) {
      expect(login).toContain(`doSocialLogin('${provider}')`);
    }
    for (const [source, form] of [[login, 'loginForm'], [register, 'registerForm']]) {
      for (const field of ['username', 'password', 'code']) expect(source).toContain(`v-model="${form}.${field}"`);
      expect(source).toContain('v-if="captchaEnabled"');
      expect(source).toContain('Copyright © 2018-{{ currentYear }} 疯狂的狮子Li All Rights Reserved.');
    }
  });
});

describe('layout and default settings invariants', () => {
  it('retains theme-aware sidebar home navigation in both collapse states', () => {
    const source = read('../layout/components/Sidebar/Logo.vue');
    expect(source.match(/to="\/"/g)).toHaveLength(2);
    for (const fragment of ['v-if="collapse"', 'mode="out-in"', 'animateConfig.logoAnimate.enter',
      'settingsStore.sideTheme', 'NavTypeEnum.TOP', 'var(--app-text-title)']) expect(source).toContain(fragment);
  });

  it('retains card surfaces and theme variables without fabricated business metrics', () => {
    const source = read('./index.vue');
    for (const fragment of ['class="home"', 'hero-panel', 'section-card', 'var(--app-surface-bg)', 'var(--app-text-title)']) {
      expect(source).toContain(fragment);
    }
    expect(source).not.toMatch(/收益|营收|利润|销售额|成交额|官方授权|背书/);
  });

  it('preserves settings unrelated to the brand title', async () => {
    const { default: settings } = await import('../settings');
    expect(settings).toMatchObject({ theme: '#409EFF', sideTheme: 'theme-dark', showSettings: true,
      tagsView: true, tagsViewPersist: false, tagsIcon: true, fixedHeader: true, sidebarLogo: true,
      dynamicTitle: true, animationEnable: false, dark: false, size: 'default', radiusBase: 14, fullHeightTable: true });
  });
});
