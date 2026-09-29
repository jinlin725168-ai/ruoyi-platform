# 测试与验收基础设施

对应底座版本：1.0.19，生成日期：2026-09-28

StoryLoop 的层级（`acceptance/storyloop-settings.json` 与 `.storyloop/config.json` 的 `profile`）依次为：单元（`unit_commands`）、集成（`integration_commands`）、检查（`check_commands`）、变更验收（`acceptance/changes/<id>/manifest.json`）、系统冒烟（`acceptance/smoke/manifest.json`）。每层单独给出结论，任何一层红都不能通过。`test_roots` 为 `backend/**/src/test/**` 和 `frontend/src/**/*.test.ts`，供特征化门识别测试文件。

## 一、单元与集成测试

### 相关配置

- `backend/pom.xml`：
  - 属性 `maven.test.skip=true`：默认连测试编译都跳过，运行测试时要同时传 `-Dmaven.test.skip=false -DskipTests=false`。
  - surefire 3.5.5：`groups=${profiles.active}`（默认 profile 为 dev，所以只运行 `@Tag("dev")`），`excludedGroups=exclude`。
- `backend/ruoyi-modules/pom.xml`：
  - 给所有业务模块加 test 作用域的 `spring-boot-starter-test`（JUnit 5、Mockito、AssertJ）。
  - failsafe 3.5.6：`includes` 为 `**/integration/**/*IT.java`，`groups=${profiles.active}`。没有绑定 execution，只能显式调用 `failsafe:integration-test failsafe:verify`，并且要传 `-DskipITs=false`。

### 位置与命名（AGENT_GUIDE）

| 类型 | 位置 | 命名 | 约束 |
|---|---|---|---|
| 单元 | `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/<feature>/` | `*Test` | `@Tag("dev")`；用 Mockito 隔离 Mapper；不起 Spring 上下文 |
| 特征化 | 同一单元测试包 | `<Class>CharacterizationTest` | 只断言必须不变的行为（会扩展的列表用 contains 断言）；必须在当前代码上跑绿；只写 `src/test` |
| 集成 | `.../org/dromara/biz/<feature>/integration/` | `*IT` | 也要 `@Tag("dev")`；可以起 Spring 上下文或连真实数据库 |

### 现状

- `ruoyi-biz` 的单元测试类：
  - supplier：`BizSupplierServiceImplCharacterizationTest`、`BizSupplierCategoryLookupTest`、`BizSupplierNameConditionTest`、`BizSupplierCodeConditionTest`。
  - purchase：`BizPurchaseOrderServiceImplCharacterizationTest`、`BizPurchaseOrderSaveCharacterizationTest`、`BizPurchaseOrderSupplierCategoryTest`、`BizPurchaseOrderSupplierNameConditionTest`、`BizPurchaseOrderRemarkTest`。
- `ruoyi-admin/src/test/java/org/dromara/test/`：上游示例 `DemoUnitTest`、`ParamUnitTest`、`TagUnitTest`、`AssertUnitTest`。dev 下只有带 dev 标签的方法会运行。
- **还没有任何 `*IT`**。集成命令目前是空跑，此后多个变更都经过了这一层。[待确认] 集成测试怎样连接数据库或 Redis（用哪个运行档、连本地 infra 还是临时库），目前没有先例。

### 运行命令（来自 settings 与 AGENT_GUIDE）

- 单元层：`mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test`，通过 `-am` 带上 `ruoyi-biz` 等全部依赖模块。
- 单独运行一个类：`mvn -q -o -f backend/pom.xml -pl ruoyi-modules/ruoyi-biz -Dmaven.test.skip=false -DskipTests=false -Dtest=<Class> -Dsurefire.failIfNoSpecifiedTests=false test`。
- 集成层：`mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -DskipITs=false -pl ruoyi-modules/ruoyi-biz failsafe:integration-test failsafe:verify`。
- 编译：`mvn -q -o -f backend/pom.xml -pl ruoyi-admin -am compile`。

### 纯单元测试的写法（已在 `BizPurchaseOrderRemarkTest` 验证）

