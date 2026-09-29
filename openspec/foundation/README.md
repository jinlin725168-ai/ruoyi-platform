# 底座知识库

对应底座版本：1.0.19，生成日期：2026-09-28，生成方式：storyloop survey（引擎以 survey 角色调用，只读摸底）。上一版对应 1.0.7（BASE-20260923-002），本版是刷新。

- 后端 `backend/`：RuoYi-Vue-Plus 6.X，以 git subtree 引入。Maven `revision` 为 6.0.0。技术栈为 Spring Boot 4.1.0、JDK 21、Sa-Token 1.45.0、MyBatis-Plus 3.5.17（另有 mybatis-plus-join）、Redisson、MapStruct-Plus、Fesod、Warm-Flow、LiteFlow、SnailJob（`backend/pom.xml` 的 `<properties>`）。
- 前端 `frontend/`：plus-ui 6.X，以 git subtree 引入。技术栈为 Vue 3.5、TypeScript 6、Element Plus 2.14、Vite 8、Pinia、vxe-table，另有 vitest 4.1.11 和 @playwright/test，包管理用 pnpm 10（`frontend/package.json`）。
- 本仓库自建的部分：`acceptance/`（代理指南、冒烟与检查执行器、验收客户端、系统冒烟、变更验收、UI 回归资产）、`sql/biz/`（业务增量 SQL）、`infra/`（本地 MySQL 和 Redis 容器）、`openspec/`（活规格、变更归档、本知识库）、`.github/workflows/`（CI 与 CodeQL）。

本知识库只记录底座现状，以及怎样在底座上扩展。各角色必须遵守的规则写在 `acceptance/AGENT_GUIDE.md`。本文档与 AGENT_GUIDE 或代码冲突时，以 AGENT_GUIDE 和代码为准，再通过 BASE 提案修正本文档。

## 怎么用

- product：先看 `capabilities.md`，避免重复建设；修改既有需求时沿用活规格里的旧 Requirement 标题。
- implement：先看 `extension.md` 和 `building-blocks.md`；测试写法和运行命令看 `testing.md`。
- characterize：先看 `testing.md` 第一节（特征化测试的位置、命名与 MapstructUtils 的处理）。
- smoke / acceptance：先看 `testing.md` 和 `building-blocks.md` 第三节的验收客户端；接口路径和权限串看 `api.md`。
- review：对照 `extension.md`（文件清单、禁止事项）和 `building-blocks.md`（有没有重复实现）。

## 文档索引

| 文档 | 一句话用途 |
|---|---|
| [modules.md](modules.md) | 顶层目录、Maven 模块与前端目录的职责，依赖方向，可变区、集成点和受保护路径 |
| [architecture.md](architecture.md) | 技术栈版本、启动过程、一个请求从进入到返回的每个环节、数据访问、缓存与调度、前端运行机制、配置键位置 |
| [extension.md](extension.md) | 新增一个业务表功能要创建或修改的全部文件、菜单与权限、前端页面、修改既有功能、代码生成器、禁止事项、参考实现 |
| [api.md](api.md) | 接口约定，业务接口与上游系统接口的路由、权限串、实现类，前端 api 封装 |
| [capabilities.md](capabilities.md) | 上游自带能力，本仓库已实现的能力（以 `openspec/specs/*/spec.md` 为准），能力之间的依赖 |
| [building-blocks.md](building-blocks.md) | 应复用的后端类与服务、前端 hooks 与组件、验收工具，以及「别自己写」清单 |
| [testing.md](testing.md) | 单元、集成、检查、前端单元、变更验收、系统冒烟、CI 各层的位置和运行命令，默认被跳过的东西，已知的坑 |

## 1.0.7 以来的底座变化（本次刷新的原因）

