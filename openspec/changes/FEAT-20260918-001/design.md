## Context

**现状**

- 平台基于 RuoYi-Vue-Plus 体系：后端用 Spring Boot + MyBatis-Plus + Sa-Token，前端用 Vue 3 + Element Plus + TypeScript。已有通用能力可直接复用，包括 `BaseEntity` 审计字段、`BaseMapperPlus`、`PageQuery`/`PageResult`、`ExcelBuilder` 与字典转换、`@Log` 操作日志、`@RepeatSubmit` 防重复提交、`v-hasPermi` 按钮权限指令，以及 `useFormDialog`、`useTableSelection` 等页面 hooks。
- 本次变更之前，系统中没有『业务管理』一级目录，也没有供应商相关的表、接口或页面。FEAT-20260918-001 是第一个业务变更，由它负责创建这个目录。
- 全局主键策略是 `idType: ASSIGN_ID`（雪花 ID），配置见 `common-mybatis.yml`。当前平台没有 `tenant_id` 多租户字段。
- 本文依据 main 分支当前工作区中的对应文件整理（仓库状态 clean）。

**约束**

- 后端接口和前端页面都要交付。列表、新增、修改、删除、导出分别由按钮级权限控制。
- 可维护的字段有：供应商编码、名称、联系人、联系电话、启用/停用状态、备注。
- 列表按名称和状态分页查询，支持导出 Excel。
- SQL 脚本要能重复执行，便于在各环境反复部署。

**涉及的模块**

- 后端：`ruoyi-modules/ruoyi-biz`，包 `org.dromara.biz.supplier`（controller / domain / bo / vo / mapper / service），以及 `mapper/biz` 下的 XML。
- 前端：`src/api/biz/supplier`（接口与类型）、`src/views/biz/supplier`（页面）。
- 数据库：新表 `biz_supplier`；`sys_menu` 中新增『业务管理』目录、『供应商管理』菜单和 5 个按钮。
- 复用字典：`sys_normal_disable`（0 正常 / 1 停用）。

## Goals

- 在『业务管理』目录下提供『供应商管理』菜单。有权限的用户可以维护供应商档案，字段包括编码、名称、联系人、联系电话、状态和备注。
- 支持按供应商名称（模糊匹配）和状态（精确匹配）分页查询，结果按新增时间倒序排列。
- 支持新增、修改、删除（含批量删除），并导出与当前查询条件一致的 Excel。
- 列表、查询详情、新增、修改、删除、导出分别由 `biz:supplier:list/query/add/edit/remove/export` 权限控制，前端按钮也按同一套权限显示或隐藏。
- 供应商编码在未删除的数据中唯一，创建后不能修改。
- 新增、修改、删除、导出都写入操作日志；新增和修改防止重复提交。

## Decisions

**1. 表结构：单表 `biz_supplier`，带审计字段和逻辑删除**

- Choice：新建 `biz_supplier` 表。
  - 主键 `supplier_id bigint`，业务字段 `supplier_code varchar(64) not null`、`supplier_name varchar(100) not null`、`contact_name varchar(50)`、`contact_phone varchar(50)`、`status char(1) default '0'`、`remark varchar(500)`。
  - 加上 `del_flag` 以及 `create_dept/create_by/create_time/update_by/update_time`。
  - 在 `supplier_code` 和 `supplier_name` 上各建一个普通索引。
  - 实体继承 `BaseEntity`，`delFlag` 标注 `@TableLogic`。
- Rationale：
  - 与平台现有表的风格一致，审计字段由框架自动填充。
  - 逻辑删除保留历史档案，今后采购单等业务引用供应商时也可追溯。
  - 两个索引分别服务于编码唯一性校验和名称模糊查询。
  - 联系电话用 `varchar(50)`，可以存座机、分机或多个号码。
- Alternatives considered：
  - 物理删除：会丢失历史，被业务单据引用后也无法追溯，因此不采用。
  - 在 `supplier_code` 上建唯一索引：它与逻辑删除冲突，已删除记录会占住编码，除非改成 `(supplier_code, del_flag)` 这类组合唯一键。最终把唯一性放在应用层（见决策 3）。
  - 拆出联系人子表以支持多个联系人：超出本期需求，没有采用。

**2. 主键与编码规则：主键用雪花 ID，供应商编码由用户手工录入**

