## Context
FEAT-20260923-001 要在采购单列表和 Excel 导出里显示供应商分类，并支持按分类单选筛选。分类实时取供应商档案上的当前分类，口径和供应商管理一致：取字典名称，分类为空或已失效时显示『未分类』。按已确认的澄清，采购单关联的供应商被逻辑删除后，仍按该供应商记录上保留的分类显示和筛选。现有基础：`org.dromara.biz.purchase`（BizPurchaseOrder*），`org.dromara.biz.supplier`（BizSupplierServiceImpl 已有 fillCategoryLabel、CATEGORY_NONE='__none__'、CATEGORY_NONE_LABEL='未分类'）。前端 `views/biz/purchaseOrder/index.vue` 和 `api/biz/purchaseOrder/types.ts` 已存在；供应商页面已有『未分类』选项，用的是 SUPPLIER_CATEGORY_NONE。

## Goals
- 列表每行返回 `supplierCategoryLabel`（字典名称或『未分类』），已删除的供应商也一样。
- 列表和导出都支持 `supplierCategory` 查询条件：字典值匹配当前分类等于该值的采购单；`__none__` 匹配分类为空或已失效的采购单；可与单号、供应商、状态、日期条件组合。
- 导出新增『供应商分类』列，取值口径和列表一致，筛选条件也相同。
- 前端新增分类下拉（字典选项加『未分类』）和『供应商分类』表格列。
- 不做：不存分类快照；详情和表单不显示分类；不支持多选；不改字典；没有 SQL 变更。

## Tests First
运行命令：`mvn -q -o -f backend/pom.xml -pl ruoyi-modules/ruoyi-biz -Dmaven.test.skip=false -DskipTests=false -Dtest=<Class> -Dsurefire.failIfNoSpecifiedTests=false test`。

### BizSupplierCategoryLookupTest（ruoyi-biz/src/test/java/org/dromara/biz/supplier/）
先是编译失败（`selectCategoriesIgnoreDeleted`、`queryCategoryLabels` 等方法不存在）；接着加了只返回空值的桩方法，得到行为失败：
- `queryCategoryLabelsTranslatesValidAndFallsBackToUncategorized`：期望 {1=原材料, 2/3/4=未分类}，实际是 `{}`，失败。
- `querySupplierIdsByCategoryIncludesDeletedSuppliers`：期望 [7, 8]，实际是 `[]`，失败。
- `queryCategorizedSupplierIdsUsesCurrentDictValues`：期望 [5]，实际是 `[]`，失败。
- `queryCategorizedSupplierIdsIsEmptyWhenDictIsEmpty`：失败，Mockito 报 UnnecessaryStubbing，因为桩方法没有去读字典。
- `queryCategoryLabelsSkipsQueryWhenNoSupplier`：在桩实现下已经通过（桩本来就返回空，不查询），作为边界守卫保留。
实现 XML 查询和服务方法后，5 个测试全部通过。

### BizPurchaseOrderSupplierCategoryTest（ruoyi-biz/src/test/java/org/dromara/biz/purchase/）
先只加字段（Bo.supplierCategory、Vo 和 ExportVo 的 supplierCategoryLabel），让测试能编译，然后观察失败：
- `pageRowsShowSupplierCategoryLabelOrUncategorized`：实际是 [null, null, null]，期望 [原材料, 未分类, 未分类]，失败。
- `filterBySpecificCategoryKeepsOnlyOrdersOfMatchingSuppliers`：SQL 片段只有 `(status = ...) ORDER BY ...`，缺少 `supplier_id IN`，失败。
- `filterByCategoryWithoutMatchingSupplierReturnsNothing`：缺少 `1 = 0`，失败。
- `filterUncategorizedExcludesOrdersOfCategorizedSuppliers`：缺少 `supplier_id NOT IN`，失败。
- `filterUncategorizedWithoutCategorizedSupplierKeepsAllOrders`：失败，报 UnnecessaryStubbing，因为没有调用 queryCategorizedSupplierIds。
- `exportRowsCarrySupplierCategoryLabelUnderSameFilter`：实际是 [null, null]，期望 [服务, 未分类]，失败。
- `noCategoryConditionDoesNotLookUpSuppliers`：在实现前已经通过，作为防回归守卫保留。
实现 fillSupplierCategoryLabel 和 applySupplierCategory 后，7 个测试全部通过。

关于 testing.md 里的待验证项：在纯 Mockito 测试中，`@BeforeAll` 里调用 `TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), BizPurchaseOrder.class)` 后，就能用 `LambdaQueryWrapper.getSqlSegment()` 和 `getParamNameValuePairs()` 断言查询条件；也可以直接给 mock 的 `selectVoPage` / `selectVoList` 打桩，这两条路径都不经过 MapstructUtils。

最终结果：回归命令 `mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test` 通过；两个新测试类在 ruoyi-biz/target/surefire-reports 下都有报告。`pnpm --dir frontend exec vue-tsc --noEmit` 通过。

