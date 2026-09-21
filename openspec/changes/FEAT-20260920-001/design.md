## Context

**现状**
- ruoyi-platform 基于 RuoYi-Vue-Plus（Spring Boot + MyBatis-Plus + Sa-Token，前端 Vue3 + Element Plus + TypeScript）。业务代码放在 `ruoyi-modules/ruoyi-biz` 模块，按业务域分包（`org.dromara.biz.<域>`）。
- 之前的变更 FEAT-20260918-001 已经建好「业务管理」目录菜单（`menu_id = 1770000000000000000`）和供应商档案（`org.dromara.biz.supplier`，暴露 `IBizSupplierService`），本变更直接依赖这两项。
- 在本变更之前，平台没有采购单据相关的表、接口和页面。

**约束**
- 沿用框架现有约定：实体继承 `BaseEntity`（自动填充创建/更新人、部门、时间），逻辑删除用 `del_flag` + `@TableLogic`，主键用雪花 ID，分层为 Bo/Vo/Entity + MapStruct-Plus（`@AutoMapper`），分页返回 `PageResult`，权限注解用 `@SaCheckPermission`，审计注解用 `@Log`，防重复提交用 `@RepeatSubmit`，Excel 导出用 `ExcelBuilder` + 字典转换。
- 前端沿用平台已有的 hooks（`useFormDialog`、`useTableSelection`、`useDateRangeQuery`、`useSearchReset` 等）、`v-hasPermi` 指令、`dict-tag` 组件和 `page-shell` 样式。
- SQL 脚本必须能重复执行，菜单、字典使用固定 ID 段（`17700000000000000xx`、`17705/17706…`）。
- 采购单号、明细金额、合计金额、单据状态都以后端为准，前端传入的这些值一律忽略。

**涉及的模块**
- 后端：`ruoyi-biz` 下新增 `purchase` 包（controller / domain / bo / vo / mapper / service），以及 `resources/mapper/biz` 下的两个 Mapper XML。
- 跨域依赖：`biz.supplier` 的 `IBizSupplierService`（`queryById`、`queryList`）。
- 系统表：`sys_dict_type` / `sys_dict_data`（单据状态字典）、`sys_menu`（菜单和按钮）。
- 前端：`src/api/biz/purchaseOrder`（接口和类型）、`src/views/biz/purchaseOrder/index.vue`（页面），复用 `@/api/biz/supplier/types` 里的 `SupplierVO`。
- 数据库脚本：`sql/biz/FEAT-20260920-001.sql`。

## Goals

1. 在「业务管理」目录下新增「采购单管理」菜单。采购员在一个页面里就能录入采购单主信息（供应商、下单日期、备注）和多条物料明细（物料名称、数量、单价）。
2. 采购单号由系统自动生成，格式为 `PO + yyyyMMdd + 4 位当日流水号`，保证全局唯一且不会复用。
3. 系统按「数量 × 单价」算出每条明细的金额，再汇总成合计金额。金额统一保留 2 位小数，以后端结果为准。
4. 单据状态只有两种：草稿（0）和已提交（1）。草稿可以修改、删除、提交；提交后单据冻结，成为终态，不能再修改或删除。
5. 列表支持按单号（模糊）、供应商名称（模糊）、状态（精确）、下单日期区间分页查询，可以查看详情（含明细），可以按当前查询条件导出 Excel。
6. 所有接口和页面按钮都受菜单级和按钮级权限控制（list / query / add / edit / remove / submit / export）。
7. 后端接口、前端页面、建表、字典和菜单 SQL 在同一次变更里一起交付。

## Decisions

### 1. 表结构：主子两张表，主表冗余合计金额和供应商名称
- **Choice**：新建 `biz_purchase_order`（主表）和 `biz_purchase_order_detail`（明细子表），用 `order_id` 关联，不建物理外键。
  - 主表：`order_no` 建唯一索引 `uk_biz_purchase_order_no`，`supplier_id`、`order_date` 建普通索引；`status char(1)` 默认 `'0'`；`total_amount decimal(16,2)`；冗余 `supplier_name`。
  - 子表：`quantity int`、`price decimal(14,2)`、`amount decimal(16,2)`，`order_id` 建索引。
  - 两张表都带 `del_flag` 和 `BaseEntity` 审计字段，建表用 `create table if not exists`。
