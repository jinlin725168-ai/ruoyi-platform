# 端到端新增一个业务功能

以新表 `biz_<table>`、功能名 `<feature>`（小驼峰，例如 `supplier`、`purchaseOrder`）为例。下面所有文件都在可变区内。

## 0. 选参考实现

| 场景 | 复制对象 |
|---|---|
| 单表增删改查，带导出、字典字段、唯一性校验、哨兵查询值 | 后端 `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/`；前端 `frontend/src/api/biz/supplier/` 和 `views/biz/supplier/index.vue`；SQL `sql/biz/FEAT-20260918-001.sql` 和 `FEAT-20260921-001.sql` |
| 主子表、系统生成单号、状态流转（草稿到已提交）、额外按钮权限、日期区间查询、下拉选项接口 | 后端 `.../org/dromara/biz/purchase/`；前端 `views/biz/purchaseOrder/index.vue`；SQL `sql/biz/FEAT-20260920-001.sql` |
| 上游范式：数据权限、Excel 导入、自定义分页 XML、树表 | `backend/ruoyi-modules/ruoyi-demo/src/main/java/org/dromara/demo/`（`TestDemo*`、`TestTree*`） |
| 字段和注解写法对照 | `backend/ruoyi-modules/ruoyi-gen/src/main/resources/fm/{java,xml,sql,vue}/*.ftl` |

代码生成器（`/tool/gen`）会生成到 `org.dromara.system` 包，菜单 SQL 的列也不全。在 StoryLoop 里要手写文件，照参考实现写，不直接落生成器的输出。

## 1. 数据库：`sql/biz/<change-id>.sql`

### 文件要求

- 一个变更一个文件，文件名就是 change-id。
- 冒烟执行器会在全新的临时库上，先导入 `ry_vue.sql` 和 `ry_workflow.sql`，再按文件名顺序导入全部 `sql/biz/*.sql`。所以脚本必须可重复执行，也必须能在空库上执行。常用写法：
  - 建表：`create table if not exists biz_<table> (...) engine=innodb comment = '...';`
  - 给已有表加列：先查 `information_schema.columns`，再用 `prepare/execute` 条件执行，写法见 `FEAT-20260921-001.sql`。
  - 字典和菜单：先 `delete ... where ...`，再 `insert`。

### 表结构约定

- 表名前缀 `biz_`，字段用 snake_case。
- 主键为 `<x>_id bigint(20) not null`，值由应用用雪花算法生成。
- 必须有 `create_dept, create_by, create_time, update_by, update_time`。
- 建议有 `del_flag char(1) default '0'`。
- 状态字段用 `status char(1) default '0'`，对应字典 `sys_normal_disable`（0 正常，1 停用）。
- 唯一约束要慎用：逻辑删除后的行仍然占用唯一键。供应商编码因此只建了普通索引，唯一性在 Service 里按未删除行校验。采购单号本来就不允许复用，所以用了 `unique key`。

### 字典

- 表 `sys_dict_type` 的列：`dict_id, dict_name, dict_type, create_dept, create_by, create_time, update_by, update_time, remark`。
- 表 `sys_dict_data` 的列：`dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, create_dept, create_by, create_time, update_by, update_time, remark`。
- 字典类型命名为 `biz_<xxx>`。

### 菜单

用 `sys_menu` 的完整列清单（生成器模板缺 `query_param/active_menu/ext`）：

`menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark`

- **菜单行**：
  - `parent_id=1770000000000000000`，即『业务管理』目录（path 为 `biz`）。它已由 FEAT-20260918-001 创建，不要重复创建。
  - `menu_type='C'`，`path='<feature>'`，`component='biz/<feature>/index'`，`perms='biz:<feature>:list'`。
  - `is_frame='N'`，`is_cache='Y'`，`visible='0'`，`status='0'`，`order_num` 按顺序递增。
