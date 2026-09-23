# 测试与验收基础设施

## 分层总览

| 层 | 位置 | 由谁写 | 何时运行 |
|---|---|---|---|
| 后端单元测试 | `backend/ruoyi-modules/<module>/src/test/java/...`（业务放在 `ruoyi-biz/src/test/java/org/dromara/biz/<feature>/`）；上游示例在 `backend/ruoyi-admin/src/test/java/org/dromara/test/` | implement 角色（先写测试） | 回归命令 `test_commands`，本地单独运行 |
| 前端单元测试 | 源码旁边的 `frontend/src/**/<name>.test.ts` | implement 角色（只测纯函数和 api 封装） | 手动运行 vitest，没有接入回归 |
| 类型检查 | 整个 `frontend/src` | implement 自检 | 手动运行 `vue-tsc` |
| 冒烟（外部验收） | `acceptance/smoke/<change-id>/`：`manifest.json`、`test_*.py`、`*.spec.ts` | smoke 角色 | StoryLoop 按 manifest 运行，每条命令都会重新构建并启动后端 |
| UI 回归资产 | `acceptance/ui/<capability>/`：`plan.md`、`*.spec.ts` | `ui_regression.py`（Playwright Test Agents） | 按需运行；不进入冒烟 |
| 执行器自检 | `acceptance/tools/selftest_backend.py`、`selftest_ui.spec.ts` | 底座 | 验证执行器环境时手动运行 |

## 后端单元测试

### 相关配置（`backend/pom.xml`）

- `maven.test.skip=true`：默认连测试编译都跳过，所以运行测试时必须同时传 `-Dmaven.test.skip=false -DskipTests=false`。
- surefire 的 `groups=${profiles.active}`（默认 profile 是 dev，所以只运行 `@Tag("dev")`），`excludedGroups=exclude`。
- **没有打标签的测试类会被静默跳过。**
- 依赖：`ruoyi-modules/pom.xml` 给所有业务模块提供 test 作用域的 `spring-boot-starter-test`（JUnit 5、Mockito、AssertJ、Hamcrest）；`ruoyi-admin` 也有。

### 现状

- 只有 `ruoyi-admin` 里的上游示例：`DemoUnitTest`、`ParamUnitTest`、`AssertUnitTest`、`TagUnitTest`。
- 默认 dev 下实际只运行 `TagUnitTest.testTagDev`；BASE-20260923-001 的回归输出只有它的 BeforeEach/AfterEach 打印。
- 其余测试没打标签，或者是 prod、local、exclude 标签，或者带 `@Disabled`，都不会运行。
- `ruoyi-biz` 还没有任何测试。

### 运行命令

- 回归命令，即 `.storyloop/config.json` 和 `storyloop-settings.json` 的 `test_commands`：
  `mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test`
  它通过 `-am` 带上 `ruoyi-biz` 等依赖模块，所以业务模块里带 `@Tag("dev")` 的测试也会运行。
- 单独运行一个类：
  `mvn -q -o -f backend/pom.xml -pl ruoyi-modules/ruoyi-biz -Dmaven.test.skip=false -DskipTests=false -Dtest=<Class> -Dsurefire.failIfNoSpecifiedTests=false test`
- 只编译：`mvn -q -o -f backend/pom.xml -pl ruoyi-admin -am compile`。
- 所有命令都用 `-o` 离线模式，依赖只能来自本地 Maven 仓库，不要引入新的三方依赖。

### 写法约定

- 类上加 `@Tag("dev")`，用 `@ExtendWith(MockitoExtension.class)`、`@Mock`、`@InjectMocks`。
- 不启动 Spring 上下文：不用 `@SpringBootTest`，也不连数据库或 Redis。

### 静态依赖的注意事项

- `MapstructUtils` 的静态字段在类初始化时调用 `SpringUtils.getBean(Converter.class)`，没有 Spring 容器时会失败。所以凡是走到 `MapstructUtils.convert` 的路径（`insertByBo`、`updateByBo`），以及 `BaseMapperPlus` 的 `selectVo*` 默认方法，都要在单测里处理：
  - 被 mock 的 Mapper 的 `selectVo*` 直接 stub 返回值即可；
  - 纯业务规则（校验、计算、查询条件）最好放在不经过 `MapstructUtils` 的方法里测试；
  - 需要时可以用 Mockito 的 `mockStatic`。这一点在本仓库还没验证过，第一个这样写的变更要在 design 的 `## Tests First` 里记录结果。