- **Rationale**：
  - 主子表是采购单据的自然建模方式。
  - 合计金额落在主表，列表、导出、按金额排序都不用再聚合明细。
  - `supplier_name` 在保存时从供应商档案取值冗余进来，有两个作用：一是保留下单时刻的快照，二是让列表能直接按名称模糊查询，不用跨表 join。
  - 金额用 `decimal` 存储，避免浮点误差。
  - 不建外键，符合 RuoYi 的惯例，也便于逻辑删除。
- **Alternatives considered**：
  - 明细用 JSON 列存在主表里：不方便按物料查询，也不符合框架习惯，放弃。
  - 合计金额不落库、查询时实时 `sum`：列表和导出都要额外聚合，放弃。
  - 只存 `supplier_id`、查询时 join 供应商表：供应商改名会影响历史单据，模糊查询也要跨表，放弃。

### 2. 单号规则：PO + 下单日期 + 当日最大流水号加一，唯一索引兜底并重试
- **Choice**：
  - 单号格式为 `PO` + `yyyyMMdd`（按**下单日期**，不是创建日期）+ 4 位左补零流水号。
  - 流水号的取法：`selectMaxOrderNoByPrefix` 按前缀查出已占用的最大单号（先按 `length(order_no) desc` 再按 `order_no desc` 排序，并且**不过滤 `del_flag`**），解析出流水号后加一。
  - 插入时如果撞上 `DuplicateKeyException`，重新取号重试，最多 5 次；重试用尽后抛出「采购单号生成冲突，请稍后重试」。
  - 流水号不合法（非数字或超过 18 位）时按 0 处理。
  - 修改单据时，单号强制置空、不参与更新。
- **Rationale**：
  - 单号里带下单日期，业务上更直观。回填历史日期或预填未来日期时，按该日期的已占用最大号续号，不会冲突。
  - 把已逻辑删除的单据也算进来，保证单号永远不会被复用，方便审计追溯。
  - 按长度排序，保证流水号超过 9999 变成 5 位时仍然能取到真正的最大值。
  - 并发下两个请求可能算出同一个号，由唯一索引 + 有限次重试解决，不用引入额外组件。
- **Alternatives considered**：
  - Redis 自增序列：需要处理 Redis 与数据库一致性、按日重置、数据恢复等问题，放弃。
  - 独立的序号表加 `select … for update`：多一张表和锁竞争，当前量级不需要，放弃。
  - 按创建时间生成：与业务日期脱节，回填单据会让人困惑，放弃。
  - 允许用户手输单号：违背「系统自动生成」的目标，放弃。

### 3. 金额计算：后端 BigDecimal 权威计算，前端只做预览
- **Choice**：
  - 后端 `buildDetails` 里：单价先 `setScale(2, HALF_UP)`，明细金额 = 单价 × 数量后再 `setScale(2, HALF_UP)`；合计金额 = 明细金额之和（`sumAmount`）。
  - Bo 里的 `amount`、`totalAmount` 注释写明「提交的值被忽略」。
  - 前端 `rowAmount` / `formTotalAmount` 用 Number 实时算出预览值，展示为 2 位小数；提交时只回传物料名称、数量、单价。
- **Rationale**：金额只有一个权威来源，可以防止篡改和前后端口径不一致；前端预览让用户录入时能即时看到结果。
- **Alternatives considered**：采信前端算好的金额、后端只做校验：多一套比对逻辑，还要考虑容差，放弃。