- **按钮行**：
  - `menu_type='F'`，`path='#'`，`component=''`，`icon='#'`。
  - `perms` 分别为 `biz:<feature>:query`、`:add`、`:edit`、`:remove`、`:export`；有自定义动作时再加，例如 `biz:purchaseOrder:submit`。
- `create_dept`、`create_by` 沿用现有 `sql/biz` 文件里的种子部门 ID 和管理员 ID 常量。

### ID 分配

ID 用 19 位常量，避开上游的 `1761…` 段。

| 区段 | 已用 | 下一个变更建议从 |
|---|---|---|
| 菜单 `17700000000000000xx` | `…000` 业务管理目录；`…001–006` 供应商；`…010–016` 采购单 | `1770000000000000020`（每个功能占一个 10 的区段） |
| 字典类型 `17705000000000000xx` | `…001` 采购单状态；`…002` 供应商分类 | `1770500000000000003` |
| 字典数据 `17706000000000000xx` | `…001–005` | `1770600000000000006` |

写之前先 grep 一遍 `sql/biz/`，确认没有被占用。

### 角色授权

超级管理员自动拥有全部权限，不需要插 `sys_role_menu`。普通角色的授权由管理员在界面上完成；冒烟里通过 `/system/role` 接口完成。

## 2. 后端：`backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/<feature>/`

每个文件的要点，对照 `BizSupplier*`：

### `domain/Biz<X>.java`（实体）

- 类注解：`@Data @EqualsAndHashCode(callSuper = true) @TableName("biz_<table>")`，`extends BaseEntity`。
- 主键：`@TableId(value = "<x>_id") private Long <x>Id;`。
- 逻辑删除：`@TableLogic private String delFlag;`。

### `domain/bo/Biz<X>Bo.java`（业务对象，入参）

- 类注解：`@Data @AutoMapper(target = Biz<X>.class, reverseConvertGenerate = false)`，`implements Serializable`。
- 校验：
  - 主键：`@NotNull(groups = EditGroup.class)`。
  - 必填：`@NotBlank(message, groups = {AddGroup.class, EditGroup.class})`。
  - 长度用 `@Size`，格式用 `@Pattern`。
  - 字典值也可以用 core 里的 `@DictPattern`。
- 日期字段：`@DateTimeFormat(pattern = "yyyy-MM-dd")` 加 `@JsonFormat(pattern = "yyyy-MM-dd")`。
- 子表：`@Valid @NotEmpty List<ChildBo>`。
- 需要日期区间时，自己声明 `private Map<String, Object> params = new HashMap<>();`。前端 `useDateRangeQuery('OrderDate')` 会生成 `params[beginOrderDate]` 和 `params[endOrderDate]`，写法见 `BizPurchaseOrderBo`。

### `domain/vo/Biz<X>Vo.java`（视图对象，出参）

- 类注解：`@Data @ExcelIgnoreUnannotated @AutoMapper(target = Biz<X>.class)`。
- 导出列：`@ExcelProperty(value = "中文列名")`。字典列加 `converter = ExcelDictConvert.class` 和 `@ExcelDictFormat(dictType = "...")`。
- 只在响应里出现的派生字段（例如 `supplierCategoryLabel`）由 Service 填充。
- 导出结构与列表不同时，单独建 `*ExportVo`（例如 `BizPurchaseOrderExportVo`）。

### `mapper/Biz<X>Mapper.java`

- `public interface Biz<X>Mapper extends BaseMapperPlus<Biz<X>, Biz<X>Vo>`。
- 自定义 SQL 方法的参数加 `@Param`。

### `resources/mapper/biz/Biz<X>Mapper.xml`

- 放在 `ruoyi-biz/src/main/resources/mapper/biz/` 下，`namespace` 为 Mapper 接口的全名。
- 没有自定义 SQL 也保留一个空的 mapper 文件，与现有文件保持一致。

### `service/IBiz<X>Service.java`

