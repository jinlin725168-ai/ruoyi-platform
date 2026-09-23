# 底座已有能力

## 平台能力（来自 RuoYi-Vue-Plus 6.X 和 plus-ui）

### 身份与权限

- 账号密码登录（图形验证码可开关），以及短信、邮箱、第三方社交（JustAuth）、小程序登录策略。
- 多客户端：`sys_client` 管理 clientId、支持的授权类型、token 时效、设备类型、访问路径和 IP 白名单。
- 注册（由系统参数控制）、密码错误次数锁定、在线用户管理与强制下线。
- RBAC：用户、角色、菜单（目录 M、菜单 C、按钮 F）、部门、岗位。
- 按钮级权限串，由 `@SaCheckPermission` 和 `v-hasPermi` 两端配合。
- 角色数据范围（全部、自定义、本部门、本部门及以下、仅本人），通过 `@DataPermission` 在 Mapper 上生效。

### 系统管理

- 字典类型与字典数据：前端 `useDict` 使用，后端 `DictService` 和 Excel 字典转换使用。
- 系统参数（`ConfigService`）、通知公告、站内消息与推送（SSE/WebSocket）。
- OSS 对象存储：S3 协议，多套配置，文件上传下载。
- 客户端管理、第三方账号绑定。

### 系统监控

- 操作日志：由 `@Log` 产生，可查询、导出、清空。
- 登录日志：可解锁账号。
- 在线用户、缓存监控。
- Spring Boot Admin（独立应用，默认关闭）、SnailJob 调度中心（独立应用，默认关闭）。

### 系统工具

代码生成器（`/tool/gen`）：从数据库表导入，生成 Java、XML、SQL、Vue 或 React 代码。

### 工作流

Warm-Flow 流程分类、流程定义（设计器、发布、导入导出）、流程实例、待办、已办、抄送、转办、退回、终止、催办、流程变量；请假示例 `test_leave`；`WorkflowService` 供业务模块发起和办理流程。

### 横切能力

- 接口加解密（`@ApiEncrypt`）、数据库字段加密（`@EncryptField`）。
- 响应脱敏（`@Sensitive`）、翻译（`@Translation`）。
- XSS 过滤、防重复提交、限流、分布式锁。
- Excel 导入导出（字典与枚举转换、合并单元格、下拉选项、模板导出）。
- 国际化（`i18n/messages*`）、接口文档（springdoc，分组不含 biz）、MCP 服务端。

### 演示

`ruoyi-demo` 里的单表、树表、缓存、锁、队列、邮件、短信、MQTT、ES 等示例（菜单『测试菜单』）。

### 种子数据

- `backend/script/sql/ry_vue.sql`：`sys_*` 表、`gen_*` 表、演示表；顶级菜单为系统管理、系统监控、系统工具、测试菜单、PLUS 官网。
- 预置用户：`admin`（超级管理员角色 `superadmin`）、`test`、`test1`；预置角色：`superadmin`、`test1`（本部门及以下）、`test2`（仅本人）。
- 预置字典，包括 `sys_normal_disable`、`sys_user_sex`、`sys_yes_no` 等，以及默认客户端。
- `ry_workflow.sql`：`flow_category`、`flow_instance_biz_ext`、`test_leave`，以及 Warm-Flow 的表和菜单。
- `ry_job.sql`、`ry_ai.sql`：冒烟不导入。

### 未启用或不存在的能力

- 没有多租户。
- 没有 `@Scheduled` 定时任务。
- dev 和 smoke 运行档里，SnailJob、Snail AI、MQTT、Elasticsearch、邮件、MCP 客户端、Spring Boot Admin 客户端都关闭。

## 业务能力（ruoyi-biz，已验收合并）

| 变更 | 能力 | 落点 |
|---|---|---|
| FEAT-20260918-001 | 『业务管理』顶级目录；供应商档案的增删改查、导出、按钮级权限 | `biz_supplier`；`org.dromara.biz.supplier`；`views/biz/supplier`；`sql/biz/FEAT-20260918-001.sql` |
| FEAT-20260920-001 | 采购单主子表：自动单号、金额计算、草稿到已提交的状态流转、导出、提交权限 | `biz_purchase_order`、`biz_purchase_order_detail`，字典 `biz_purchase_order_status`；`org.dromara.biz.purchase`；`views/biz/purchaseOrder`；`sql/biz/FEAT-20260920-001.sql` |
| FEAT-20260921-001 | 供应商分类：字典 `biz_supplier_category`（原材料、服务、设备），『未分类』筛选与显示，新增和修改时分类必填并校验 | 给 `biz_supplier.supplier_category` 加列；`SupplierConstants`；`sql/biz/FEAT-20260921-001.sql` |

## 活规格摘要（`openspec/specs/`）

活规格是需求的真源，下面只是摘要。每条场景的 ID（A1、A2…）与 `acceptance/smoke/<change-id>/manifest.json` 里的 `criteria` 对应。

### supplier-management（`openspec/specs/supplier-management/spec.md`）