### 4. 状态与校验：二态状态机，后端强制只有草稿可以变更
- **Choice**：
  - 状态常量：`STATUS_DRAFT = "0"`、`STATUS_SUBMITTED = "1"`。新增时固定写草稿。修改时 `status` 置空，不允许通过修改接口改状态。只有专用接口 `PUT /submit/{orderId}` 能把状态改为已提交。
  - `loadDraft` 统一校验「单据存在且为草稿」，修改和提交都会调用；批量删除时逐条校验，只要有一张已提交就整体拒绝，并且要求查到的条数等于入参条数。
  - 提交前再检查一次明细数量大于 0。
  - 供应商必须存在且为启用状态（`loadEnabledSupplier`）。新增和修改都会校验，下拉框也只列出启用的供应商。
  - 字段校验分两层：
    - Bean Validation（Add/Edit 分组）：供应商和下单日期必填；明细非空，并且用 `@Valid` 级联；物料名称必填、最长 200 字；数量 > 0、`@Digits(9,0)`；单价 > 0、`@Digits(10,2)`；备注最长 500 字。
    - 服务层兜底：`toQuantity` 用 `intValueExact` 确保数量是正整数。
  - Bo 中的数量用 `BigDecimal` 接收，这样传入小数时能返回可读的业务提示，而不是 JSON 反序列化错误。
  - 修改明细采用「整体替换」：先逻辑删除原有全部明细，再批量插入本次提交的明细，不按 `detailId` 做差异比对。
  - 新增、修改、提交、删除都加了 `@Transactional(rollbackFor = Exception.class)`。
  - 前端做同样的校验，给出按行号定位的提示；非草稿行的「修改 / 提交 / 删除」按钮置灰；批量操作要求勾选的全部是草稿。
- **Rationale**：
  - 两态已经够用，把终态冻结放在后端强制执行，不依赖前端置灰。
  - 整体替换明细的实现最简单，语义也清楚：以本次提交为准。
  - 停用供应商不能再下新单，但历史单据的回显不受影响（见决策 7）。
- **Alternatives considered**：
  - 引入审批流或更多状态（审核、作废等）：超出本次范围，放弃。
  - 按 `detailId` 做增、删、改差异合并：实现复杂，收益有限，放弃。
  - 用乐观锁版本号防并发：本次没有采用，见 Risks。

### 5. 权限与菜单：一个菜单加六个按钮，接口逐一绑定权限
- **Choice**：
  - 菜单：「采购单管理」`C` 类型菜单（`menu_id 1770000000000000010`），挂在「业务管理」目录下，`order_num = 2`，路由 `purchaseOrder`，组件 `biz/purchaseOrder/index`，权限 `biz:purchaseOrder:list`。
  - 按钮：六个 `F` 类型按钮（`…011`～`…016`），分别对应 `query`、`add`、`edit`、`remove`、`submit`、`export`。
  - 字典：新增 `biz_purchase_order_status`（0 草稿 / info，1 已提交 / success）。
  - 脚本先删除固定 ID 的记录再插入，可以重复执行。
  - 后端每个接口都用 `@SaCheckPermission` 绑定对应权限，供应商候选接口 `/supplierOptions` 复用 `list` 权限。
  - 写操作都加 `@Log` 审计；新增、修改、提交还加了 `@RepeatSubmit`。
  - 前端所有按钮用 `v-hasPermi` 控制是否显示。
- **Rationale**：
  - 「提交」单独设一个按钮权限，可以把「录入」和「提交」分给不同角色。
  - 供应商候选只在本页面使用，不应该要求用户额外拥有供应商管理的权限，所以在采购单控制器里提供一个受 `list` 权限保护的只读接口。
- **Alternatives considered**：
  - 前端直接调用供应商模块的列表接口：会要求用户同时拥有 `biz:supplier:list` 权限，耦合权限模型，放弃。
  - 提交复用 `edit` 权限：无法分离职责，放弃。

### 6. 导出：只导出主表，一张单一行，沿用查询条件
- **Choice**：
  - 用专门的 `BizPurchaseOrderExportVo`（`@ExcelIgnoreUnannotated`），导出列为：采购单号、供应商、下单日期（转成 `yyyy-MM-dd` 字符串）、状态（`ExcelDictConvert` 按字典翻译）、合计金额、备注。Sheet 名为「采购单」。
  - 导出复用 `buildQueryWrapper`，所以条件和排序与列表一致，但不分页，导出全部匹配数据。
  - 前端导出时传入当前查询参数（含日期区间）。
- **Rationale**：
  - 满足对账和汇总的主要需求；导出结构扁平，一行对应一张单，容易在 Excel 里处理。
  - 导出对象独立定义，列表 Vo 里的 `details`、`createTime` 等字段不会混进 Excel。
- **Alternatives considered**：
  - 主从展开（每条明细一行，重复主表字段）或多 Sheet：复杂度更高，本期需求没有要求，放弃。
  - 直接在 `BizPurchaseOrderVo` 上加 Excel 注解：与接口返回结构耦合，放弃。