## Decisions
- **分类查询放在供应商服务里（IBizSupplierService）**
  - Choice：新增 `queryCategoryLabels`、`querySupplierIdsByCategory`、`queryCategorizedSupplierIds` 三个方法，由采购单服务调用。
  - Rationale：供应商模块本来就负责分类字典的规则（名称翻译、『未分类』的含义），和供应商管理共用 `categoryLabel` 辅助方法，才能保证『口径和供应商管理一致』；采购单服务原来就已经依赖 IBizSupplierService。
  - Alternatives considered：在采购单 XML 里 join biz_supplier 并注入 DictService（会重复一份分类规则）；在采购单服务里直接用 BizSupplierMapper（违反服务边界）。
- **自定义 XML 查询，不过滤 del_flag**
  - Choice：`selectCategoriesIgnoreDeleted` 和 `selectIdsByCategoriesIgnoreDeleted` 写在 BizSupplierMapper.xml 里。
  - Rationale：MyBatis-Plus 的 @TableLogic 会给 wrapper 查询自动加 del_flag 条件，而已删除供应商的分类必须仍然参与显示和筛选（A44/A47/A48）。自定义 XML 不受这个条件影响，写法和现有的 selectMaxOrderNoByPrefix 一致。
  - Alternatives considered：用 `DataPermissionHelper` 或拦截器忽略逻辑删除（没有现成机制）；在采购单上存分类快照（明确不做）。
- **用供应商 ID 集合过滤，不用 SQL 子查询**
  - Choice：选具体分类时用 `supplier_id IN (ids)`，集合为空时 `apply("1 = 0")`；选『未分类』时用 `supplier_id NOT IN (分类有效的供应商 ids)`，集合为空时不加条件。
  - Rationale：分页（selectVoPage）和导出继续复用 buildQueryWrapper 和默认排序；参数全部绑定，不拼接 SQL；NOT IN 的写法还能把供应商记录已不存在的单据归入『未分类』，和显示时的兜底一致。
  - Alternatives considered：用 `inSql` 子查询（要拼字符串，有注入风险）；写自定义 XML 分页 join（会绕开现有的 wrapper 和 PageQuery 写法）。
- **『未分类』的取值沿用 `__none__`**
  - Choice：复用 SupplierConstants.CATEGORY_NONE，前端复用 SUPPLIER_CATEGORY_NONE。
  - Rationale：和供应商管理的查询条件保持一致。
  - Alternatives considered：新增专门的布尔参数。
- **标签字段只在列表和导出里填充**
  - Choice：只在 queryPageList 和 queryExportList 中填充 supplierCategoryLabel，queryById 不填。
  - Rationale：规格明确详情不展示供应商分类。
  - Alternatives considered：所有读取接口都填充。

## Risks And Trade-Offs
- 按分类筛选时会先把匹配的供应商 ID 集合读出来，再作为 IN / NOT IN 参数。供应商数量大（几千以上）时参数列表会变长；以目前的数据规模可以接受，将来可以改成 join 或子查询的 XML。
- 每次列表或导出会多一次按本页供应商 ID 的查询；字典读取走缓存。
- 字典为空时所有采购单都算『未分类』，这时『未分类』筛选不加任何条件，和供应商管理的行为一致。
- 如果筛选时传入的分类值不在字典里，按精确匹配处理（和供应商管理一致），但这些单据显示的是『未分类』。前端只提供字典选项加『未分类』，所以正常操作不会遇到。
- 冒烟（A4、A25–A27、A36–A48）需要 Docker、MySQL 和 Playwright 环境，本地没有运行，由外部验收执行。

## Files
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/mapper/BizSupplierMapper.java：新增 selectCategoriesIgnoreDeleted、selectIdsByCategoriesIgnoreDeleted。
- backend/ruoyi-modules/ruoyi-biz/src/main/resources/mapper/biz/BizSupplierMapper.xml：上面两个方法的 SQL，不带 del_flag 过滤。
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/IBizSupplierService.java：声明三个分类查询方法。
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/impl/BizSupplierServiceImpl.java：实现三个方法，并把名称翻译提取为公共的 categoryLabel。
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/bo/BizPurchaseOrderBo.java：新增 supplierCategory 查询条件。
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/vo/BizPurchaseOrderVo.java：新增 supplierCategoryLabel。
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/domain/vo/BizPurchaseOrderExportVo.java：新增『供应商分类』导出列。
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/service/impl/BizPurchaseOrderServiceImpl.java：新增 applySupplierCategory（筛选）和 fillSupplierCategoryLabel（列表和导出）。
- backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/supplier/BizSupplierCategoryLookupTest.java：供应商分类查询的单元测试。
- backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/purchase/BizPurchaseOrderSupplierCategoryTest.java：采购单分类显示、筛选和导出的单元测试。
- frontend/src/api/biz/purchaseOrder/types.ts：PurchaseOrderVO 新增 supplierCategoryLabel，PurchaseOrderQuery 新增 supplierCategory。
- frontend/src/views/biz/purchaseOrder/index.vue：新增『供应商分类』查询下拉（biz_supplier_category 加『未分类』）和『供应商分类』表格列。