方法：`queryById`、`queryPageList(bo, PageQuery)`（返回 `PageResult<Vo>`）、`queryList(bo)`、`insertByBo`、`updateByBo`、`deleteWithValidByIds(Collection<Long>, Boolean)`，以及校验方法（例如 `checkXxxUnique`）。

### `service/impl/Biz<X>ServiceImpl.java`

- 类注解：`@RequiredArgsConstructor @Service`。
- 查询条件：私有方法 `buildQueryWrapper(bo)` 用 `Wrappers.lambdaQuery()` 加带条件的 `like/eq/ge/le(condition, column, value)`，最后固定排序。
- 分页：`mapper.selectVoPage(pageQuery.build(), lqw)`，再 `PageResult.build(page.getRecords(), page.getTotal())`。
- 转换：BO 转实体用 `MapstructUtils.convert(bo, X.class)`。
- 新增：成功后把主键回写到 bo。
- 修改：把不允许修改的字段置为 null，`updateById` 会忽略 null 字段。
- 失败：`throw new ServiceException("可读提示")`。
- 事务：涉及多表的写操作加 `@Transactional(rollbackFor = Exception.class)`。
- 字典相关逻辑：注入 `DictService`，例如 `getAllDictByDictType`。

### `controller/Biz<X>Controller.java`

- 类注解：`@Validated @RequiredArgsConstructor @RestController @RequestMapping("/biz/<feature>")`，`extends BaseController`。
- 标准接口见下表。

### `constant/<X>Constants.java`（可选）

放字典类型、哨兵值等常量，例如 `SupplierConstants`。

### 控制器标准接口

接口与菜单权限一一对应：

| 方法与路径 | 注解 | 签名与返回 |
|---|---|---|
| `GET /list` | `@SaCheckPermission("biz:<feature>:list")` | `R<PageResult<Vo>> list(Bo bo, PageQuery pageQuery)` |
| `POST /export` | `:export`，加 `@Log(title = "...", businessType = BusinessType.EXPORT)` | `void export(Bo bo, HttpServletResponse response)`，方法体为 `ExcelBuilder.of(list, Vo.class).sheetName("...").toResponse(response)` |
| `GET /{id}` | `:query` | `R<Vo>`，路径变量加 `@NotNull` |
| `POST` | `:add`，加 `@Log(INSERT)` 和 `@RepeatSubmit()` | `R<Void> add(@Validated(AddGroup.class) @RequestBody Bo bo)`，返回 `toAjax(...)` |
| `PUT` | `:edit`，加 `@Log(UPDATE)` 和 `@RepeatSubmit()` | `R<Void> edit(@Validated(EditGroup.class) @RequestBody Bo bo)` |
| `DELETE /{ids}` | `:remove`，加 `@Log(DELETE)` | `R<Void> remove(@NotEmpty @PathVariable Long[] ids)` |
| 自定义动作，例如 `PUT /submit/{id}` 或 `GET /supplierOptions` | 独立的权限串 `biz:<feature>:<action>`；只读的选项接口可以复用 `:list` | 视情况而定 |

可读的业务失败有两种写法：在控制器里 `return R.fail("...")`（见供应商编码重复），或者在 Service 里抛 `ServiceException`（见采购单）。对外都是 `code=500` 加 msg。

### 跨模块调用

- 需要用户、部门、角色、参数、OSS、消息、工作流时，注入 `ruoyi-api` 的接口：`UserService`、`DeptService`、`RoleService`、`ConfigService`、`OssService`、`MessageService`、`WorkflowService`。
- 需要字典时，注入 `DictService`。
- 不要注入 `ruoyi-system` 的 `ISys*Service` 或 Mapper。
- 需要额外的 common 模块时，在 `ruoyi-biz/pom.xml` 里加依赖，不写版本。

## 3. 前端

### `frontend/src/api/biz/<feature>/types.ts`