- 类上加 `@Tag("dev") @ExtendWith(MockitoExtension.class)`，需要时加 `@MockitoSettings(strictness = Strictness.LENIENT)`。用 `@Mock` 模拟 Mapper、`DictService`、`IBiz*Service`，用 `@InjectMocks` 注入 ServiceImpl。
- **`LambdaQueryWrapper` 解析列名**：在 `@BeforeAll` 里调用 `TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), Entity.class)`。
- **`MapstructUtils` 在类初始化时从 Spring 取 `Converter`**：
  - 在 `@BeforeAll` 里尝试 `SpringUtil.getBeanFactory()`；失败时新建 `DefaultListableBeanFactory`，注册一个 mock 的 `Converter`，再调用 `new SpringUtil().postProcessBeanFactory(factory)`。
  - 每个用例用 `mockStatic(MapstructUtils.class)` 指定 convert 的结果，在 `@AfterEach` 里关闭。
- **断言写库参数**：用 `ArgumentCaptor` 捕获 `updateById` 或 `insert` 的实体。断言查询条件时，可以捕获 wrapper，检查 `getSqlSegment()` 和 `getParamNameValuePairs()`。
- **校验注解**：用 `Validation.buildDefaultValidatorFactory().getValidator().validateValue(Bo.class, "field", value, AddGroup.class)`。
- **`LoginHelper`** 依赖 Sa-Token 上下文，要避开或者 mock。

## 二、前端测试

- **框架**：vitest 4.1.11（devDependency）。没有独立的 vitest 配置文件，vitest 读取 `vite.config.ts`，`@/` 别名和 auto-import 都能用；`package.json` 里没有 `test` 脚本。
- **缺什么**：没有 `@vue/test-utils` 和 jsdom，所以不写组件测试。页面只能用 `import source from './index.vue?raw'` 对源码做包含式断言（见 `views/biz/purchaseOrder/index.test.ts`）。
- **位置**：放在源码旁边，命名 `<name>.test.ts`。现有 `api/biz/supplier/types.test.ts`、`api/biz/supplier/query.test.ts`、`views/biz/purchaseOrder/index.test.ts`、`views/biz/purchaseOrder/remarkOrder.test.ts`。
- **运行**：
  - 单个文件：`pnpm --dir frontend exec vitest run <file>`。
  - 单元层：`python3 acceptance/tools/frontend_unit.py`。它把候选副本同步到 `$TMP/storyloop-ruoyi-smoke`（与冒烟共用 node_modules），再运行 `vitest run --passWithNoTests --reporter=dot`。退出码：0 绿，1 有失败，2 环境错误（例如 scratch 里没有 node_modules）。
- **检查层**：`python3 acceptance/tools/frontend_check.py`，依次运行 `oxlint src` 和 `vue-tsc --noEmit`。vue-tsc 只对 `src/views/biz/**`、`src/api/biz/**` 和 `*.test.ts` 里的错误判失败，上游错误只计数（BASE-20260923-006）。
- **手动**：`pnpm --dir frontend lint`（oxlint）、`pnpm --dir frontend fmt`（oxfmt）。

## 三、验收

### 静态检查层（`check_commands`，每轮都跑）

| 命令 | 检查内容 |
|---|---|
| `mvn -q -o -f backend/pom.xml -pl ruoyi-modules/ruoyi-biz spotless:check` | `src/main/java` 和 `src/test/java`：未用 import、import 顺序（`java,javax,jakarta,org,com,`）、尾随空白、文件末尾换行、4 空格缩进。`spotless:apply` 可一键修复 |
| `mvn -q -o -f backend/pom.xml -pl ruoyi-modules/ruoyi-biz checkstyle:check` | `backend/ruoyi-modules/checkstyle-biz.xml`，包含测试源码：无 tab；单行不超过 160 字符；星号导入只允许 `org.springframework.web.bind.annotation`；命名规则；`NeedBraces`；`EmptyCatchBlock`；不能 catch `Throwable` 或 `Error`；`MissingSwitchDefault` 等 |
| `python3 acceptance/tools/frontend_check.py` | oxlint 加业务文件的 vue-tsc |
| `gitleaks detect --no-git --source . --config .gitleaks.toml --redact --exit-code 1` | 密钥扫描。`.gitleaks.toml` 只豁免上游的 `application*.yml`、`ruoyi-demo`、`frontend/.env.*`、`.storyloop`、构建产物；业务代码不豁免 |

