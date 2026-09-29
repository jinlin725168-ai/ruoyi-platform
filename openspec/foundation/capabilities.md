# 能力清单

对应底座版本：1.0.19，生成日期：2026-09-28

## 一、上游自带

| 能力 | 入口路径 | 可复用点 |
|---|---|---|
| 登录与多客户端 | `/auth/login`（`AuthController`）；`sys_client` 表；`/system/client` | 密码、短信、邮箱、社交、小程序登录策略（`IAuthStrategy`）；验证码可开关；密码错误锁定 |
| RBAC | `/system/user`、`/system/role`、`/system/menu`、`/system/dept`、`/system/post` | 菜单分三类：目录 M、菜单 C、按钮 F；按钮级权限串；`ruoyi-api` 的 `UserService`、`DeptService`、`RoleService`、`PostService` |
| 数据权限 | `@DataPermission` 标注在 Mapper 方法上（示例 `TestDemoMapper`） | 角色数据范围：全部、自定义、本部门、本部门及以下、仅本人 |
| 字典 | `/system/dict/type`、`/system/dict/data`；前端 `useDict` | `DictService`（带缓存，修改后立即生效）；`@DictPattern`；`ExcelDictConvert`；`DictTag` |
| 系统参数 | `/system/config` | `ConfigService.getConfigValue` 等 |
| 通知、站内消息与推送 | `/system/notice`、`/resource/message`、`{message.path}` | `MessageService` |
| 对象存储 | `/resource/oss`、`/resource/oss/config` | `OssService`；前端 `FileUpload`、`ImageUpload` |
| 日志与监控 | `/monitor/operlog`、`/monitor/loginInfo`、`/monitor/online`、`/monitor/cache` | `@Log` 自动写入操作日志 |
| 代码生成器 | `/tool/gen`；`ruoyi-gen/src/main/resources/fm/**` | 模板作为写法对照 |
| 工作流 | `/workflow/**`（Warm-Flow） | `WorkflowService`，以及流程事件 `ProcessEvent` 等 |
| 横切能力 | 各 `ruoyi-common-*` | Excel 导入导出、防重复提交、限流、分布式锁、接口与字段加密、脱敏、翻译、XSS、i18n、springdoc |
| 演示 | `/demo/**`（`ruoyi-demo`） | 单表和树表的参考实现 |
| 种子数据 | `backend/script/sql/ry_vue.sql`、`ry_workflow.sql` | 预置用户、角色、字典（如 `sys_normal_disable`），以及默认客户端 |

**未启用或不存在**：

- 多租户。
- `@Scheduled` 定时任务。
- dev 和 smoke 运行档里关闭的：SnailJob、Snail AI、MQTT、Elasticsearch、邮件、MCP 客户端、Spring Boot Admin 客户端；smoke 运行档还关闭了验证码、接口加密和消息推送。
- 冒烟不导入 `ry_job.sql`、`ry_ai.sql`。

## 二、本仓库已实现

以活规格为准，这里只列 Requirement 标题和入口，不重述细节。场景 ID（A1、A2…）与验收 manifest 的 `criteria` 对应。

### supplier-management（`openspec/specs/supplier-management/spec.md`）

- **需求标题**：
  - 『业务管理』目录与供应商管理菜单
  - 分页查询供应商
  - 新增供应商
  - 修改供应商
  - 删除供应商
  - 导出供应商 Excel
  - 按钮级权限控制
  - 供应商分类字典
- **入口**：
  - 接口 `/biz/supplier/**`（`BizSupplierController`）。
  - 页面 `/biz/supplier`（`frontend/src/views/biz/supplier/index.vue`）。
  - 表 `biz_supplier`；字典 `biz_supplier_category`。
  - SQL：`sql/biz/FEAT-20260918-001.sql`、`FEAT-20260921-001.sql`。
- **对应变更**：
  - FEAT-20260918-001：首版单表增删改查、导出、按钮权限。
  - FEAT-20260921-001：供应商分类与『未分类』。
  - FEAT-20260923-002：名称查询去首尾空白、不区分大小写。
  - FEAT-20260924-001：编码查询条件。

### purchase-order（`openspec/specs/purchase-order/spec.md`）

- **需求标题**：
  - 采购单分页查询
  - 新增采购单及其明细
  - 修改草稿采购单
  - 查看采购单详情
  - 删除草稿采购单
  - 提交采购单
  - 导出采购单 Excel
  - 菜单与按钮级权限控制
  - 采购单备注录入
  - 采购单备注展示
- **入口**：
  - 接口 `/biz/purchaseOrder/**`（`BizPurchaseOrderController`）。
  - 页面 `/biz/purchaseOrder`（`frontend/src/views/biz/purchaseOrder/index.vue`）。
  - 表 `biz_purchase_order`、`biz_purchase_order_detail`；字典 `biz_purchase_order_status`。
  - SQL：`sql/biz/FEAT-20260920-001.sql`。
- **对应变更**：
  - FEAT-20260920-001：主子表、自动单号、状态流转、导出。
  - FEAT-20260923-001：列表和导出显示供应商分类，并可按分类筛选。
  - FEAT-20260924-002：按供应商名称查询。
  - FEAT-20260928-002：备注。

每个变更的完整材料在 `openspec/changes/<FEAT-id>/`（proposal、design、decisions、增量规格等），证据报告在 `reports/storyloop/<FEAT-id>/report.md`。

## 三、能力之间的关系

- **采购单依赖供应商**：`BizPurchaseOrderServiceImpl` 注入 `IBizSupplierService`。
  - 下拉选项和下单校验只取启用状态的供应商（`queryList`、`queryById`）。
  - 供应商分类的显示和筛选取供应商档案上的当前分类，包括已逻辑删除的供应商（`queryCategoryLabels`、`querySupplierIdsByCategory`、`queryCategorizedSupplierIds`）。
  - 采购单上冗余保存下单时的 `supplier_name`，按供应商名称查询时查的是这个冗余字段。
- **两者都依赖上游字典**（`DictService`，`biz_supplier_category`、`biz_purchase_order_status`、`sys_normal_disable`），『未分类』的口径在两个能力里一致（`SupplierConstants.CATEGORY_NONE`、`CATEGORY_NONE_LABEL`）。
- **两者都依赖上游的 RBAC 与菜单**（『业务管理』目录 `1770000000000000000`），以及操作日志、Excel 导出、防重复提交。
- **两者都没有用数据权限**：规格明确不按部门隔离数据。
