# 扩展新功能机制

对应底座版本：1.0.19，生成日期：2026-09-28

以新表 `biz_<table>`、功能名 `<feature>`（小驼峰，例如 `supplier`、`purchaseOrder`）、类名前缀 `Biz<X>` 为例。除特别说明外，下面所有文件都在可变区内。

## 一、新增一个业务表的完整功能

| 层 | 文件（新建） | 命名与写法约定 | 参考实现 |
|---|---|---|---|
| SQL | `sql/biz/<change-id>.sql` | 建表、字典、菜单；可重复执行，空库可执行（见第二节） | `sql/biz/FEAT-20260918-001.sql`（单表）、`FEAT-20260920-001.sql`（主子表）、`FEAT-20260921-001.sql`（给已有表加列） |
| 实体 | `ruoyi-biz/src/main/java/org/dromara/biz/<feature>/domain/Biz<X>.java` | `@Data @EqualsAndHashCode(callSuper = true) @TableName("biz_<table>")`，`extends BaseEntity`；`@TableId(value = "<x>_id") private Long <x>Id`；`@TableLogic private String delFlag` | `supplier/domain/BizSupplier.java` |
| 入参 BO | `.../<feature>/domain/bo/Biz<X>Bo.java` | `@Data @AutoMapper(target = Biz<X>.class, reverseConvertGenerate = false)`；主键 `@NotNull(groups = EditGroup.class)`；必填 `@NotBlank(groups = {AddGroup.class, EditGroup.class})`；长度 `@Size`；日期字段加 `@DateTimeFormat` 和 `@JsonFormat`；子表用 `@Valid @NotEmpty List<ChildBo>`；日期区间要自己声明 `Map<String,Object> params` | `supplier/domain/bo/BizSupplierBo.java`、`purchase/domain/bo/BizPurchaseOrderBo.java` |
| 出参 VO | `.../<feature>/domain/vo/Biz<X>Vo.java` | `@Data @ExcelIgnoreUnannotated @AutoMapper(target = Biz<X>.class)`；导出列加 `@ExcelProperty(value = "中文列名")`；字典列加 `converter = ExcelDictConvert.class` 和 `@ExcelDictFormat(dictType = ...)`；派生字段（如 `supplierCategoryLabel`）由 Service 填充；导出结构与列表不同时另建 `*ExportVo` | `BizSupplierVo`、`BizPurchaseOrderExportVo` |
| Mapper | `.../<feature>/mapper/Biz<X>Mapper.java` | `extends BaseMapperPlus<Biz<X>, Biz<X>Vo>`；自定义方法的参数加 `@Param` | `BizSupplierMapper` |
| Mapper XML | `ruoyi-biz/src/main/resources/mapper/biz/Biz<X>Mapper.xml` | `namespace` 为接口全名；没有自定义 SQL 也保留空文件；手写 SQL 不会自动过滤逻辑删除 | `mapper/biz/BizSupplierMapper.xml` |
| Service 接口 | `.../<feature>/service/IBiz<X>Service.java` | `queryById`、`queryPageList(bo, PageQuery)` 返回 `PageResult<Vo>`、`queryList(bo)`、`insertByBo`、`updateByBo`、`deleteWithValidByIds(Collection<Long>, Boolean)`、`check*` | `IBizSupplierService` |
| Service 实现 | `.../<feature>/service/impl/Biz<X>ServiceImpl.java` | `@RequiredArgsConstructor @Service`；私有 `buildQueryWrapper(bo)` 用 `Wrappers.lambdaQuery()` 和带条件的 `eq/like/ge/le`，最后固定排序；BO 转实体用 `MapstructUtils.convert`；新增后把主键回写到 bo；修改时把不可改的字段置 null；业务失败抛 `ServiceException`；多表写操作加 `@Transactional(rollbackFor = Exception.class)` | `BizSupplierServiceImpl`、`BizPurchaseOrderServiceImpl` |
| Controller | `.../<feature>/controller/Biz<X>Controller.java` | `@Validated @RequiredArgsConstructor @RestController @RequestMapping("/biz/<feature>")`，`extends BaseController`；标准接口见下表 | `BizSupplierController` |
| 常量（可选） | `.../<feature>/constant/<X>Constants.java` | 字典类型、哨兵值 | `supplier/constant/SupplierConstants.java` |
| 后端单元测试 | `ruoyi-biz/src/test/java/org/dromara/biz/<feature>/Biz<X>*Test.java` | 类上 `@Tag("dev")`，用 `@ExtendWith(MockitoExtension.class)`，不起 Spring 上下文；写法见 `testing.md` | `purchase/BizPurchaseOrderRemarkTest.java` |
| 前端类型 | `frontend/src/api/biz/<feature>/types.ts` | `<X>VO`（ID 类型写 `string \| number`）、`<X>Form extends BaseEntity`（字段全部可选）、`<X>Query extends PageQuery`；前后端共享的常量也放这里 | `api/biz/supplier/types.ts` |
| 前端请求 | `frontend/src/api/biz/<feature>/index.ts` | `list<X>/get<X>/add<X>/update<X>/del<X>`，`import request from '@/utils/request'`，返回类型 `AxiosPromise<...>`；URL 与 `@RequestMapping` 一致 | `api/biz/supplier/index.ts` |
| 前端页面 | `frontend/src/views/biz/<feature>/index.vue` | 见第三节 | `views/biz/supplier/index.vue` |
| 前端单元测试（可选） | 源码旁边的 `<name>.test.ts` | 只测纯函数、api 封装和类型；页面只能用 `?raw` 读源码做包含式断言 | `api/biz/supplier/query.test.ts`、`views/biz/purchaseOrder/index.test.ts` |

