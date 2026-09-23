# ruoyi-platform 代理工作指南

本仓库以 RuoYi-Vue-Plus 6.x（Spring Boot 4.1 / JDK 21 / Sa-Token / MyBatis-Plus）为底座，
前端 plus-ui（Vue 3 / TypeScript / Element Plus / Vite）。所有角色都必须遵守下面的约定。

## 可变区与底座

只允许修改这些目录（module_roots）：

- `backend/ruoyi-modules/**`：新业务放 `ruoyi-biz`（包 `org.dromara.biz`），改现有系统功能改对应模块
- `frontend/src/**`、`frontend/public/**`
- `sql/biz/**`：每个变更一个文件 `<change-id>.sql`，包含建表 DDL 和 `sys_menu` 插入

其余一切（各级 pom、`ruoyi-common`、`ruoyi-api`、`ruoyi-admin` 配置、`package.json`、
`.env.*`、`backend/script/sql`、`acceptance/tools`）是底座。需要改底座时不要动手，
在返回结果的 questions 或 summary 里说明原因，由外部流程转成 BASE 提案。

## 后端约定（对照 `backend/ruoyi-modules/ruoyi-gen/src/main/resources/fm/` 的生成器模板）

一个业务表对应一组固定文件，全部放在 `org.dromara.biz.<feature>` 下：

| 文件 | 约定 |
|---|---|
| `domain/X.java` | `@TableName`，继承 `BaseEntity`（含 create_dept/create_by/create_time/update_by/update_time），主键 `@TableId` 雪花 Long |
| `domain/bo/XBo.java` | `@AutoMapper(target = X.class, reverseConvertGenerate = false)`，校验分组 `AddGroup`/`EditGroup`/`QueryGroup` |
| `domain/vo/XVo.java` | `@AutoMapper(target = X.class)`，Excel 用 `@ExcelProperty` |
| `mapper/XMapper.java` | `extends BaseMapperPlus<X, XVo>` |
| `service/IXService.java` + `service/impl/XServiceImpl.java` | 分页用 `PageQuery`，返回 `PageResult<XVo>`；条件用 `LambdaQueryWrapper` 或 `MPJLambdaWrapper`；BO/实体转换用 `MapstructUtils.convert` |
| `controller/XController.java` | `@RestController @RequestMapping("/biz/<feature>")`，继承 `BaseController`，每个接口 `@SaCheckPermission("biz:<feature>:list|query|add|edit|remove|export")`，写操作加 `@Log(title, businessType)` 和 `@RepeatSubmit()`，返回 `R<T>` |
| `resources/mapper/biz/XMapper.xml` | 与 Mapper 接口同名 |

参考实现：`backend/ruoyi-modules/ruoyi-demo/src/main/java/org/dromara/demo/`（TestDemo 单表）。

跨模块只通过 `backend/ruoyi-api` 里的接口调用，不直接依赖其他模块的 Service。

## 数据库与菜单

- 表名前缀 `biz_`，字段 snake_case，必须带 `create_dept, create_by, create_time, update_by, update_time`，建议 `del_flag char(1) default '0'`。
- 菜单 SQL 参照 `fm/sql/mysql.sql.ftl`：一个目录/菜单 `menu_type='C'`，`component='biz/<feature>/index'`，
  按钮 `menu_type='F'`，`perms='biz:<feature>:query|add|edit|remove|export'`。
- `menu_id` 用 19 位雪花风格常量，本仓库业务菜单固定使用 `1770000000000000001` 起的区段，每个变更递增，避免与上游 `1761…` 段冲突。
- 顶级"业务管理"目录 `1770000000000000000` 由第一个业务变更创建。
- 冒烟执行器会先导入 `backend/script/sql/ry_vue.sql`、`ry_workflow.sql`，再按文件名顺序导入 `sql/biz/*.sql`，因此 SQL 必须可重复执行且不依赖手工步骤。

## 前端约定（对照 `fm/vue/*.ftl`）

- `frontend/src/api/biz/<feature>/index.ts`（`listX/getX/addX/updateX/delX`，使用 `@/utils/request`）和 `types.ts`（`XVO/XForm/XQuery`）。
- `frontend/src/views/biz/<feature>/index.vue`：`<script setup lang="ts">`，`el-card` 查询区 + 表格 + `el-dialog` 表单，
  按钮用 `v-hasPermi="['biz:<feature>:add']"` 等，字典用 `useDict`，提示用 `proxy?.$modal`。
- 路由由后端 `sys_menu.component` 动态下发，不改 `frontend/src/router`。

## 验收（acceptance 角色）