- **菜单**：『业务管理』为顶级目录，其下有『供应商管理』菜单，以及查询、新增、修改、删除、导出五个按钮权限。场景 A1、A2。
- **分页查询**：
  - 列表列为编码、名称、分类（显示字典名称）、联系人、联系电话、状态、备注。
  - 查询条件只有名称（模糊）、状态（`sys_normal_disable`）、分类三个，可以组合，也可以都不填。
  - 分类为空，或分类值已不在字典里时，显示为『未分类』。用『未分类』作条件查询，会返回这两类供应商，不返回分类有效的。
  - 结果分页并显示总数，不显示已删除的记录；没有列表权限时拒绝。
  - 场景 A4–A8、A25、A41–A44、A51、A52、A56、A58、A59。
- **新增**：
  - 编码必须手工录入且必填，在未删除的供应商中唯一；已删除记录的编码可以复用。
  - 名称必填，不要求唯一；分类必填，且必须是字典里现有的值，否则提示分类无效。
  - 联系人和电话选填，电话不校验格式；状态默认启用。
  - 场景 A9–A12、A26–A29、A38–A40、A50。
- **修改**：
  - 可以改名称、分类、联系人、电话、状态、备注；编码不可修改。
  - 校验规则与新增相同。分类为空的历史记录必须先选分类才能保存。
  - 状态只能在修改表单里改，列表没有启停开关；不能查看已删除记录的详情。
  - 场景 A13–A15、A30、A31、A45–A48、A53。
- **删除**：支持单条和批量，删除前二次确认，任何状态都能删，逻辑删除。场景 A16–A18、A32、A33。
- **导出**：
  - 导出 Excel，分类显示名称，空分类或失效分类显示『未分类』，状态显示正常或停用。
  - 不分页，筛选条件与列表一致，不导出已删除记录。
  - 场景 A19、A20、A34、A49、A54、A57、A60；A21 为人工验收。
- **按钮级权限**：五项权限相互独立，缺哪项就拒绝对应接口；超级管理员拥有全部权限；不按部门隔离数据。场景 A22、A24、A35。
- **供应商分类字典**：初始化后有『供应商分类』字典，含原材料、服务、设备；字典里新增或删除的值立即影响可选项和有效性校验。场景 A36、A37、A55。

### purchase-order（`openspec/specs/purchase-order/spec.md`）

- **分页查询**：
  - 查询条件为单号（模糊）、供应商、状态（草稿或已提交）、下单日期区间（包含起止当天）。
  - 默认按下单日期倒序，同一天按创建时间倒序。
  - 列表显示单号、供应商名称、下单日期、状态、合计金额、创建时间；不做数据权限隔离。
  - 场景 A1–A4。
- **新增**：
  - 单号由系统生成，格式为 `PO` 加下单日期（yyyyMMdd）加当日流水号，全局唯一；调用方传入的单号会被忽略。
  - 供应商只能选启用状态的，停用的会被拒绝。
  - 明细至少一条；数量必须是大于 0 的正整数；单价必须大于 0，最多两位小数。
  - 行金额按数量乘单价计算，合计金额按明细之和计算；状态固定为草稿。
  - 场景 A5–A10、A32、A33。
- **修改**：
  - 只能修改草稿；明细以本次提交的整体为准，保存后重算金额；单号不可修改。
  - 如果原供应商已停用，必须改选启用的供应商。
  - 场景 A11–A14、A34。
- **详情**：返回主表和全部明细；单据不存在时返回可读的失败信息；供应商停用不影响查看。场景 A15、A16。
- **删除**：只能删除草稿，支持批量，明细一起删除，删除前二次确认。场景 A17–A19。
- **提交**：
  - 草稿变为已提交，这是终态；提交时校验至少有一条明细，不校验供应商是否停用。
  - 使用独立的 `submit` 权限；提交后不能再修改或删除。
  - 场景 A20–A24、A35。
- **导出**：只导出主表，筛选条件与列表相同，列名为中文，状态显示中文，需要导出权限。场景 A25、A26；A27 为人工验收。
- **菜单与权限**：『采购单管理』挂在业务管理下，有查询、新增、修改、删除、提交、导出按钮；未登录返回 401，无权限返回 403；只控制功能，不限制数据范围。场景 A28–A31。

## 变更与底座演进记录

- 业务变更的完整材料在 `openspec/changes/<FEAT-id>/`：`proposal.md`（目标、非目标、故事、澄清、待决问题）、`stories.json`、`acceptance.json`、`traceability.json`、`design.md`（Context、Goals、Decisions、Risks、Files；implement 角色在这里加 `## Tests First`）、`decisions.md`、`approval.json`、`checklist.md`、`specs/<capability>/spec.md`（增量规格）。
- 证据报告在 `reports/storyloop/<FEAT-id>/report.md`。
- 底座演进（BASE 提案，见 `.storyloop/base-proposals/`）：
  - BASE-20260918-001：试点后的底座整理。
  - BASE-20260918-002：同步上游 subtree。
  - BASE-20260921-001：回填供应商和采购单的规格。
  - BASE-20260921-002：Scenario 改为按验收条件 ID 命名。
  - BASE-20260921-003：引入 Playwright Test Agents 生成 UI 回归资产。
  - BASE-20260922-001：冒烟只跑本次变更的用例。
  - BASE-20260923-001：implement 角色先写测试，业务模块可以写 JUnit/Mockito 单测，基线升到 1.0.7。