**不需要改的文件**：`frontend/src/router/**`（路由由菜单下发）、`ruoyi-admin` 的任何文件（`ruoyi-biz` 已是 admin 的依赖）、`ruoyi-biz/pom.xml`（集成点）、`application*.yml`。

**控制器标准接口**（权限串与菜单按钮一一对应）：

| 方法与路径 | 注解 | 签名 |
|---|---|---|
| `GET /list` | `@SaCheckPermission("biz:<feature>:list")` | `R<PageResult<Vo>> list(Bo bo, PageQuery pageQuery)` |
| `POST /export` | `:export`，加 `@Log(title, businessType = BusinessType.EXPORT)` | `void export(Bo bo, HttpServletResponse response)`，方法体为 `ExcelBuilder.of(list, Vo.class).sheetName(..).toResponse(response)` |
| `GET /{id}` | `:query` | `R<Vo> getInfo(@NotNull @PathVariable Long id)` |
| `POST` | `:add`，加 `@Log(INSERT)` 和 `@RepeatSubmit()` | `R<Void> add(@Validated(AddGroup.class) @RequestBody Bo bo)`，返回 `toAjax(...)` |
| `PUT` | `:edit`，加 `@Log(UPDATE)` 和 `@RepeatSubmit()` | `R<Void> edit(@Validated(EditGroup.class) @RequestBody Bo bo)` |
| `DELETE /{ids}` | `:remove`，加 `@Log(DELETE)` | `R<Void> remove(@NotEmpty @PathVariable Long[] ids)` |
| 自定义动作（如 `PUT /submit/{id}`） | 独立权限串 `biz:<feature>:<action>`；只读的选项接口可以复用 `:list`（如 `GET /biz/purchaseOrder/supplierOptions`） | 视情况而定 |

**跨模块调用**：

- 用户、部门、角色、参数、OSS、消息、工作流：注入 `ruoyi-api` 的 `UserService`、`DeptService`、`RoleService`、`ConfigService`、`OssService`、`MessageService`、`WorkflowService`。
- 字典：注入 `DictService`。
- 同在 `ruoyi-biz` 里的其他功能：直接注入它的 `IBiz*Service`。

## 二、菜单与权限

**SQL 文件要求**：

- 冒烟执行器在全新临时库上先导入 `ry_vue.sql`、`ry_workflow.sql`，再按文件名导入全部 `sql/biz/*.sql`，所以脚本必须可重复执行，也必须能在空库上执行。
- 建表：`create table if not exists`。
- 给已有表加列：先查 `information_schema.columns`，再用 `prepare/execute` 条件执行（见 `FEAT-20260921-001.sql`）。
- 字典和菜单：先 `delete ... where id in (...)`，再 `insert`。

**表结构**：

- 表名前缀 `biz_`，字段用 snake_case；主键 `<x>_id bigint(20)`。
- 必须有 `create_dept, create_by, create_time, update_by, update_time`，建议有 `del_flag char(1) default '0'`。
- 状态字段用 `status char(1)`，对应字典 `sys_normal_disable`。
- 慎用唯一约束，因为逻辑删除的行仍然占用唯一键：供应商编码只建普通索引，在 Service 里校验唯一；采购单号用了 unique key。

**菜单**：

