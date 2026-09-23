# 模块与边界

## 顶层目录

| 目录 | 来源 | 分层 | 职责 |
|---|---|---|---|
| `backend/` | subtree RuoYi-Vue-Plus 6.X | 底座；其中 `ruoyi-modules/` 是可变区 | 后端 Maven 多模块工程 |
| `frontend/` | subtree plus-ui 6.X-Vue | 底座；其中 `src/`、`public/` 是可变区 | 管理端 SPA |
| `sql/biz/` | 本仓库 | 可变区 | 每个变更一个 `<change-id>.sql`，包含 DDL、字典和菜单 |
| `acceptance/` | 本仓库 | 底座（`smoke/`、`ui/` 由流程生成） | 代理指南、冒烟执行器、HTTP 客户端、Playwright 配置、UI 回归资产 |
| `openspec/` | 本仓库 | `specs/` 和 `changes/` 由流程生成；`foundation/` 为本文档 | 活规格、变更提案、设计与决策 |
| `infra/` | 本仓库 | 底座 | `docker-compose.yml`，定义容器 `ruoyi-mysql` 和 `ruoyi-redis` |
| `reports/storyloop/` | 流程生成 | — | 每个变更的验收证据报告 |
| `.storyloop/`（git 忽略） | 流程状态 | — | `config.json`、`baseline.json`、base-proposals、evidence、state |

- **可变区**（module_roots）：`backend/ruoyi-modules`、`frontend/src`、`frontend/public`、`sql/biz`。
- **集成点**（integration_paths，始终属于底座）：`backend/pom.xml`、`backend/ruoyi-admin/pom.xml`、`backend/ruoyi-api/pom.xml`、`backend/ruoyi-common/pom.xml`、`backend/ruoyi-common/ruoyi-common-bom/pom.xml`、`backend/ruoyi-modules/pom.xml`、`frontend/package.json`、`frontend/pnpm-lock.yaml`、`frontend/pnpm-workspace.yaml`。注意 `backend/ruoyi-modules/ruoyi-biz/pom.xml` 不在其中，它属于可变区。
- **scratch**：构建可以产生这些路径，不算越界。清单来自 `acceptance/storyloop-settings.json` 的 `scratch_paths`：`target/`、`node_modules/`、`dist/`、`logs/`、`__pycache__/`、`.flattened-pom.xml`、`frontend/src/types/auto-imports.d.ts`、`frontend/src/types/components.d.ts`。其他被 git 忽略的文件一律不要产生。
- `.storyloop/config.json` 的 `candidate_allow` 允许候选副本里出现 `frontend/.env.development` 和 `frontend/.env.production`，但它们仍然是底座。

## 后端 Maven 反应堆

`backend/pom.xml` 的 artifact 是 `ruoyi-vue-plus`，packaging 为 pom。

- **modules**：`ruoyi-admin`、`ruoyi-common`、`ruoyi-extend`、`ruoyi-modules`、`ruoyi-api`。
- **dependencyManagement**：统一声明全部内部模块（包括 `ruoyi-biz`）和三方版本；另外 import 了 Spring Boot、Spring AI、hutool、sa-token 和 `ruoyi-common-bom`。
- **Maven profiles**：`local`、`dev`（默认激活）、`prod`。它们只设置资源过滤变量 `profiles.active`、`logging.level` 和 `monitor.*`，过滤范围是 `application*`、`bootstrap*`、`banner*`。
- **插件**：
  - `maven-compiler-plugin`：release 21，注解处理器依次为 therapi-javadoc、lombok、spring-boot-configuration-processor、mapstruct-plus-processor、lombok-mapstruct-binding，编译参数带 `-parameters`。
  - `maven-surefire-plugin`：`groups=${profiles.active}`，`excludedGroups=exclude`。
  - `flatten-maven-plugin`：生成 `.flattened-pom.xml`。
- **默认跳过测试**：属性 `maven.test.skip=true`。

### ruoyi-admin（Web 入口，打包为 `ruoyi-admin.jar`）

- 入口 `org.dromara.DromaraApplication`（`@SpringBootApplication`）；war 部署用 `DromaraServletInitializer`。
- `org.dromara.web.controller`：
  - `AuthController`：`/auth/**`，类上 `@SaIgnore`。
  - `CaptchaController`：`/auth/code`、`/resource/sms/code`、`/resource/email/code`。
  - `IndexController`：`/`。
- `org.dromara.web.service`：
  - `SysLoginService`：登录校验、错误次数锁定、登录日志、构建 `LoginUser`。
  - `SysRegisterService`：注册。
  - `IAuthStrategy` 及实现 `PasswordAuthStrategy`、`SmsAuthStrategy`、`EmailAuthStrategy`、`SocialAuthStrategy`、`XcxAuthStrategy`。bean 名为 `<grantType>` + `IAuthStrategy.BASE_NAME`。