### 7. 前端页面结构：单页列表 + 主子表编辑弹窗 + 详情弹窗
- **Choice**：
  - `index.vue` 由三部分组成：
    - 可折叠的筛选卡片：单号、供应商名称、状态字典下拉、下单日期 `daterange`（由 `useDateRangeQuery('OrderDate')` 转成 `params.beginOrderDate / endOrderDate`）。
    - 列表卡片：工具栏有新增、修改、删除、导出；表格列包括单号、供应商、下单日期、状态标签、合计金额、备注、创建时间，操作列有详情、修改、提交、删除；底部分页。
    - 两个弹窗：
      - 新增 / 修改弹窗（900px）：上半部分是主表字段，单号只在修改时以只读方式显示；下半部分是可编辑的明细表格，支持添加行、删除行，每行实时显示金额，底部显示合计。
      - 只读详情弹窗：`el-descriptions` 展示主表信息，下方是明细表格。
  - 供应商选择：用「关键词输入框 + 下拉框」的组合做本地过滤；已选中的供应商始终保留在候选里。修改时如果原供应商已停用，会插入一个带「（已停用）」标记的禁用项，只用于回显。
  - 提交单据前弹出二次确认，提示「提交后将不能再修改和删除」。
- **Rationale**：
  - 满足「一个页面内录入主信息和多条明细」的目标。
  - 结构和平台其他 CRUD 页面保持一致（相同的 hooks 和 `page-shell` 样式），降低学习和维护成本。
  - 停用供应商的回显问题通过禁用项解决，避免下拉框显示原始 ID；同时后端仍然会拒绝以停用供应商保存。
- **Alternatives considered**：
  - 独立的编辑路由页或抽屉：页面切换多，也和现有 CRUD 风格不一致，放弃。
  - 供应商远程搜索（`remote` select）：当前启用供应商数量有限，一次性加载更简单，放弃。

### 8. 查询与排序
- **Choice**：
  - 查询条件：单号和供应商名称用 `like`，`supplierId` 和状态用 `eq`，下单日期用 `ge` / `le`（空白参数视为未填）。
  - 排序：按下单日期倒序、创建时间倒序、主键倒序。
  - 详情接口返回主表和按 `detail_id` 升序排列的明细；列表接口不返回明细。
- **Rationale**：最新的单据排在最前；加上主键排序，保证分页结果稳定；列表不带明细，避免 N+1 查询和多余的传输。
- **Alternatives considered**：列表附带明细摘要。本期不需要，放弃。

## Risks And Trade-Offs

- **草稿校验与写入之间存在竞态**：`loadDraft` 先查状态再 `updateById`，更新条件里没有带 `status = '0'`，也没有版本号。如果「修改」和「提交」几乎同时发生，已提交的单据可能被改写，或者两次提交都返回成功。目前靠 `@RepeatSubmit` 和低并发的使用场景缓解，后续可以改成条件更新（`where status = '0'`），根据影响行数判断是否成功。
- **修改下单日期后单号不变**：修改时单号保持原样，如果改了下单日期，单号里的日期就和 `order_date` 对不上了。这是为了保持单号稳定性做的取舍，需要在使用说明里说清楚，或者后续在修改时限制跨日期调整。
- **流水号策略**：按「最大号加一」取号，高并发下重试成本会上升，5 次重试用尽会直接报错。取号查询走的是 `like 'POyyyyMMdd%'` 前缀匹配，能用上唯一索引。因为已删除单据也占号，流水号会出现「空洞」，这是有意为之。当日流水号超过 9999 后会自动变成 5 位，单号长度随之变化。
- **明细整体替换**：每次修改都会逻辑删除全部旧明细再插入新明细，`detail_id` 每次都会变，逻辑删除的记录会越积越多。如果以后有其他单据按 `detail_id` 引用明细（比如入库单），需要改成差异合并。
- **前后端金额口径**：前端预览用 JavaScript Number 计算，极端情况下（比如大额 × 大数量）显示可能和后端 `HALF_UP` 的结果差 0.01。保存后以后端返回为准，列表和详情展示的都是后端数值。
- **供应商名称快照**：供应商档案改名后，历史单据仍然显示旧名称，按名称查询时也是按快照名称匹配。这是保留历史的取舍，按 `supplierId` 查询不受影响（后端支持，但当前前端没有提供这个筛选项）。
- **停用供应商的草稿**：原供应商被停用后，这张草稿必须先换成启用的供应商才能保存修改；但提交接口不校验供应商状态，仍然可以直接提交。
- **导出规模**：导出不分页，会一次性加载全部匹配数据，数据量很大时有内存和响应时间压力。另外导出不含明细，如果需要明细级报表，需要另行扩展。
- **批量删除的严格校验**：只要有一张单据不存在或已提交，整批都会被拒绝，不会部分成功。这种方式语义清楚，但用户需要先把已提交的单据取消勾选。
- **强依赖前置变更**：SQL 依赖 FEAT-20260918-001 创建的「业务管理」目录和供应商表，执行顺序不能颠倒。菜单、字典脚本先删后插，会覆盖对这些固定 ID 记录的手工调整。
- **数据权限**：本次没有配置数据权限（部门、本人范围），拥有 `list` 权限的用户能看到全部采购单。