- Choice：
  - `supplier_id` 沿用全局 `ASSIGN_ID` 雪花策略，`@TableId` 不另外指定类型。
  - `supplier_code` 由用户在新增时手工填写，必填，最长 64 个字符，格式不限。
  - 创建后编码不能修改：前端在修改时禁用编码输入框；后端 `updateByBo` 强制把 `supplierCode` 置空，让它不参与更新。
- Rationale：
  - 雪花 ID 与平台其他实体一致，大致按时间递增，列表可以直接用 `orderByDesc(supplierId)` 实现"新增在前"。
  - 供应商编码往往沿用企业已有的外部编码体系（如 ERP 编码），手工录入最灵活。
  - 编码可能被外部系统或导出文件引用，锁定后可以避免引用失效。
  - 前后端双重锁定，防止有人绕过前端直接改接口。
- Alternatives considered：
  - 系统自动生成编码（例如 `SUP` + 日期 + 流水号）：要引入序列号组件，还要处理并发，而且不一定符合企业既有编码，不采用。
  - 允许修改编码并在修改时校验唯一：会破坏外部引用的稳定性，不采用。

**3. 状态与校验：两层校验，编码唯一性由应用层保证**

- Choice：
  - 状态取值 `0` 正常 / `1` 停用，复用字典 `sys_normal_disable`。Bo 上用 `@Pattern("^[01]?$")` 限制取值，允许空值。
  - 新增时状态为空则默认 `SystemConstants.NORMAL`（启用），与表默认值 `'0'` 一致。修改时状态为空则置为 null，不覆盖原值。
  - 字段校验用 Bean Validation 分组实现：
    - `AddGroup`：编码和名称必填，编码最长 64。
    - `EditGroup`：`supplierId` 必填，名称必填。
    - 两个分组都校验：名称最长 100，联系人和联系电话各最长 50，备注最长 500。
  - 联系电话只限制长度，不校验格式。
  - 新增前由 Controller 调用 `checkCodeUnique` 检查编码是否已存在。查询依靠 MyBatis-Plus 自动追加 `del_flag = '0'`，所以只和未删除的记录比较。如果重复，返回"新增供应商'xxx'失败，供应商编码已存在"。
  - 前端表单只校验编码和名称必填，长度靠输入框的 `maxlength` 限制。
  - 删除不做业务校验：`deleteWithValidByIds` 虽然保留了 `isValid` 参数，但当前没有使用，直接逻辑删除。
- Rationale：
  - 状态复用系统字典，无需新建字典数据，列表标签和导出转换也能直接使用。
  - 联系电话可能是座机、分机或国际号码，强行校验格式容易误拦截。
  - 已删除的编码允许重新使用，符合"删除即作废"的用户预期。
  - 目前还没有其他业务表引用供应商，暂不需要删除前的引用检查。
- Alternatives considered：
  - 用数据库唯一约束兜底：与逻辑删除冲突（见决策 1），不采用。
  - 校验手机号格式：可能误拦截座机和分机号码，不采用。
  - 自定义供应商状态字典：语义与 `sys_normal_disable` 完全相同，重复维护没有收益，不采用。

**4. 权限与菜单：目录 + 菜单 + 5 个按钮，用固定 ID 且脚本可重复执行**

- Choice：
  - `sql/biz/FEAT-20260918-001.sql` 在 `sys_menu` 中插入以下记录：
    - 『业务管理』目录：`1770000000000000000`，`parent_id=0`，`order_num=10`，`path=biz`，图标 `guide`。
    - 『供应商管理』菜单：`...001`，`path=supplier`，`component=biz/supplier/index`，`perms=biz:supplier:list`，图标 `shopping`。
    - 查询、新增、修改、删除、导出 5 个按钮：`...002` 至 `...006`，perms 分别为 `biz:supplier:query/add/edit/remove/export`。
  - 脚本先按固定 ID `delete` 再 `insert`，建表使用 `create table if not exists`。
  - 后端每个接口都用 `@SaCheckPermission` 标注对应权限：
    - `GET /list` → `list`
    - `GET /{id}` → `query`
    - `POST` → `add`
    - `PUT` → `edit`
    - `DELETE /{ids}` → `remove`
    - `POST /export` → `export`
  - 前端工具栏和行内按钮使用 `v-hasPermi`。
