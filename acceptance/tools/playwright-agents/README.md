# Playwright Test Agents 定义

由 `npx playwright init-agents --loop=claude`（Playwright 1.63）生成后拆出：`*.md` 是各代理的系统提示，`*.tools` 是其 MCP 工具清单，`mcp.json` 是 `playwright-test` MCP 服务配置。Playwright 升级后重新生成并覆盖这里的文件。

`ui_regression.py` 用它们驱动 `claude -p --restricted --mcp-config`，对着冒烟栈里跑起来的应用生成 `acceptance/ui/<capability>/` 下的回归资产。