- `<X>VO`：ID 类型写 `string | number`。
- `<X>Form extends BaseEntity`：字段全部可选。
- `<X>Query extends PageQuery`。
- 前后端共享的常量也放在这里，例如 `SUPPLIER_CATEGORY_NONE`。

### `frontend/src/api/biz/<feature>/index.ts`

- 导出 `list<X>`、`get<X>`、`add<X>`、`update<X>`、`del<X>`，加上自定义动作的函数。
- 用 `import request from '@/utils/request'` 发请求；返回类型写 `AxiosPromise<PageResult<VO>>`，类型分别来自 `@/utils/api-types` 和 `@/api/types`。
- URL 必须与后端 `@RequestMapping` 一致，例如 `/biz/<feature>/list`。

### `frontend/src/views/biz/<feature>/index.vue`

照 `views/biz/supplier/index.vue` 的结构写：

- **模板结构**：查询卡片（`el-card` 里放 inline 的 `el-form`）；表格卡片（工具栏按钮、`right-toolbar`、`el-table`、`pagination`）；`el-dialog` 表单。按钮权限写法：`v-hasPermi="['biz:<feature>:add']"`。
- **脚本头**：`<script setup name="<X>" lang="ts">`，name 用菜单 path 首字母大写（例如 `Supplier`、`PurchaseOrder`）。
- **组合函数**：`useLoading`、`useSearchToggle`、`useTableSelection`、`useFormDialog`、`useSearchReset`；有日期区间时加 `useDateRangeQuery`。
- **字典**：`toRefs<any>(useDict('sys_normal_disable', 'biz_xxx'))`，列表里用 `<dict-tag :options=... :value=...>` 显示。
- **提示与确认**：`modal.msgSuccess`、`modal.confirm`。
- **导出**：`download('biz/<feature>/export', { ...queryParams }, '<feature>_<时间戳>.xlsx')`。
- **样式**：`@use '@/assets/styles/components/page-shell' as pageShell; @include pageShell.table-crud-page;`。

### 路由与权限一致性

- 不改 `frontend/src/router`。菜单的 `path` 和 `component` 决定访问地址 `/biz/<feature>` 和对应的视图文件。
- 同一个权限串在三处必须一致：`sys_menu.perms`、`@SaCheckPermission`、`v-hasPermi`。

## 4. 测试（先写测试）

- **后端单元测试**：放在 `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/<feature>/`。
  - 用 JUnit 5 加 Mockito：`@ExtendWith(MockitoExtension.class)`，`@Mock` Mapper 和 `DictService`，`@InjectMocks` ServiceImpl。
  - 类上必须加 `@Tag("dev")`。
  - 不启动 Spring 上下文。
  - 注意 `MapstructUtils` 和 `LoginHelper` 依赖 Spring 容器。运行方式和注意事项见 `testing.md`。
- **前端**：只给纯函数和 api 封装写 vitest 用例，命名 `<name>.test.ts`，放在源码旁边。
- **冒烟**：由 smoke 角色写在 `acceptance/smoke/<change-id>/`，见 `testing.md`。

## 5. 自检清单

1. `mvn -q -o -f backend/pom.xml -pl ruoyi-admin -am compile` 通过。
2. `pnpm --dir frontend exec vue-tsc --noEmit` 通过。
3. SQL 在空库上能连续执行两遍；ID 与已有文件不冲突；`parent_id` 指向业务管理目录。
4. 三组对应关系一致：`perms`、`@SaCheckPermission`、`v-hasPermi`；前端 URL 与 `@RequestMapping`；`component` 与 `views` 下的路径。
5. 新 Mapper 位于 `org.dromara.biz.<feature>.mapper`，XML 位于 `resources/mapper/biz/`。
6. 没有改动可变区以外的任何文件，包括 `.env.*`、各级集成 pom 和 `acceptance/tools`。
7. 单元测试类带 `@Tag("dev")`，在回归命令里确实被执行了。