- `org.dromara.web.listener`：`UserLoginSuccessListener`、`UserActionListener`。
- 资源：`application.yml`、`application-dev.yml`、`application-prod.yml`、`application-smoke.yml`（本仓库新增）、`logback-plus.xml`、`i18n/messages*.properties`、`banner.txt`。
- 依赖：
  - 业务模块 `ruoyi-system`、`ruoyi-job`、`ruoyi-ai`、`ruoyi-demo`、`ruoyi-biz`、`ruoyi-workflow`；`ruoyi-gen` 通过默认激活的 profile `gen` 引入。
  - `ruoyi-api`。
  - `ruoyi-common-doc`、`ruoyi-common-social`、`ruoyi-common-mail`、`ruoyi-common-mcp`。
  - MySQL 驱动、Spring Boot Admin client，以及 test 作用域的 `spring-boot-starter-test`。
- 测试：`src/test/java/org/dromara/test/` 下的上游示例（`DemoUnitTest`、`ParamUnitTest`、`TagUnitTest`、`AssertUnitTest`）。

### ruoyi-api（跨模块接口，只依赖 ruoyi-common-core）

- `org.dromara.system.api`：
  - 接口：`UserService`、`DeptService`、`RoleService`、`PostService`、`ConfigService`、`OssService`、`MessageService`、`TaskAssigneeService`。
  - `model`：`LoginUser`、`PasswordLoginBody`、`SmsLoginBody`、`EmailLoginBody`、`SocialLoginBody`、`XcxLoginBody`、`RegisterBody`、`TaskAssigneeBody`、`XcxLoginUser`。
  - `domain`：`UserDTO`、`DeptDTO`、`RoleDTO`、`PostDTO`、`OssDTO`、`UserOnlineDTO`、`PushPayloadDTO`、`TaskAssigneeDTO`。
- `org.dromara.workflow.api`：
  - 接口 `WorkflowService`。
  - DTO：`StartProcessDTO`、`StartProcessReturnDTO`、`CompleteTaskDTO`、`FlowCopyDTO`、`FlowInstanceBizExtDTO`。
  - 事件：`ProcessEvent`、`ProcessTaskEvent`、`ProcessDeleteEvent`。
- 实现在哪里：
  - system 接口由 `ruoyi-system` 的 `Sys*ServiceImpl` 同时实现，例如 `SysUserServiceImpl implements ISysUserService, UserService`；`SysTaskAssigneeServiceImpl` 实现 `TaskAssigneeService`。
  - `WorkflowService` 由 `ruoyi-workflow` 的 `WorkflowServiceImpl` 实现。
  - `ruoyi-common-core` 里的 `DictService` 由 `SysDictTypeServiceImpl` 实现，`PermissionService` 由 `SysPermissionServiceImpl` 实现。

### ruoyi-common（BOM 加 24 个功能子模块）