- Rationale：
  - 固定 ID 配合先删后插，使脚本可以重复执行，而且同一 ID 在各环境保持一致，`sys_role_menu` 中已有的授权关系也不会失效。
  - 另外增加 `query` 权限，把"查看单条详情"和"看列表"区分开，与平台代码生成器的惯例一致。
  - 前后端使用同一套权限字符串，按钮显隐和接口鉴权一致。
- Alternatives considered：
  - 由菜单自增或雪花 ID 生成：每个环境的 ID 不同，脚本不可重复执行，角色授权也难以迁移，不采用。
  - 只控制列表、新增、修改、删除、导出 5 个权限，不单设 `query`：会与平台惯例不一致，所以保留 `query`（它带来的副作用见 Risks）。
  - 由独立的基础脚本创建『业务管理』目录：会多一个部署依赖。本期由第一个业务变更负责创建。

**5. 导出：POST 接口 + ExcelBuilder + 字典转换，不分页**

- Choice：
  - `POST /biz/supplier/export` 接收与列表相同的查询条件，调用 `queryList` 得到全部符合条件的数据，通过 `ExcelBuilder.of(list, BizSupplierVo.class).sheetName("供应商")` 写入响应。
  - VO 使用 `@ExcelIgnoreUnannotated`，只导出编码、名称、联系人、联系电话、状态、备注 6 列。状态列通过 `ExcelDictConvert` + `sys_normal_disable` 转为中文。
  - 导出记录操作日志（`BusinessType.EXPORT`）。
  - 前端使用 `download` 工具提交当前查询参数，文件名为 `supplier_<时间戳>.xlsx`。
- Rationale：
  - 复用平台导出组件和前端下载工具，实现成本低，行为与系统其他模块一致。
  - 导出结果与当前筛选条件一致，符合用户的直觉。
  - 主键和创建时间对业务人员没有意义，所以不导出。
- Alternatives considered：
  - 异步导出或分批导出：当前供应商数据量有限，不值得引入任务队列，暂不采用。
  - 只导出当前页：与"按条件导出"的需求不符，不采用。

**6. 前端页面结构：单页 CRUD，采用平台标准三段式布局**

- Choice：`views/biz/supplier/index.vue`（组件名 `Supplier`）由三部分组成：
  - 可折叠的筛选卡片：供应商名称输入框（回车即可搜索）、状态下拉框（字典），加上搜索和重置按钮。
  - 表格卡片：
    - 头部显示记录总数。
    - 工具栏有新增、修改（单选时可用）、删除（多选时可用）、导出，以及 `right-toolbar`。
    - 表格有多选列，以及编码、名称、联系人、电话、状态（`dict-tag`）、备注、操作列（行内修改、删除）。
    - 底部是分页组件。
  - 新增/修改共用一个弹窗（宽 500px）：表单默认状态为 `'0'`；修改时先调用 `getSupplier` 拉取详情再回填，编码输入框禁用。
  - 删除前弹出确认框：单行删除显示编码，批量删除显示 ID 列表。
  - 页面复用 `useLoading`、`useFormDialog`、`useSearchReset`、`useSearchToggle`、`useTableSelection` 等 hooks 和 `page-shell` 样式 mixin。
  - 接口封装在 `api/biz/supplier/index.ts`（列表、详情、新增、修改、删除），类型定义在 `types.ts`（`SupplierVO`、`SupplierForm`、`SupplierQuery`）。
- Rationale：
  - 字段少、交互简单，单页加弹窗足够。
  - 与平台其他 CRUD 页面的交互和视觉保持一致，使用者无需重新学习。
  - 复用 hooks 可以减少重复代码。
  - 修改时重新拉取详情，保证回填的是最新数据。
- Alternatives considered：
  - 独立的详情页或编辑页：字段太少，没有必要。
  - 修改时直接用行数据回填、不再请求详情：可以省一次请求，也不依赖 `query` 权限，但可能回填过期数据，而且偏离平台惯例，不采用。

## Risks And Trade-Offs

