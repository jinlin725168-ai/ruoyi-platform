# StoryLoop 验收报告：FEAT-20260920-001

- 状态：PASSED
- 需求摘要：在 ruoyi-platform 的『业务管理』目录下提供采购单（主子表）管理能力：采购员可以在一个页面内录入采购单主信息与多条物料明细，单号由系统自动生成，系统自动计算明细金额与合计金额，草稿单据可修改、删除并提交；提交后单据冻结为终态，列表支持按单号/供应商/状态/下单日期范围分页查询、查看详情与导出 Excel，全部操作受菜单与按钮级权限控制，后端接口与前端页面同时交付。
- 审批摘要：`f1f7bd7dd3eead821e670d75ebdc83845c987a01d86203c3ba4099b106233da3`
- 实现提交：`8aaa6b356e7b260ca63ec68b2c3a8a3d02db7658`

## 需求追溯

| 用户故事 | 验收条件 | 测试 | 结果 | 证据 SHA-256 |
|---|---|---|---|---|
| S1 采购单分页查询 | A1 返回结果只包含该单号匹配的单据，总条数为 1 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S1 采购单分页查询 | A2 返回结果只包含下单日期落在该范围内（含起止当天）的单据 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S1 采购单分页查询 | A3 返回结果中全部单据的状态均为草稿 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S1 采购单分页查询 | A4 表格只展示匹配的单据，且展示单号、供应商、下单日期、状态、合计金额列 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A5 保存成功，查询详情可看到两条明细，且状态为草稿 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A6 系统以计算值为准，两条明细金额分别为 20 和 15，主表合计金额为 35 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A7 保存失败并返回可读的错误提示，系统中不产生该采购单 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A8 保存失败并返回明细不能为空的提示 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A9 弹窗关闭、列表中出现该新单据，状态显示为草稿且合计金额等于两行金额之和 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A10 下拉候选中只出现启用状态的供应商 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A32 保存成功，单据单号为系统生成的『PO+下单日期+流水号』格式且不等于请求中传入的值 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S2 新增采购单及其明细 | A33 三次调用都失败并返回可读的校验提示，系统中不产生对应采购单 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S3 修改草稿采购单 | A11 保存成功，详情中明细为修改后的两条，合计金额等于这两条金额之和 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S3 修改草稿采购单 | A12 修改失败并返回已提交不可修改的提示，单据内容保持不变 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S3 修改草稿采购单 | A13 表单回显该单据的供应商、下单日期、备注及全部明细行 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S3 修改草稿采购单 | A14 列表中该单据的合计金额更新为按新单价重算后的值 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S3 修改草稿采购单 | A34 保存失败并返回需改选为启用状态供应商的可读提示，单据内容保持不变 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S4 查看采购单详情 | A15 返回主表字段与三条明细，合计金额等于三条明细金额之和 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S4 查看采购单详情 | A16 接口返回失败且带有可读的错误提示 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S5 删除草稿采购单 | A17 删除成功，再次查询列表与详情都查不到该单据及其明细 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S5 删除草稿采购单 | A18 删除失败并返回已提交不可删除的提示，该单据仍可被查询到 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S5 删除草稿采购单 | A19 两张单据同时从列表中消失，总条数相应减少 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S6 提交采购单 | A20 提交成功，详情中状态变为已提交 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S6 提交采购单 | A21 提交失败并返回状态不允许提交的提示，状态保持为已提交 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S6 提交采购单 | A22 两次调用都失败并返回可读提示，单据内容与状态均未变化 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S6 提交采购单 | A23 列表中该行状态变为已提交，且该行的修改与删除按钮不可用 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S6 提交采购单 | A24 接口返回无权限，单据状态保持为草稿 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S6 提交采购单 | A35 详情正常返回完整主表与明细，提交成功且状态变为已提交 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S7 导出采购单 Excel | A25 接口返回成功且响应为 Excel 文件内容（非空二进制） | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S7 导出采购单 Excel | A26 接口返回无权限，不产生任何文件内容 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S7 导出采购单 Excel | A27 列标题为中文业务名称，状态显示为『草稿』或『已提交』，每张采购单占一行且带合计金额，数据行与页面查询结果一致 | human | ACCEPTED | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S8 菜单与按钮级权限控制 | A28 『业务管理』目录下出现『采购单管理』菜单，点击可进入采购单列表页 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S8 菜单与按钮级权限控制 | A29 接口返回未登录错误，不返回业务数据 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S8 菜单与按钮级权限控制 | A30 三次调用都返回无权限，而列表查询可正常返回数据 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |
| S8 菜单与按钮级权限控制 | A31 页面可见列表数据，但新增、修改、删除、提交、导出按钮均不展示 | FEAT-20260920-001-purchase-order-core | PASS | `962c573c5a169f3243de3bf9d102d6b1b6384d8ca8aa13306917fc34dd1976aa` |