- `LoginHelper` 依赖 Sa-Token 上下文，同样需要避开或者 mock。
- 断言 `LambdaQueryWrapper` 时，可以用 `ArgumentCaptor` 捕获 wrapper，再检查 `getSqlSegment()` 或 `getParamNameValuePairs()`。

## 前端单元测试与类型检查

- vitest 4.1.11 在 devDependencies 里，但没有 vitest 配置文件，没有 `test` 脚本，也没有任何现有测试。
- 没有 `@vue/test-utils` 和 jsdom，所以只测纯函数和 api 封装（api 封装可以对 `@/utils/request` 做 `vi.mock`）。
- vitest 默认读取 `vite.config.ts`，其中 `resolve.tsconfigPaths` 已打开，`@/` 别名应该能解析；auto-import 插件也会加载。第一次使用时要实际验证。
- 运行单个文件：`pnpm --dir frontend exec vitest run <file>`。
- 类型检查：`pnpm --dir frontend exec vue-tsc --noEmit`。
- lint 和格式化（可选）：`pnpm --dir frontend lint`（oxlint）、`pnpm --dir frontend fmt`（oxfmt）。

## 冒烟（smoke）

### manifest 格式（`acceptance/smoke/<change-id>/manifest.json`）

```
{"version": 1, "tests": [{"id": "<change-id>-<slug>", "criteria": ["A1", "A2"],
  "command": ["{python}", "acceptance/tools/ruoyi_smoke.py", "acceptance/smoke/<change-id>/test_x.py", "acceptance/smoke/<change-id>/x.spec.ts"],
  "timeout_seconds": 900}]}
```

- `criteria` 对应规格里的场景 ID。
- 一个变更尽量只用一条命令，因为每条命令都会重新构建和启动。
- `timeout_seconds` 至少 900；现有变更用的是 2400。

### 执行器流程（`acceptance/tools/ruoyi_smoke.py`，在仓库根目录运行）

1. **校验工具**：`mvn`、`java`、`docker` 必须在 PATH 上；有 spec 时还需要 `pnpm` 和 `node`。
2. **同步副本**：`sync_scratch` 把 git 可见的文件同步到 `$TMP/storyloop-ruoyi-smoke`，保留构建产物以支持增量构建。候选副本本身不会被写入。
3. **构建**：`mvn -q -o -f backend/pom.xml -DskipTests -pl ruoyi-admin -am package`，日志写到 scratch 里的 `smoke-build.log`。
4. **建临时库**：通过 `docker exec` 在容器 `ruoyi-mysql` 里建库 `ry_smoke_<pid>`，依次导入 `backend/script/sql/ry_vue.sql`、`ry_workflow.sql`，再按文件名导入 `sql/biz/*.sql`。
5. **启动后端**：`java -jar ruoyi-admin.jar --spring.profiles.active=dev,smoke --server.port=<随机端口> --spring.datasource.dynamic.datasource.master.url=<临时库> --spring.data.redis.database=<独立库索引>`。就绪探测为 `wait_http`，默认 180 秒；日志写到 `smoke-server.log`。
6. **运行 Python 用例**：用 unittest 按路径加载。环境变量有 `SMOKE_BASE_URL`，`PYTHONPATH` 指向 `acceptance/tools`，另有 `CI=1`。
7. **运行 spec**：
   - 在 scratch 的 frontend 里执行 `pnpm install --offline --frozen-lockfile`。
   - 启动 vite：`--mode development`，注入 `VITE_PROXY_TARGET`，另设 `VITE_APP_ENCRYPT=false`、`VITE_APP_MESSAGE_ENABLED=false`。日志写到 `smoke-vite.log`。
   - 运行 `playwright test -c acceptance/tools/playwright.config.ts <specs>`。额外的环境变量有 `SMOKE_UI_URL`、`SMOKE_OUTPUT_DIR`，同时也能读到 `SMOKE_BASE_URL`。
8. **清理**：停止 vite 和后端，删除临时库。