- **编码唯一性存在并发窗口**：唯一性只在应用层"先查后插"，`supplier_code` 上只有普通索引。两个请求同时新增同一编码时，都可能通过检查。`@RepeatSubmit` 只能挡住同一用户的重复点击，不能解决不同用户的并发。换来的好处是删除后编码可以重新使用。如果今后要严格保证唯一，可以增加 `(supplier_code, del_flag)` 组合唯一索引，并把删除标志改为写入唯一值。
- **修改和查询权限耦合**：前端"修改"会先调用 `GET /biz/supplier/{id}`，该接口要求 `biz:supplier:query`。如果角色只有 `edit` 没有 `query`，点修改会被拒绝。分配角色权限时，需要同时勾选『供应商查询』。
- **删除没有引用校验**：`deleteWithValidByIds` 的 `isValid` 参数目前没有使用。今后采购、入库等单据引用供应商时，要在这里补上引用检查。删除是逻辑删除，数据可以恢复，但页面上没有恢复入口。
- **导出没有数量上限**：`queryList` 一次性加载全部符合条件的数据。供应商数量一旦增长到数万条，可能带来内存和响应时间压力。
- **没有数据权限隔离**：表中记录了 `create_dept`，但查询没有启用 `@DataPermission`。任何有 `list` 权限的用户都能看到全部供应商。这符合"供应商是公共主数据"的定位，但如果要按部门隔离，需要另行改造。
- **修改时状态留空即保持原值**：`updateByBo` 把空状态置为 null，意味着接口无法把状态"清空"，这是有意为之。其他字段（联系人、电话、备注）传空字符串时会被更新为空字符串，行为与状态字段不同。
- **前后端校验不完全对称**：前端只校验必填，长度靠 `maxlength`；后端还校验状态取值和长度。绕过前端直接调用接口的请求仍由后端拦截，但错误信息以后端返回为准。
- **菜单脚本使用固定 ID，且耦合了『业务管理』目录**：
  - 脚本重复执行时会删掉再重建『业务管理』目录，ID 不变，所以其他业务子菜单的 `parent_id` 仍然有效。
  - 后续业务变更不能再插入同一 ID 的目录，否则会冲突或互相覆盖。
  - 脚本中 `create_dept`/`create_by` 写死了 `1761000000000000103`/`1761100000000000001`，依赖这些初始化数据在目标环境中存在。
- **联系电话不校验格式**：录入更灵活，代价是可能存入无效号码。
- **导出不含主键**：导出的 Excel 不能直接作为按 ID 批量更新的导入源。本期没有导入功能，影响有限。

## Files

- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/controller/BizSupplierController.java`：供应商 REST 接口（`/biz/supplier`），负责权限校验、操作日志、防重复提交、新增前的编码唯一性检查和 Excel 导出。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/domain/BizSupplier.java`：对应 `biz_supplier` 表的实体，继承 `BaseEntity` 获得审计字段，`delFlag` 为逻辑删除字段。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/domain/bo/BizSupplierBo.java`：新增、修改、查询的入参对象，按 Add/Edit 分组声明必填、长度和状态取值校验，并自动映射为实体。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/domain/vo/BizSupplierVo.java`：列表和详情的出参对象，同时定义 Excel 导出列和状态字典转换。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/mapper/BizSupplierMapper.java`：继承 `BaseMapperPlus` 的供应商 Mapper，提供通用 CRUD 和 VO 查询。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/IBizSupplierService.java`：供应商服务接口，定义查询、分页、编码唯一性校验、新增、修改、删除的契约。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/impl/BizSupplierServiceImpl.java`：服务实现，包括名称模糊加状态精确的查询条件、按 ID 倒序排序、编码唯一性校验、新增默认启用、修改时忽略编码，以及逻辑删除。
- `backend/ruoyi-modules/ruoyi-biz/src/main/resources/mapper/biz/BizSupplierMapper.xml`：空的 MyBatis 映射文件，为今后的自定义 SQL 预留。
- `frontend/src/api/biz/supplier/index.ts`：前端供应商接口封装，包括列表、详情、新增、修改和删除（支持批量）。
- `frontend/src/api/biz/supplier/types.ts`：前端类型定义，包括列表视图 `SupplierVO`、表单 `SupplierForm` 和查询参数 `SupplierQuery`。
- `frontend/src/views/biz/supplier/index.vue`：供应商管理页面，包含筛选区、带权限按钮的表格和分页、新增/修改弹窗，以及导出操作。
- `sql/biz/FEAT-20260918-001.sql`：可重复执行的部署脚本，创建 `biz_supplier` 表，并写入『业务管理』目录、『供应商管理』菜单和 5 个按钮权限。