## 独立审查

独立复核了 FEAT-20260920-001 采购单管理（主子表）的真实实现，对照 revision 2 已批准契约的 8 个故事、35 条验收项逐条核对了后端（controller/service/bo/vo/domain/mapper/mapper.xml）、SQL（建表+字典+菜单按钮）、前端（api/types/index.vue）与验收冒烟用例，未发现与故事规则不符之处。要点：单号由 PO+yyyyMMdd+4 位流水生成（唯一索引兜底并重试取号），请求传入的单号/明细金额/合计金额/状态一律被忽略并由服务端重算（S2/S3 A6 A32）；新增与修改均校验供应商必须为启用状态，而详情与提交不校验供应商状态（S3 A34 / S6 A35，与 Q5 决策一致）；数量为大于 0 的正整数、单价大于 0 且最多 2 位小数由 @DecimalMin/@Digits 与服务端 intValueExact 双重保证（A33）；修改/删除/提交前统一经 loadDraft 拒绝已提交单据，提交为终态（A12 A18 A21 A22）；列表按单号模糊、供应商、状态、下单日期起止过滤且默认下单日期倒序+创建时间倒序，无数据权限隔离；导出复用同一 wrapper 且不分页、仅主表一行一单、中文表头并用 biz_purchase_order_status 字典把状态转成『草稿/已提交』（A25 A27）；六个接口的 @SaCheckPermission 与 sql/biz/FEAT-20260920-001.sql 中 1770000000000000010–016 的菜单/按钮权限串一一对应，提交使用独立的 biz:purchaseOrder:submit（A24），菜单挂在已有『业务管理』目录（1770000000000000000）下、component 与前端路径 biz/purchaseOrder/index 一致，menu_id 与 FEAT-20260918-001 使用的 …000–006 段无冲突；前端 api 路径与后端 @RequestMapping("/biz/purchaseOrder") 一致，弹窗单号只读且仅修改时展示，明细行可动态增删并实时显示行金额与合计，按钮均带 v-hasPermi 且已提交行的修改/删除/提交按钮禁用。落地范围与 boundary 报告的 18 个文件一致，全部位于 module_roots 之内，未触碰底座。回归（mvn -pl ruoyi-admin -am test，含 ruoyi-biz 编译）与冒烟（25 条后端用例 + 9 条 Playwright 用例，覆盖除 manual 的 A27 外全部 34 条验收项）均为 PASS，冒烟用例通过字段别名探针实现、不绑定具体实现命名，功能缺失时会失败。本次复核未修改任何文件；`git status` 因权限被拒未能执行，故未复核工作区是否存在额外未跟踪文件，该项以 boundary 报告与外部验收结果为准。

## 成本与耗时

- 代理调用：11 次（失败 0 次），代理累计 73 分 47 秒
- 闭环墙钟：165 分 20 秒，实现尝试 4 轮
- 费用：32.4878 USD

| 角色 | 调用 | 轮数 | 耗时 | 费用 |
|---|---|---|---|---|
| implement | 5 | 264 | 30 分 57 秒 | 18.6261 |
| product | 2 | 6 | 3 分 7 秒 | 0.7417 |
| review | 2 | 58 | 6 分 6 秒 | 4.0658 |
| smoke | 2 | 56 | 33 分 36 秒 | 9.0542 |