- `acceptance/ui/<capability>/` 里是早期对着真实页面探索得到的测试计划（plan.md）和 Playwright 用例：写浏览器验收用例时复用其中的定位器、文案和流程。它们不进任何门。变更验收套件放在 `acceptance/changes/<change-id>/`，只含本次变更的核心链路和不能坏的基础功能；项目级系统冒烟在 `acceptance/smoke/`，由维护流程（smoke-propose / smoke-apply）更新。
- 后端用例：Python `unittest` 文件，`from ruoyi_client import Client`，`Client().login()` 后调用接口；
  RuoYi 返回 `{code, msg, data}`，成功 `code == 200`，未登录 401，无权限 403，业务失败 500。
- 前端用例：Playwright `*.spec.ts`，`import { test, expect } from '@playwright/test'`，登录页在 `/login`，
  默认账号 `admin / admin123`；页面路径与菜单 `path` 一致。
- manifest 命令统一为
  `["{python}", "acceptance/tools/ruoyi_smoke.py", "<suite_root>/test_x.py", "<suite_root>/x.spec.ts"]`（系统冒烟的 manifest 也用它，条目多一个 description），
  一个变更尽量只用一条命令（每条命令都会重新构建并启动后端）。`timeout_seconds` 至少 900。
- 用例必须在功能缺失时失败，不得因环境错误伪装为失败。

## 实现（implement 角色）

- 可以直接在仓库里编译或测试：`mvn -q -o -f backend/pom.xml -pl ruoyi-admin -am compile`；
  前端类型检查：`pnpm --dir frontend exec vue-tsc --noEmit`。
- `target/`、`node_modules/`、`dist/`、`logs/`、`__pycache__/` 和各模块的 `.flattened-pom.xml`
  已声明为 scratch，构建产生它们不会被判越界；其他被忽略的文件一律不要产生。
- git 只允许只读命令（status/diff/log/show），并且要原样单条执行（`git diff`、`git status`），
  不要加 `-C`、`--no-pager` 或管道，否则会被权限规则拒绝；不要 add、commit、stash 或切换分支。
- questions 只用于真实的产品歧义。工具、权限、环境类问题不要提问：按本指南处理，
  某项检查无法执行就跳过并在 summary 里说明，让外部冒烟和回归去验证。
- 测试分层（每层单独出结论，任何一层红都过不了）：
  - 单元测试（`*Test`，包 `org.dromara.biz.<feature>`，Mockito 隔离 Mapper，不起 Spring 上下文）由 surefire 跑；
  - 集成测试（`*IT`，包 `org.dromara.biz.<feature>.integration`，可起 Spring 上下文或真实数据库）由 failsafe 跑，
    命令 `mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -DskipITs=false -pl ruoyi-modules/ruoyi-biz failsafe:integration-test failsafe:verify`；
  - 静态检查：`pnpm --dir frontend exec vue-tsc --noEmit`；
  - 变更验收 `acceptance/changes/<change-id>/`（合同，你不能改）；项目级系统冒烟 `acceptance/smoke/`（你不能改，合并后由维护流程更新）。
- 特征化（characterize 角色）：实现之前，为将被修改的既有类写只断言"必须不变"行为的单元测试（列表和字段会扩展的用 contains 断言），
  放在同一个单元测试包里，命名 `<Class>CharacterizationTest`，必须在当前代码上跑绿；只能写 `src/test` 下的文件。
- 测试先行：每个行为先写单元测试，看到它因预期原因失败，再写最小实现让它通过，最后重构。实现只能修改 payload.characterization.touched 列出的既有文件和新文件。
  - 后端：`backend/ruoyi-modules/<module>/src/test/java/org/dromara/biz/<feature>/` 下的 JUnit 5 测试，Service 层用 Mockito 隔离 Mapper
    （`spring-boot-starter-test` 已对所有业务模块可用，不要起 Spring 上下文）。测试类必须加 `@Tag("dev")`，
    因为父 pom 的 surefire 只运行当前 profile 标签的测试，没有标签的类会被静默跳过。单跑一个类：
    `mvn -q -o -f backend/pom.xml -pl ruoyi-modules/ruoyi-biz -Dmaven.test.skip=false -DskipTests=false -Dtest=<Class> -Dsurefire.failIfNoSpecifiedTests=false test`
    （父 pom 默认 `maven.test.skip=true`，两个开关都要传）。回归命令 `-pl ruoyi-admin -am test` 会一起跑业务模块的测试。
  - 前端：只对纯函数和 api 封装写 vitest 用例，文件放在源码旁边命名为 `<name>.test.ts`，运行
    `pnpm --dir frontend exec vitest run <file>`；仓库没有 @vue/test-utils，不写组件测试，页面行为交给冒烟。
  - design 的 `## Tests First` 逐条记录测试名、实现前看到的失败、最终绿灯。
- 实现完成后自检：编译通过、SQL 语法正确、菜单权限串与 `@SaCheckPermission` 一致、前端 api 路径与后端 `@RequestMapping` 一致。