| 模块 | 职责 | 关键类 |
|---|---|---|
| core | 通用域对象、常量、异常、工具、校验分组与校验注解 | `R`、`PageResult`、`ServiceException`、`SystemConstants`、`CacheNames`、`HttpStatus`、`DictService`、`PermissionService`、`MapstructUtils`、`StringUtils`、`StreamUtils`、`DateUtils`、`ValidatorUtils`、`SpringUtils`、`TreeBuildUtils`、`AddGroup/EditGroup/QueryGroup`、`@DictPattern`、`@EnumPattern`、`@Xss`、`ThreadPoolConfig` |
| mybatis | MyBatis-Plus 配置、Mapper 基类、分页、数据权限、自动填充 | `BaseEntity`、`BaseMapperPlus`、`LambdaCrudChainWrapper`、`PageQuery`、`QueryBuilder`、`LambdaQueryBuilder`、`LambdaJoinQueryBuilder`、`@DataPermission`、`@DataColumn`、`DataPermissionHelper`、`MybatisPlusConfig`、`InjectionMetaObjectHandler`、`MybatisExceptionHandler`、`IdGeneratorUtil` |
| web | 全局异常、过滤器、验证码、国际化、耗时拦截、控制器基类、响应增强 | `BaseController`、`GlobalExceptionHandler`、`FilterConfig`、`XssFilter`、`RepeatableFilter`、`CaptchaConfig`、`CaptchaProperties`、`PlusWebInvokeTimeInterceptor`、`ResponseEnhancementAdvice`、`I18nLocaleResolver` |
| satoken | Sa-Token 集成 | `LoginHelper`、`SaPermissionImpl`、`PlusSaTokenDao`、`SaTokenExceptionHandler`、`SaTokenConfig` |
| security | 路由拦截与放行 | `SecurityConfig`、`SecurityProperties`（键 `security.excludes`）、`AllUrlHandler` |
| redis | Redisson、Spring Cache、分布式锁、限流、防重复提交 | `RedisUtils`、`CacheUtils`、`QueueUtils`、`SequenceUtils`、`@RepeatSubmit`、`@RateLimiter`、`PlusSpringCacheManager`、`CaffeineCacheDecorator`、`RedisExceptionHandler`、`Lock4jConfig` |
| log | 操作日志注解与事件 | `@Log`、`BusinessType`、`OperatorType`、`LogAspect`、`OperLogEvent`、`LoginInfoEvent` |
| excel | Excel 导入导出（基于 Fesod） | `ExcelBuilder`、`@ExcelDictFormat`、`ExcelDictConvert`、`@ExcelEnumFormat`、`ExcelEnumConvert`、`@CellMerge`、`@ExcelRequired`、`@ExcelNotation`、`@ExcelDynamicOptions`、`DefaultExcelListener`、`ExcelResult`、`DropDownOptions` |
| translation | 响应字段翻译 | `@Translation`、`TransConstant`（user_id_to_name、user_id_to_nickname、dept_id_to_name、dict_type_to_label、oss_id_to_url） |
| sensitive | 响应脱敏 | `@Sensitive`、`SensitiveStrategy` |
| encrypt | 接口加解密、数据库字段加密 | `@ApiEncrypt`、`CryptoFilter`、`@EncryptField`、`EncryptorManager`、`EncryptUtils` |
| json | Jackson 配置、JSON 工具、字段增强管线 | `JsonUtils`、`JacksonConfig`、`BigNumberSerializer`、`JsonFieldProcessor`、`@JsonPattern` |
| doc | springdoc 加运行时 javadoc 的接口文档 | `SpringDocConfig` |
| oss | S3 兼容对象存储 | `OssFactory`、`OssClient` |
| push | SSE 与 WebSocket 消息推送 | `SseController`、`PushHelper`、`MessageProperties` |
| job | SnailJob 客户端 | `SnailJobConfig` |
| mail、sms、social | 邮件、短信（sms4j）、第三方登录（JustAuth） | `MailBuilder`、`SmsAutoConfiguration`、`SocialUtils` |
| liteflow | 规则编排基础组件 | `LiteFlowUtils` |
| elasticsearch、mqtt、ai、mcp | Easy-Es、mica-mqtt、Snail AI、Spring AI MCP | 大多默认关闭，见 `architecture.md` |
| bom | 内部 common 模块版本清单 | `ruoyi-common-bom/pom.xml` |

### ruoyi-modules（可变区；`ruoyi-modules/pom.xml` 本身是集成点）

`ruoyi-modules/pom.xml` 给所有子模块统一加了 test 作用域的 `spring-boot-starter-test`（JUnit 5、Mockito、AssertJ），这是 BASE-20260923-001 引入的。

| 模块 | 包 | 职责 | 路由前缀 |
|---|---|---|---|
| ruoyi-system | `org.dromara.system` | 用户、角色、菜单、部门、岗位、字典、参数、通知、客户端、OSS、社交账号、站内消息、在线用户、操作与登录日志、缓存监控；实现 ruoyi-api 的系统接口 | `/system/**`、`/monitor/**`、`/resource/oss/**`、`/resource/message/box` |
| ruoyi-workflow | `org.dromara.workflow` | Warm-Flow 工作流：分类、定义、实例、任务、SpEL 表达式、请假示例；用 LiteFlow 编排任务办理链（`resources/liteflow/*.el.xml`） | `/workflow/**` |
| ruoyi-gen | `org.dromara.gen` | 代码生成器：FreeMarker 模板在 `resources/fm/**`，默认值在 `generator.yml` | `/tool/gen/**` |
| ruoyi-demo | `org.dromara.demo` | 上游演示：单表 TestDemo、树表 TestTree、Excel、缓存、锁、限流、加密、脱敏、国际化、ES、MQTT、短信、邮件、MCP、WebSocket、批量操作 | `/demo/**`、`/es`、`/swagger/demo` |
| ruoyi-job | `org.dromara.job` | SnailJob 执行器示例 | 无 HTTP 路由 |
| ruoyi-ai | `org.dromara.ai` | Snail AI 用户注册接口 | `/snail-ai/**` |
| **ruoyi-biz** | `org.dromara.biz` | **StoryLoop 业务落点**：`supplier`（供应商）、`purchase`（采购单） | `/biz/**` |

