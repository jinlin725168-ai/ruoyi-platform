# ruoyi-platform 底座摸底文档（foundation）

- 基线版本：**1.0.7**（取自 `.storyloop/baseline.json` 的 `baseline_version`，对应 `main` 分支提交 `363a5d397`，即 BASE-20260923-001 之后）。
- 后端 `backend/`：RuoYi-Vue-Plus 6.X，以 git subtree 引入。Maven `revision` 为 6.0.0，技术栈为 Spring Boot 4.1、JDK 21、Sa-Token 1.45、MyBatis-Plus 3.5.17（另有 mybatis-plus-join）、Redisson、MapStruct-Plus、Fesod（EasyExcel 的后继）、Warm-Flow、LiteFlow 和 SnailJob。
- 前端 `frontend/`：plus-ui 6.X-Vue，以 git subtree 引入。技术栈为 Vue 3.5、TypeScript 6、Element Plus 2.14、Vite 8、Pinia 和 vxe-table，包管理用 pnpm 10。
- 本仓库自建的部分：`acceptance/`（代理指南、冒烟执行器、客户端和 UI 回归资产）、`sql/biz/`（业务增量 SQL）、`infra/`（本地 MySQL 和 Redis 容器）、`openspec/`（活规格和变更归档）。

本目录只记录底座的现状，以及怎样在底座上扩展。各角色必须遵守的规则写在 `acceptance/AGENT_GUIDE.md`。本文档与 AGENT_GUIDE 或代码冲突时，以 AGENT_GUIDE 和代码为准，再通过 BASE 提案修正本文档。

## 文档索引

| 文档 | 内容 | 主要读者 |
|---|---|---|
| [modules.md](modules.md) | 顶层目录，Maven 与前端模块的职责，依赖方向，可变区与集成点 | 所有角色 |
| [architecture.md](architecture.md) | 启动顺序；配置键与运行档；请求管线（认证、权限、校验、加解密、异常）；数据访问、缓存、调度；前端运行时 | implement、review |
| [extension.md](extension.md) | 端到端新增业务功能：每层文件、SQL、菜单与权限、字典、前端、测试、自检清单，以及参考实现 | implement |
| [api.md](api.md) | 全部控制器路由和权限串，按模块分组 | smoke、implement |
| [capabilities.md](capabilities.md) | 底座已有功能，以及 `openspec/specs/` 活规格的摘要 | 产品、需求分析 |
| [building-blocks.md](building-blocks.md) | 可复用的后端类、注解、工具，前端 hooks、组件、工具，验收客户端与冒烟工具 | implement、smoke |
| [testing.md](testing.md) | 单元测试、类型检查、冒烟、UI 回归的布局和运行方式，标签，默认跳过项 | implement、smoke |

## 使用方式

1. 先确定改动落在哪里：查 `modules.md` 的可变区。可变区只有 `backend/ruoyi-modules/**`、`frontend/src/**`、`frontend/public/**` 和 `sql/biz/**`。其余都是底座，需要改时写进 questions 或 summary，由外部流程转成 BASE 提案。
2. 新增业务功能：按 `extension.md` 的步骤做。单表功能复制 `org.dromara.biz.supplier`；主子表加状态流转的功能复制 `org.dromara.biz.purchase`。
3. 写冒烟用例：先读 `testing.md` 和 `api.md`，后端用例用 `acceptance/tools/ruoyi_client.py`，UI 用例的定位器复用 `acceptance/ui/<capability>/`。
4. 引用配置时只写键名和文件位置。本目录不抄录任何配置值、口令、密钥或连接串，它们都在原文件里。

## 与常见 RuoYi-Vue-Plus 资料不同的地方（容易踩坑）

- **没有多租户。** 底座没有 `ruoyi-common-tenant`，表里没有 `tenant_id`，也没有 `/auth/tenant/list` 路由。但 `ruoyi_client.Client.login()` 和现有冒烟 spec 仍在登录体里带 `tenantId`，后端会忽略它。`ruoyi_smoke.py` 的就绪探测地址也是 `/auth/tenant/list`，之所以能用，是因为 `smoke_harness.wait_http` 收到任意 HTTP 响应就算就绪。
- **分页返回 `PageResult<T>`。** 类型是 `org.dromara.common.core.domain.PageResult`，字段为 `rows` 和 `total`。控制器返回 `R<PageResult<XVo>>`，所以 JSON 形如 `{code,msg,data:{rows,total}}`，不是旧版 `TableDataInfo` 那样把 rows 放在顶层。
- **`BaseEntity` 没有 `params` 和 `searchValue`。** 它只有 `createDept/createBy/createTime/updateBy/updateTime`。需要日期区间这类额外参数时，在 BO 里自己声明 `Map<String,Object> params`（见 `BizPurchaseOrderBo`）。
- **接口加密和验证码默认打开。** `application.yml` 里 `api-decrypt.enabled` 和 `captcha.enable` 默认都开，`/auth/login` 带 `@ApiEncrypt`。只有 smoke 运行档（`application-smoke.yml`）关闭它们；UI 冒烟再由执行器向 vite 注入 `VITE_APP_ENCRYPT=false`。
- **生成器的菜单 SQL 模板列不全。** `ruoyi-gen` 的 `fm/sql/mysql.sql.ftl` 在 `sys_menu` 上缺少 `query_param/active_menu/ext` 三列。业务 SQL 以 `sql/biz/FEAT-20260918-001.sql` 的完整列清单为准。
- **业务接口不在接口文档分组里。** `springdoc.group-configs` 不包含 `org.dromara.biz`，这是底座配置。
- **唯一键冲突返回 `code=409`。** `DuplicateKeyException` 由 `MybatisExceptionHandler` 统一处理，结果是 409 而不是 500。需要可读提示时，先在 Service 里校验（如 `checkCodeUnique`），或者捕获 `DuplicateKeyException`（见 `BizPurchaseOrderServiceImpl.insertWithGeneratedOrderNo`）。
- **手写 SQL 不过滤逻辑删除。** 逻辑删除条件由 MyBatis-Plus 全局开关加实体上的 `@TableLogic` 自动追加；Mapper XML 里的手写 SQL 不会追加。
- **权限在登录时固化。** 权限写进 `LoginUser.menuPermission`，给测试用户新分配角色或菜单后，要重新登录才生效。超级管理员（角色 key 为 `superadmin`）直接拥有 `*:*:*`。
- **前端弹窗提示的写法。** 现有业务页用 `import modal from '@/plugins/modal'` 加上 `@/hooks/**` 里的组合函数。AGENT_GUIDE 提到的 `proxy?.$modal` 也能用，但新页面应与 `views/biz/*` 保持一致。
- **测试默认不跑。** `ruoyi-biz` 目前没有任何 `src/test`。父 pom 默认 `maven.test.skip=true`，surefire 只运行带 `@Tag(<profiles.active>)`（默认 `dev`）的测试类。
- **纯单测里不能直接用 `MapstructUtils`。** 它在类初始化时从 Spring 容器取 `Converter`，没有 Spring 上下文的 Mockito 测试一旦触发它的类加载就会失败，详见 `testing.md`。