- `sys_menu` 用完整列清单：`menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark`。
- 菜单行：
  - `parent_id=1770000000000000000`，即『业务管理』目录（path 为 `biz`）。它已由 FEAT-20260918-001 创建，不要重复创建。
  - `menu_type='C'`、`path='<feature>'`、`component='biz/<feature>/index'`、`perms='biz:<feature>:list'`。
  - `is_frame='N'`、`is_cache='Y'`、`visible='0'`、`status='0'`。
- 按钮行：`menu_type='F'`、`path='#'`、`component=''`、`icon='#'`，`perms` 为 `biz:<feature>:query|add|edit|remove|export` 或自定义动作。
- `create_dept`、`create_by` 沿用现有 `sql/biz` 文件里的种子部门 ID 和管理员 ID 常量。

**ID 区段**（19 位常量，避开上游的 `1761…` 段；写之前先在 `sql/biz/` 里搜一遍）：

| 区段 | 已用 | 下一个建议值 |
|---|---|---|
| 菜单 `17700000000000000xx` | `…000` 业务管理；`…001–006` 供应商；`…010–016` 采购单 | `1770000000000000020`（每个功能占一个 10 的区段） |
| 字典类型 `17705000000000000xx` | `…001` 采购单状态；`…002` 供应商分类 | `1770500000000000003` |
| 字典数据 `17706000000000000xx` | `…001–005` | `1770600000000000006` |

**权限一致性**：同一个权限串在 `sys_menu.perms`、`@SaCheckPermission`、前端 `v-hasPermi` 三处必须一致。超级管理员自动拥有全部权限，不需要插 `sys_role_menu`；普通角色的授权在冒烟里通过 `/system/role` 接口完成。

## 三、前端页面

- **路由怎么出现**：不改 `frontend/src/router`。菜单的 `component`（`biz/<feature>/index`）决定加载 `views/biz/<feature>/index.vue`，父目录 path 和菜单 path 拼成访问地址 `/biz/<feature>`。
- **页面骨架**（照 `views/biz/supplier/index.vue` 写）：
  - `<script setup name="<X>" lang="ts">`，name 为菜单 path 首字母大写。
  - 模板：查询卡片（`el-card` 里放 inline 的 `el-form`）；表格卡片（工具栏按钮、`right-toolbar`、`el-table`、`pagination`）；`el-dialog` 表单。
  - 按钮权限：`v-hasPermi="['biz:<feature>:add']"`。
  - 组合函数：`useLoading`、`useSearchToggle`、`useTableSelection`、`useFormDialog`、`useSearchReset`；有日期区间时加 `useDateRangeQuery`。
  - 字典：`toRefs<any>(useDict('sys_normal_disable', 'biz_xxx'))`，列表里用 `<dict-tag>` 显示。
  - 提示：现有业务页用 `import modal from '@/plugins/modal'`；`proxy?.$modal` 也能用。
  - 导出：`download('biz/<feature>/export', {...queryParams}, '<feature>_<时间戳>.xlsx')`。
  - 样式：`@use '@/assets/styles/components/page-shell' as pageShell; @include pageShell.table-crud-page;`。

## 四、修改既有功能

| 改动 | 要碰的文件 |
|---|---|
| 加字段 | `sql/biz/<change-id>.sql`（`information_schema` 条件加列）、实体、Bo（校验）、Vo（加 `@ExcelProperty` 才会导出）、导出用的 `*ExportVo` 与 Service 里的组装代码（如 `queryExportList`）、前端 `types.ts`、`index.vue`（表单、列、详情、初始值、回填和提交） |
| 已有列只是新暴露到页面 | 不需要 SQL（例如 FEAT-20260928-002 的 remark 列在建表时已存在） |
| 加查询条件 | Bo 加字段；`ServiceImpl.buildQueryWrapper`（列表和导出共用，一处改动两处生效）；前端 `types.ts` 的 `<X>Query` 和 `index.vue` 的查询表单 |
| 加跨表派生显示 | 被依赖功能的 Service 接口加批量查询方法（如 `IBizSupplierService.queryCategoryLabels`），在调用方的 `fill*` 方法里填充 Vo |
| 改接口或加动作 | Controller 方法、权限串、SQL 里的按钮行、前端 `index.ts` 和 `v-hasPermi` |
| 改既有类之前 | characterize 角色先在同一测试包里写 `<Class>CharacterizationTest`（前端写 `index.test.ts`），锁定必须不变的行为；实现角色只能改 `payload.characterization.touched` 列出的既有文件 |

## 五、代码生成器