- **退出码**：0 表示通过，1 表示行为失败，2 表示环境错误（构建失败、建库失败、后端没起来等）。
- 执行器参数可以覆盖：`--mysql-container`、`--mysql-user`、`--mysql-password`、`--mysql-host-port`、`--redis-db`、`--boot-timeout`、`--scratch`。默认值见脚本。
- 本地手动运行：`python3 acceptance/tools/ruoyi_smoke.py acceptance/smoke/<id>/test_x.py [acceptance/smoke/<id>/x.spec.ts]`。需要先 `docker compose -f infra/docker-compose.yml up -d`。

### 用例约定（见 AGENT_GUIDE 和现有用例）

- **后端用例**：
  - 写 unittest，`from ruoyi_client import ApiError, Client`，`Client().login()` 之后调用接口。
  - 成功 `code == 200`，未登录 401，无权限 403，业务失败 500；唯一键冲突是 409。
  - 分页数据在 `data.rows` 和 `data.total`。
- **权限用例**：通过 `/system/role`（新增角色，带上 `menuIds`）和 `/system/user`（新增用户，带上 `roleIds`）准备只有部分权限的用户，然后用新 `Client` 登录。权限在登录时固化，改权限后要重新登录。
- **UI 用例**：
  - Playwright 用 `import { test, expect } from '@playwright/test'`；登录页是 `/login`，默认管理员账号见 AGENT_GUIDE。
  - 定位器：用户名输入框用 placeholder 匹配 用户名/username，密码框用 placeholder 匹配 密码/password，提交按钮是 `button.submit-button`；登录成功后 URL 为 `/index`。
  - 业务页面路径与菜单 path 一致，例如 `/biz/supplier`。
  - `page.goto` 一律用相对路径。
  - 优先复用 `acceptance/ui/<capability>/` 里已验证的定位器和文案。
- **现有用例的技巧**：
  - 用例在 UI 测试里先通过后端 API 准备数据（`fetch` 带上 `clientid` 头）。
  - 需要模拟接口无法产生的历史数据（例如分类为空的供应商）时，通过 `docker exec ruoyi-mysql mysql ...` 直接改临时库。当前库名可以从 `information_schema` 找到：用例是按包含 `supplier_category` 列的 `ry_smoke_*` 库定位的。
  - 雪花 ID 偶发 `Clock moved backwards`，准备数据时应该稍等后重试。
  - 字段名不绑定实现时，用候选别名探测。
- **可靠性要求**：用例必须在功能缺失时失败，但不能把环境错误伪装成行为失败。环境问题交给执行器报告为退出码 2。

### 流程生成物

- 冒烟的红灯和绿灯证据：`.storyloop/evidence/<id>/smoke-red.json`、`smoke-result.json`。
- 验收报告：`reports/storyloop/<id>/report.md`。

## UI 回归（`ui_regression`）

- 在 `.storyloop/config.json` 的 `ui_regression` 里配置：`{python} acceptance/tools/ui_regression.py --max-scenarios 3`，超时 7200 秒。
- 它启动与冒烟相同的栈，然后：planner 代理探索页面，写出 `plan.md`（如果 `acceptance/ui/<capability>/plan.md` 已存在就跳过）；generator 按场景生成 spec；healer 修复失败的 spec。只返回通过的 spec，由 StoryLoop 放到 `acceptance/ui/<capability>/`。
- 需要 `claude`、`npx`、`pnpm`、`mvn`、`java`、`docker`。
- 这些资产不进入冒烟门禁（BASE-20260922-001）。它们是写冒烟时的参考，也可以按需运行回归：`playwright test -c acceptance/tools/playwright.config.ts acceptance/ui/<capability>/...`，需要设置 `SMOKE_UI_URL`。

## 默认被跳过或未覆盖的内容

- 打包时（`-DskipTests` 或 `maven.test.skip=true`）跳过全部 Java 测试。
- 不带 `@Tag("dev")` 的测试类，以及 prod、local、exclude 标签的测试和 `@Disabled` 的测试，都不会运行。
- 前端没有接入任何自动测试，vitest 只在手动运行时执行。
- `acceptance/ui/**` 不在冒烟里运行。
- smoke 运行档关闭了验证码、接口加密、消息推送、SnailJob、Spring Boot Admin 客户端和接口文档，所以这些能力不在冒烟覆盖范围内。
- 冒烟不导入 `ry_job.sql` 和 `ry_ai.sql`。
- 规格里标注为 `_manual acceptance_` 的场景需要人工验收，例如 supplier A21、purchase-order A27（打开 Excel 核对）。
