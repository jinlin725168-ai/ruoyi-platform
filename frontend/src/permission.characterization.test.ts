import { beforeEach, describe, expect, it, vi } from 'vitest';

const state = vi.hoisted(() => ({
  guard: undefined as unknown as (to: Record<string, unknown>, from: object) => Promise<unknown>,
  token: '', roles: [] as string[],
  settings: { dynamicTitle: true, title: '采购单', setTitle: vi.fn() },
  getInfo: vi.fn(), logout: vi.fn(), generateRoutes: vi.fn(), addRoute: vi.fn(),
  start: vi.fn(), done: vi.fn(), error: vi.fn(), relogin: { show: false }
}));
vi.mock('./router', () => ({ default: {
  beforeEach: (guard: typeof state.guard) => { state.guard = guard; }, afterEach: vi.fn(), addRoute: state.addRoute
} }));
vi.mock('nprogress', () => ({ configure: vi.fn(), start: state.start, done: state.done }));
vi.mock('element-plus/es', () => ({ ElMessage: { error: state.error } }));
vi.mock('@/store/modules/settings', () => ({ useSettingsStore: () => state.settings }));
vi.mock('@/store/modules/user', () => ({ useUserStore: () => ({ roles: state.roles, getInfo: state.getInfo, logout: state.logout }) }));
vi.mock('@/store/modules/permission', () => ({ usePermissionStore: () => ({ generateRoutes: state.generateRoutes }) }));
vi.mock('@/utils/auth', () => ({ getToken: () => state.token }));
vi.mock('@/utils/request', () => ({ isRelogin: state.relogin, isHandledRequestError: () => false }));

await import('./permission');

const target = (path: string) => ({ path, fullPath: `${path}?filter=mine`, meta: {},
  params: { id: 'fixture' }, query: { filter: 'mine' }, hash: '#details', name: 'PurchaseOrder' });

beforeEach(() => {
  vi.clearAllMocks();
  state.token = '';
  state.roles = [];
  state.relogin.show = false;
  state.getInfo.mockResolvedValue(undefined);
  state.logout.mockResolvedValue(undefined);
  state.generateRoutes.mockResolvedValue([]);
});

describe('permission guard invariants', () => {
  it.each(['/login', '/register', '/social-callback', '/register/team'])('allows anonymous public route %s', async path => {
    expect(await state.guard(target(path), {})).toBe(true);
    expect(state.getInfo).not.toHaveBeenCalled();
  });

  it('redirects anonymous users with the full encoded destination', async () => {
    const to = target('/biz/purchaseOrder');
    expect(await state.guard(to, {})).toBe(`/login?redirect=${encodeURIComponent(to.fullPath)}`);
    expect(state.generateRoutes).not.toHaveBeenCalled();
  });

  it('allows an authenticated non-admin role without regenerating routes', async () => {
    state.token = 'synthetic-session';
    state.roles = ['warehouse-reader'];
    expect(await state.guard(target('/biz/purchaseOrder'), {})).toBe(true);
    expect(state.getInfo).not.toHaveBeenCalled();
    expect(state.generateRoutes).not.toHaveBeenCalled();
  });

  it('installs internal dynamic routes and preserves navigation state after fetching identity', async () => {
    state.token = 'synthetic-session';
    const internal = { path: '/biz/purchaseOrder' };
    state.generateRoutes.mockResolvedValue([internal, { path: 'https://example.invalid/help' }]);
    const to = target(internal.path);
    expect(await state.guard(to, {})).toMatchObject({ path: to.path, replace: true,
      params: to.params, query: to.query, hash: to.hash, name: to.name });
    expect(state.getInfo).toHaveBeenCalledOnce();
    expect(state.addRoute.mock.calls).toEqual([[internal]]);
    expect(state.relogin.show).toBe(false);
  });

  it('logs out after identity failure and reports the error', async () => {
    state.token = 'synthetic-session';
    state.getInfo.mockRejectedValue(new Error('fixture identity unavailable'));
    expect(await state.guard(target('/index'), {})).toEqual({ path: '/' });
    expect(state.logout).toHaveBeenCalledOnce();
    expect(state.error).toHaveBeenCalledWith('fixture identity unavailable');
    expect(state.generateRoutes).not.toHaveBeenCalled();
  });

  it('redirects authenticated login visits to home', async () => {
    state.token = 'synthetic-session';
    expect(await state.guard(target('/login'), {})).toEqual({ path: '/' });
  });
});

describe('dynamic title switch invariant', () => {
  it('uses the default title when disabled and includes the page title when enabled', async () => {
    const { useDynamicTitle } = await import('./utils/dynamicTitle');
    const { default: settings } = await import('./settings');
    vi.stubGlobal('document', { title: '' });
    try {
      state.settings.dynamicTitle = false;
      useDynamicTitle();
      expect(document.title).toBe(settings.title);
      state.settings.dynamicTitle = true;
      useDynamicTitle();
      expect(document.title.startsWith('采购单 - ')).toBe(true);
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