### 冒烟执行器（`acceptance/tools/ruoyi_smoke.py`，在仓库根目录运行）

1. 检查 `mvn`、`java`、`docker` 在 PATH 上；有 spec 时还要 `pnpm` 和 `node`。
2. 用 `sync_scratch` 把 git 可见文件同步到 `$TMP/storyloop-ruoyi-smoke`，保留构建产物以支持增量构建。
3. 在 scratch 里执行 `mvn -q -o -f backend/pom.xml -DskipTests -pl ruoyi-admin -am package`，日志为 `smoke-build.log`。
4. 通过 `docker exec` 在容器 `ruoyi-mysql` 里建库 `ry_smoke_<pid>`，依次导入 `backend/script/sql/ry_vue.sql`、`ry_workflow.sql`，再按文件名导入 `sql/biz/*.sql`。
5. 启动 `java -jar ruoyi-admin.jar --spring.profiles.active=dev,smoke`，用随机端口、临时库 url 和独立的 Redis 库索引（执行器参数 `--redis-db` 的默认值）。就绪探测 `wait_http`，超时由 `--boot-timeout` 决定。
6. 用 unittest 运行 Python 用例，环境变量有 `SMOKE_BASE_URL`，`PYTHONPATH` 指向 `acceptance/tools`。
7. 有 spec 时：执行 `pnpm install --offline --frozen-lockfile`；启动 vite（`--mode development`，设置 `VITE_PROXY_TARGET`、`VITE_APP_ENCRYPT=false`、`VITE_APP_MESSAGE_ENABLED=false`）；把生成的 `*.d.ts` 备份到 `smoke-dts/`；最后运行 `playwright test -c acceptance/tools/playwright.config.ts`（环境变量 `SMOKE_UI_URL`、`SMOKE_OUTPUT_DIR`）。
8. 停止进程，删除临时库。

- 退出码：0 通过；1 行为失败；2 环境错误。
- 容器名、MySQL 账号与端口、Redis 库索引都可以通过执行器参数覆盖，默认值见脚本 `main()`，这里不抄录。
- 本地运行前先 `docker compose -f infra/docker-compose.yml up -d`。

### 变更验收与系统冒烟

- **变更验收**：`acceptance/changes/<change-id>/manifest.json` 加 `test_*.py` 和 `*.spec.ts`，是本次变更的合同，实现角色不能改。命令统一为 `["{python}", "acceptance/tools/ruoyi_smoke.py", "<suite_root>/test_x.py", "<suite_root>/x.spec.ts"]`；`timeout_seconds` 至少 900，现有的都是 2400；`criteria` 对应规格里的场景 ID。
- **系统冒烟**：`acceptance/smoke/manifest.json` 目前只有一条 `system-purchase-order-supplier-category`，运行 `acceptance/smoke/purchase-order/` 下的两个文件，条目多一个 `description`。由 smoke-propose / smoke-apply 维护。
- `acceptance/smoke/FEAT-20260918-001`、`FEAT-20260920-001`、`FEAT-20260921-001`、`FEAT-20260923-001` 是改名前的变更验收套件（当时的目录就是 `acceptance/smoke/<id>/`），引擎仍按各自变更识别它们，只在 `storyloop ci --change <id>` 重跑该变更时执行；它们不属于系统冒烟，也不会被任何变更的闭环再次运行。
- **用例约定**：
  - 后端用例：`from ruoyi_client import Client`，`Client().login()`。成功 `code == 200`，未登录 401，无权限 403，业务失败 500，唯一键冲突 409。
  - 前端用例：登录页 `/login`，默认账号见 AGENT_GUIDE，页面路径与菜单 path 一致，`page.goto` 用相对路径。
  - 用例必须在功能缺失时失败，但环境问题要交给执行器报告为退出码 2。