- 模板路径：`backend/ruoyi-modules/ruoyi-gen/src/main/resources/fm/{java,xml,sql,vue,...}/*.ftl`；默认值在 `generator.yml`（默认包为 `org.dromara.system`）；前端另有 `frontend/gen/*.ftl`。
- 生成物与手写的差异：
  - 包名不同，生成器默认 `org.dromara.system`，StoryLoop 要求 `org.dromara.biz.<feature>`。
  - 菜单 SQL 模板缺 `query_param/active_menu/ext` 三列，也不可重复执行。
  - 生成的代码没有经过 spotless 和 checkstyle。
  - 所以只把模板当作注解和结构的对照，照参考实现手写。

## 六、禁止事项

- 不改底座：集成点（各级 pom，包括 `ruoyi-biz/pom.xml`、`package.json`、`pnpm-lock.yaml`、`pnpm-workspace.yaml`）、`ruoyi-common/**`、`ruoyi-api/**`、`ruoyi-admin/**`、`backend/script/sql/**`、`acceptance/tools/**`、`.env.*`、`vite.config.ts`、`.github/workflows/**`、`checkstyle-biz.xml`、`.gitleaks.toml`。需要改时写进 questions 或 summary，转成 BASE 提案。
- 不在离线构建里引入新的三方依赖（所有命令都带 `-o`）。
- `ruoyi-biz` 不注入 `ruoyi-system` 或 `ruoyi-workflow` 的 Service、Mapper。
- 不绕过 `@SaCheckPermission` 和 `R<T>`；不在控制器里 try/catch 吞掉异常（checkstyle 有 `EmptyCatchBlock`、`IllegalCatch`）。
- 不改 `frontend/src/router`；不写组件测试（仓库没有 `@vue/test-utils`）。
- 不写入任何密钥、口令或 token（gitleaks 会拦截，业务代码不在豁免范围内）。
- 实现角色不写 `acceptance/changes`、`acceptance/smoke`、`openspec/specs` 这些流程生成路径。
- 检查层的格式要求：无未用 import；import 顺序为 `java,javax,jakarta,org,com,` 加其余；无尾随空白；4 空格缩进；if/for 必须加大括号；只有 `org.springframework.web.bind.annotation` 允许星号导入；单行不超过 160 字符。`spotless:apply` 可以一键修复格式。

## 七、参考实现

**单表**：带导出、字典字段、唯一性校验、哨兵查询值、去空白且忽略大小写的模糊查询。

- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/`：`constant/SupplierConstants`、`domain/BizSupplier`、`domain/bo/BizSupplierBo`、`domain/vo/BizSupplierVo`、`mapper/BizSupplierMapper`、`service/IBizSupplierService`、`service/impl/BizSupplierServiceImpl`、`controller/BizSupplierController`
- `ruoyi-biz/src/main/resources/mapper/biz/BizSupplierMapper.xml`
- `frontend/src/api/biz/supplier/{index.ts,types.ts,query.test.ts,types.test.ts}`
- `frontend/src/views/biz/supplier/index.vue`
- `sql/biz/FEAT-20260918-001.sql`、`sql/biz/FEAT-20260921-001.sql`
- 测试：`ruoyi-biz/src/test/java/org/dromara/biz/supplier/*Test.java`

**主子表**：系统生成单号、状态流转、额外按钮权限、日期区间、选项接口、跨功能派生字段、备注。

- `.../org/dromara/biz/purchase/` 下全部文件
- `mapper/biz/BizPurchaseOrderMapper.xml`、`BizPurchaseOrderDetailMapper.xml`
- `frontend/src/api/biz/purchaseOrder/*`、`frontend/src/views/biz/purchaseOrder/*`
- `sql/biz/FEAT-20260920-001.sql`

**上游范式**：数据权限、Excel 导入、树表，见 `backend/ruoyi-modules/ruoyi-demo/src/main/java/org/dromara/demo/`（`TestDemo*`、`TestTree*`）。

**自检清单**：

1. `mvn -q -o -f backend/pom.xml -pl ruoyi-admin -am compile` 通过。
2. `spotless:check` 和 `checkstyle:check` 通过（命令见 `testing.md`）。
3. `python3 acceptance/tools/frontend_check.py` 通过。
4. SQL 在空库上能连续执行两遍，ID 不冲突。
5. 三组对应关系一致：`perms`、`@SaCheckPermission`、`v-hasPermi`；前端 URL 与 `@RequestMapping`；`component` 与 views 下的路径。
6. 单元测试类带 `@Tag("dev")`，并且确实被执行了。
