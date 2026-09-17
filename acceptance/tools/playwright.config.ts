// StoryLoop UI 冒烟配置：由 acceptance/tools/ruoyi_smoke.py 在 scratch 副本中调用。
// 所有输出写到 SMOKE_OUTPUT_DIR（scratch 内），绝不写回候选副本。
import { defineConfig } from '@playwright/test';
import path from 'node:path';

export default defineConfig({
  testDir: path.resolve(__dirname, '..'),
  outputDir: process.env.SMOKE_OUTPUT_DIR || path.resolve(__dirname, '../../../storyloop-ui-output'),
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  reporter: [['list']],
  use: {
    baseURL: process.env.SMOKE_UI_URL,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'off',
    video: 'off'
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }]
});