- **UI 回归资产**：`acceptance/ui/<capability>/`，由 `ui_regression.py` 生成，不进任何门，作为写浏览器用例时的参考。

## 四、回归命令

| 层 | settings 里的命令 | 实际跑到什么 |
|---|---|---|
| 单元 | `mvn ... -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test` | admin、common、api、全部业务模块里带 `@Tag("dev")` 的 `*Test`：`ruoyi-biz` 的 9 个类，加上 admin 示例里的 dev 方法 |
| 单元 | `{python} acceptance/tools/frontend_unit.py` | `frontend/src/**/*.test.ts`，当前 4 个文件 |
| 集成 | `mvn ... -DskipITs=false -pl ruoyi-modules/ruoyi-biz failsafe:integration-test failsafe:verify` | `ruoyi-biz` 里 `**/integration/**/*IT.java` 中带 dev 标签的类，目前为 0 个 |
| 检查 | spotless、checkstyle（只查 `ruoyi-biz`）、`frontend_check.py`、gitleaks | 见第三节 |
| CI（`.github/workflows/ci.yml`，同一套命令的在线版，不带 `-o`） | `backend` 作业：先 install，再跑单元、集成、spotless、checkstyle，最后 Trivy（有修复版本的 HIGH/CRITICAL 阻断，SARIF 上传到 Security 标签页）。`frontend` 作业：`frontend_unit.py --in-place`、`frontend_check.py --in-place`。`security` 作业：gitleaks，加 Semgrep（只扫 `ruoyi-biz`、`views/biz`、`api/biz`）。`smoke` 作业：compose 起中间件，再 `run_manifest.py acceptance/smoke/manifest.json` | 每次 push 到 main 和每个 PR |
| CodeQL（`codeql.yml`） | Java 与 JS/TS 的深度 SAST | 每周一次，另可手动触发，不阻挡 PR |

## 五、坑

- **默认被跳过的东西**：
  - 打包时（`-DskipTests` 或 `maven.test.skip=true`）跳过全部 Java 测试。
  - 不带 `@Tag("dev")` 的测试类，surefire 和 failsafe 都会**静默跳过**；prod、local、exclude 标签的测试和 `@Disabled` 的测试也不运行。
  - `*IT` 不放在 `integration` 包下时，failsafe 不会运行；放在那里又以 `Test` 结尾时，会被 surefire 当作单元测试运行。
  - 集成层不传 `-DskipITs=false` 时什么都不跑。
- **vitest 的 `--passWithNoTests`**：没有前端测试也是绿灯，这一层只对已有的测试把关。
- **vue-tsc 静默跳过**：`frontend_check.py` 在找不到 `auto-imports.d.ts` 时（从没启动过 vite 或冒烟）只打印提示、跳过类型检查，退出码仍然是 0。
- **离线构建**：所有闭环命令都带 `-o`。新的三方依赖、插件版本不在本地仓库时直接失败；spotless、checkstyle 插件也必须事先在本地仓库里。
- [待确认] 本地没有 gitleaks 可执行文件时，检查层会怎样判定，未验证。
- **仓库里没有 `.trivyignore`**：CI 注释提到可以用它登记例外，但目前没有任何例外；依赖漏洞要修，只能在根 pom 的安全版本覆盖里钉版本（BASE 迭代）。
- **`/auth/tenant/list` 探测**：底座没有多租户，这个路由不存在；它能当就绪探测，是因为收到任意 HTTP 响应（包括 404）都算就绪。
- **smoke 运行档关闭了验证码、接口加密、消息推送、SnailJob、Spring Boot Admin 和接口文档**，这些能力不在冒烟覆盖范围内。冒烟也不导入 `ry_job.sql`、`ry_ai.sql`。
- **权限在登录时固化**：给测试用户新分配角色或菜单后，要重新登录才生效。
- **WSL 下偶发 `Clock moved backwards`**（雪花 ID）：准备数据时应该稍等后重试。
- **规格里标注 `_manual acceptance_` 的场景**需要人工验收，例如打开导出的 Excel 核对。