`ruoyi-biz/pom.xml` 的依赖是 `ruoyi-api` 加上 `ruoyi-common-core/doc/redis/mybatis/log/excel/security/web/translation/sensitive/encrypt`。这个 pom 在可变区里，需要其他 common 模块（如 oss、push）时可以直接加依赖，不写版本，版本由 BOM 管。

### ruoyi-extend（独立应用，不打进 ruoyi-admin）

`ruoyi-monitor-admin`（Spring Boot Admin 服务端）、`ruoyi-snailjob-server`、`ruoyi-snailai-server`。dev 和 smoke 运行档都关闭了对应的客户端。

## 依赖方向

```
ruoyi-admin
  ├─> ruoyi-modules/{system, workflow, demo, job, ai, biz, gen(profile gen)}
  ├─> ruoyi-api
  └─> ruoyi-common-{doc, social, mail, mcp}
ruoyi-modules/*  ─> ruoyi-api + ruoyi-common-*   （业务模块之间互不依赖，已按各模块 pom 核对）
ruoyi-api        ─> ruoyi-common-core
ruoyi-common-*   ─> ruoyi-common-core（common 模块之间也有依赖，core 在最底层）
```

- 跨模块能力只能从两处获取：`ruoyi-api` 的接口，或 `ruoyi-common-core` 的 `DictService`、`PermissionService`。`ruoyi-biz` 不得依赖 `ruoyi-system` 的 Service 或 Mapper。
- 同在 `ruoyi-biz` 里的功能可以直接互相注入，例如 `BizPurchaseOrderServiceImpl` 注入了 `IBizSupplierService`。

## 前端（frontend/src）

| 目录 | 职责 |
|---|---|
| `api/<module>/<feature>/index.ts`、`types.ts` | 按后端路由组织的请求封装和类型。`api/types.ts` 定义 `PageResult` 和登录相关类型，`api/menu.ts` 提供 `getRouters` |
| `views/<module>/<feature>/index.vue` | 页面。`views/biz/**` 是业务页（`supplier`、`purchaseOrder`），其余来自上游 |
| `hooks/**` | 组合函数：`async/useLoading`、`dialog/useFormDialog`、`dialog/useDialogState`、`form/useSearchReset`、`form/useSearchToggle`、`form/useDateRangeQuery`、`table/useTableSelection`、`table/useTableSortQuery`、`table/useFullHeightTable`、`tree/useTreeTableExpand`、`tree/useTreeCollapsed` |
| `components/**` | 全局组件，由 unplugin-vue-components 自动注册（清单见 `building-blocks.md`） |
| `utils/**` | `request.ts`（axios 实例和 `download`）、`dict.ts`（`useDict`）、`ruoyi.ts`、`auth.ts`、`permission.ts`、`crypto.ts`、`validate.ts` 等 |
| `plugins/**` | `modal`、`tab`、`cache`、`download`、`auth`，由 `installPlugin` 挂到 `app.config.globalProperties`（`$modal` 等） |
| `directive/**` | `v-hasPermi`、`v-hasRoles`、`v-copyText` |
| `store/modules/**` | Pinia 仓库：`user`、`permission`（动态路由）、`dict`、`settings`、`tagsView`、`app`、`notice` |
| `router/index.ts` | 常量路由（登录、注册、404、首页、个人中心等）；业务路由不写在这里 |
| `permission.ts` | 全局路由守卫：拉取用户信息，生成动态路由 |
| `layout/**`、`assets/**`、`lang/**`、`types/**` | 布局；样式（含 `assets/styles/components/page-shell`）；i18n；全局类型（`types/global.d.ts`） |

前端里属于底座的文件：`package.json`、`pnpm-lock.yaml`、`pnpm-workspace.yaml`、`vite.config.ts`、`vite/plugins/**`、`.env.*`、`tsconfig.json`、`uno.config.ts`、`.oxlintrc.json`、`.oxfmtrc.json`、`gen/*.ftl`。

## acceptance/

- `AGENT_GUIDE.md`：各角色的约定，StoryLoop 通过 `--guide` 注入。
- `storyloop-settings.json`：module_roots、integration_paths、test_commands、candidate_allow、scratch_paths。
- `tools/`：`ruoyi_smoke.py`（冒烟执行器）、`smoke_harness.py`（通用机制）、`ruoyi_client.py`（HTTP 客户端）、`playwright.config.ts`、`ui_regression.py`、`playwright-agents/`、`selftest_backend.py`、`selftest_ui.spec.ts`。
- `smoke/<change-id>/`：每个变更的 `manifest.json` 和用例，由流程生成。现有 FEAT-20260918-001、FEAT-20260920-001、FEAT-20260921-001。
- `ui/<capability>/`：对着真实页面探索得到的 `plan.md` 和已验证的 Playwright 回归用例。目前只有 `supplier-management`。