## Files

- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/controller/BizPurchaseOrderController.java`：REST 入口 `/biz/purchaseOrder`，提供列表、供应商候选、导出、详情、新增、修改、提交、删除接口，并绑定权限、审计日志和防重复提交注解。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/BizPurchaseOrder.java`：采购单主表实体，映射 `biz_purchase_order`，带逻辑删除字段。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/BizPurchaseOrderDetail.java`：采购单明细实体，映射 `biz_purchase_order_detail`，带逻辑删除字段。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/bo/BizPurchaseOrderBo.java`：采购单入参对象，兼作新增、修改请求体和查询条件，定义主表字段的分组校验和明细的级联校验。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/bo/BizPurchaseOrderDetailBo.java`：明细入参对象，校验物料名称、数量（正整数）和单价（大于 0、最多 2 位小数）。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/vo/BizPurchaseOrderDetailVo.java`：明细视图对象，用于详情接口返回。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/vo/BizPurchaseOrderExportVo.java`：Excel 导出对象，只含主表列，状态按字典翻译。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/vo/BizPurchaseOrderVo.java`：采购单视图对象，列表和详情共用，只有详情接口会填充明细。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/mapper/BizPurchaseOrderDetailMapper.java`：明细 Mapper，继承 `BaseMapperPlus`，提供通用增删改查和批量插入。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/mapper/BizPurchaseOrderMapper.java`：主表 Mapper，额外声明按前缀查询最大单号的方法 `selectMaxOrderNoByPrefix`。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/service/IBizPurchaseOrderService.java`：采购单服务接口，定义查询、导出、供应商候选、增、改、提交、删除等契约。
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/service/impl/BizPurchaseOrderServiceImpl.java`：核心业务实现，包括单号生成和冲突重试、金额计算、草稿状态校验、供应商启用校验、明细整体替换和事务控制。
- `backend/ruoyi-modules/ruoyi-biz/src/main/resources/mapper/biz/BizPurchaseOrderDetailMapper.xml`：明细 Mapper 的 XML 占位文件，目前没有自定义 SQL。
- `backend/ruoyi-modules/ruoyi-biz/src/main/resources/mapper/biz/BizPurchaseOrderMapper.xml`：定义 `selectMaxOrderNoByPrefix`，查询时不过滤 `del_flag`，保证单号不被复用。
- `frontend/src/api/biz/purchaseOrder/index.ts`：前端采购单接口封装，包括列表、供应商候选、详情、新增、修改、提交、删除。
- `frontend/src/api/biz/purchaseOrder/types.ts`：前端类型定义，包括采购单和明细的 VO、表单类型，以及查询参数类型。
- `frontend/src/views/biz/purchaseOrder/index.vue`：采购单管理页面，包含筛选区、列表和工具栏、主子表编辑弹窗（带金额实时预览和供应商过滤）、详情弹窗、导出功能。
- `sql/biz/FEAT-20260920-001.sql`：可重复执行的数据库脚本，负责建主子表、初始化单据状态字典、在「业务管理」下插入「采购单管理」菜单及六个按钮权限。