- 测试分层（BASE-20260923-004）：StoryLoop 配置拆成 `unit_commands`、`integration_commands`、`check_commands`，另有 `test_roots`。`backend/ruoyi-modules/pom.xml` 加了 failsafe，只跑 `**/integration/**/*IT.java`。
- 检查层（BASE-20260923-005、-006）：`ruoyi-biz` 上的 spotless 与 checkstyle（`backend/ruoyi-modules/checkstyle-biz.xml`），`acceptance/tools/frontend_check.py`（oxlint 加 vue-tsc；vue-tsc 只对业务文件判失败），gitleaks（`.gitleaks.toml`）。`backend/ruoyi-modules/ruoyi-biz/pom.xml` 从此成为集成点。
- 前端单元层（BASE-20260928-001）：`acceptance/tools/frontend_unit.py` 在 scratch 里跑 vitest，已进入 `unit_commands`。
- CI（BASE-20260923-007、BASE-20260924-001 至 -005）：`.github/workflows/ci.yml` 有 backend、frontend、security、smoke 四个作业，另有每周运行的 `codeql.yml`。Trivy 发现有修复版本的 HIGH/CRITICAL 依赖漏洞时阻断合入；两个 workflow 文件都是受保护路径。
- 依赖版本覆盖（BASE-20260924-004）：`backend/pom.xml` 的 `dependencyManagement` 开头钉住了 netty、tomcat、httpcore5、postgresql、commons-beanutils、bouncycastle 的修复版本。
- 验收分成两类：变更验收在 `acceptance/changes/<change-id>/`，项目级系统冒烟在 `acceptance/smoke/manifest.json`（由 smoke-propose / smoke-apply 维护）。
- 业务侧：供应商增加了按编码查询，名称查询改为去首尾空白且不区分大小写；采购单增加了供应商分类的展示、筛选和导出，按供应商名称查询，以及备注；`ruoyi-biz` 已有 9 个单元测试类，前端已有 4 个 vitest 文件。

## 容易踩坑（与常见 RuoYi-Vue-Plus 资料不同的地方）

- **没有多租户**：没有 `ruoyi-common-tenant`，表里没有 `tenant_id`。`ruoyi_smoke.py` 的就绪探测地址 `/auth/tenant/list` 能用，只是因为 `smoke_harness.wait_http` 收到任意 HTTP 响应就算就绪。
- **分页返回 `PageResult<T>`**：JSON 形如 `{code,msg,data:{rows,total}}`，不是旧版 `TableDataInfo` 那样把 rows 放在顶层（`org.dromara.common.core.domain.PageResult`）。
- **`BaseEntity` 没有 `params`**：需要日期区间时，在 BO 里自己声明 `Map<String,Object> params`（见 `BizPurchaseOrderBo`）。
- **接口加密和验证码默认打开**：只有 smoke 运行档（`application-smoke.yml`）关闭它们。
- **生成器菜单 SQL 模板缺列**：`fm/sql/mysql.sql.ftl` 缺 `query_param/active_menu/ext`，以 `sql/biz/FEAT-20260918-001.sql` 的列清单为准。
- **唯一键冲突返回 code=409**（`MybatisExceptionHandler`）。
- **手写 XML 不过滤逻辑删除**：`BizSupplierMapper.xml` 就是有意利用这一点，查询已删除供应商的分类。
- **测试默认不跑**：父 pom 默认 `maven.test.skip=true`；surefire 与 failsafe 都只运行带 `@Tag(<profiles.active>)`（默认 `dev`）的类，没打标签的类会被静默跳过。
- **纯单元测试里的 `MapstructUtils` 和 `LambdaQueryWrapper`**：要手动提供 Spring 的 `Converter`，并初始化 `TableInfoHelper`，写法见 `BizPurchaseOrderRemarkTest`（`testing.md` 有详细说明）。
- **`ruoyi-biz/pom.xml` 已是集成点**：需要新的 common 模块依赖时，写进 questions 或 summary，走 BASE 提案，不要自己改。
- **`updateById` 会跳过 null 字段**：要清空某个字段，必须写空串（见 `BizPurchaseOrderServiceImpl.updateByBo` 对 remark 的处理）。

## 已知空白（[待确认] 汇总）

- 仓库里还没有任何 `*IT` 集成测试。集成测试怎样拿到数据库或 Redis（起 Spring 上下文时的数据源、profile 和端口）没有先例，第一个写集成测试的变更要自己验证（testing.md）。
- 本地环境没装 gitleaks 时，StoryLoop 检查层会怎样判定，未验证（testing.md）。
- `acceptance/smoke/FEAT-*` 这四个按变更划分的旧冒烟目录已不在系统冒烟清单里，它们是否还会被某个流程使用，未确认（testing.md）。
- 仓库里没有 `.trivyignore`。CI 注释提到可以用它登记例外，但目前没有任何例外（testing.md）。
- `frontend_check.py` 在找不到 unplugin 声明文件时会跳过 vue-tsc，只打印提示。在从没跑过冒烟的新环境里，类型检查实际上没有执行（testing.md）。

## 什么时候刷新

底座版本变化时刷新：上游 subtree 同步，或者某个 BASE 迭代改变了模块、机制、测试分层、检查或 CI。普通功能变更合入后，`capabilities.md` 和 `api.md` 会稍有滞后，但活规格 `openspec/specs/` 始终是准的；累积几个变更后再刷新即可。
