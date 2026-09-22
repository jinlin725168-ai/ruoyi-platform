# StoryLoop 验收报告：FEAT-20260921-001

- 状态：PASSED
- 需求摘要：让供应商档案带上『供应商分类』（原材料、服务、设备等）。分类值由系统字典维护。新增和修改供应商时必须选择分类，提交的分类不在字典中时拒绝保存。列表显示分类，可以按分类筛选，也可以单独筛出『未分类』的供应商。导出的 Excel 包含分类列。历史数据没有分类，或者所用的分类值已在字典中被删除时，列表和导出都显示『未分类』，按『未分类』筛选或导出时也包含这两类供应商，业务人员可以据此逐步补齐。
- 审批摘要：`05e41ec52d3ca44dd180a2c143a0dbfcfe2bd3a7fa09b8c7730088c1d9ea9d1b`
- 实现提交：`a789324ce75b652ddabbd62d8d828d1207a2bf21`
- 集成提交：`a2ad28337aff4c228c86046bd82e416b0f3fe70f`

## 需求追溯

| 用户故事 | 验收条件 | 测试 | 结果 | 证据 SHA-256 |
|---|---|---|---|---|
| S8 供应商分类字典 | A36 字典存在，且包含原材料、服务、设备三个值 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S8 供应商分类字典 | A37 返回成功，再查询该供应商时分类为 C | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S8 供应商分类字典 | A55 新增失败，并提示分类无效，系统中没有编码为 X 的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A9 返回成功，之后按该名称查询能查到这条新供应商，各字段（包括分类）与提交的一致 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A10 新增失败，并提示编码重复，系统中编码为 X 的供应商仍只有一条 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A11 新增失败，并提示名称必填 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A26 新增失败，并提示编码必填，系统中没有新增这条供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A27 返回成功，按名称 N 查询能查到两条供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A28 返回成功，再查询该供应商时联系人和联系电话为空，状态为启用（0），分类与提交的一致 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A29 返回成功，再查询该供应商时联系电话与提交的一致 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A38 新增失败，并提示分类必填，系统中没有编码为 X 的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A50 新增失败，并提示分类无效，系统中没有编码为 X 的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A12 弹窗关闭，页面提示操作成功，列表中出现新增的供应商，并显示所选分类 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A39 可选项中包含原材料、服务、设备 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S3 新增供应商 | A40 表单不提交，分类处提示必填，弹窗保持打开 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A4 返回成功，结果含当前页记录和总条数，每条记录包含编码、名称、分类、联系人、联系电话、状态、备注 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A5 结果只包含停用的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A6 结果包含该供应商，且不包含名称不匹配的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A25 结果包含名称已知的供应商，且不包含名称里没有这段文字的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A41 结果包含分类为『原材料』的供应商，且每条结果的分类都是『原材料』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A42 结果只包含分类为『设备』的那条供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A51 结果包含这条分类为空的历史供应商，且不包含分类为『原材料』的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A58 结果包含分类为 C 的这条供应商，且不包含分类为『服务』的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A7 请求被拒绝，并提示未登录 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A8 表格只显示符合条件的供应商，并显示分页控件 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A43 表格中每一行的分类列都显示『服务』，且包含这条供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A44 该供应商所在行的分类列显示『未分类』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A52 表格中每一行的分类列都显示『未分类』，且包含这条历史供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A56 该供应商所在行的分类列显示『未分类』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S2 分页查询供应商 | A59 表格中包含这条供应商，其分类列显示『未分类』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A13 返回成功，再查询该供应商时联系人为新值，状态为停用（1） | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A14 返回该供应商的完整档案信息，包括分类 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A30 再查询该供应商时编码仍为 X，系统中没有编码为 Y 的供应商 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A31 修改失败，并提示名称必填，再查询该供应商时名称仍为原值 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A45 返回成功，再查询该供应商时分类为『设备』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A46 修改失败，并提示分类必填，再查询该供应商时分类仍为『服务』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A53 修改失败，并提示分类无效，再查询该供应商时分类仍为『服务』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A47 修改失败，并提示分类必填，再查询该供应商时联系人仍为原值 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A15 弹窗关闭，页面提示操作成功，列表中这一行显示新名称 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S4 修改供应商 | A48 弹窗关闭，页面提示操作成功，该行的分类列显示『原材料』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A19 返回一个非空的 Excel 文件，表头包含供应商编码、名称、分类、联系人、联系电话、状态、备注 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A34 导出文件的数据行数等于按同一条件查询得到的总条数，且每一行的状态都是该状态 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A49 导出文件的数据行数等于按同一条件查询得到的总条数，且每一行的分类列都显示『原材料』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A54 导出文件中该供应商所在行的分类列显示『未分类』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A57 导出文件中该供应商所在行的分类列显示『未分类』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A60 导出文件包含前两条供应商、不包含分类为『服务』的供应商，数据行数等于按同一条件查询得到的总条数，且每一行的分类列都显示『未分类』 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A20 浏览器下载一个 Excel 文件 | FEAT-20260921-001-supplier-category-core | PASS | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |
| S6 导出供应商 Excel | A21 文件中该供应商各列的值与系统一致，分类显示为分类名称，状态显示为正常或停用 | human | ACCEPTED | `b68c2cb0c3c8f6906ed2c80a9b75df44b04625134b2f9a5d516095270a7394a1` |

## 独立审查

I reviewed the FEAT-20260921-001 implementation against stories S8, S3, S2, S4 and S6. I found no defects. I read the changed files directly because the read-only `git diff` command was denied in this session.  - **SQL:** The script adds the nullable `supplier_category` column only when it is missing, so it can be run more than once. It recreates the `biz_supplier_category` dictionary ('供应商分类') with 原材料/服务/设备. Its ID ranges continue on from FEAT-20260920-001 without overlapping (A36). Historical supplier data is left untouched. - **Required and invalid category:** The request object marks the category as required for both add and edit, giving 'category required' (A38, A46, A47). On add and edit, the controller calls `checkCategoryValid`, which checks the value against the current dictionary through `DictService`. A value that is not in the dictionary, or was deleted from it, is rejected with '供应商分类无效' (A50, A53, A55), and a newly added dictionary value is accepted (A37). The existing duplicate-code, name-required and code-can't-change rules are kept. - **Display:** The list, detail and export results fill `supplierCategoryLabel` from the dictionary. Empty categories and categories deleted from the dictionary both show '未分类'. The Excel export uses this label as its '供应商分类' column, and status still goes through `sys_normal_disable`. - **Filtering:** An exact category filter returns only that category. The '未分类' filter (sentinel `__none__`) returns suppliers whose category is null, empty, or no longer in the dictionary, and excludes valid categories. The export uses the same query without paging (A41, A42, A51, A58, A34, A49, A60). - **Frontend:** The page has a category filter that includes a '未分类' option, a category column showing the label, and a required category select in the form, filled from `useDict`. When editing a supplier whose category is empty or deleted, the form clears the field so the user must pick one (A48). - **Consistency:** API paths and permission strings are unchanged and still match the controller. The boundary check found no violations.  The regression build passed, and the smoke run passed all 35 API tests and all 12 UI tests, covering every automated criterion. A21 is manual and was not run.

## 成本与耗时

- 代理调用：13 次（失败 0 次），代理累计 27 分 13 秒
- 闭环墙钟：1173 分 40 秒，实现尝试 2 轮
- 费用：13.5309 USD

| 角色 | 调用 | 轮数 | 耗时 | 费用 |
|---|---|---|---|---|
| implement | 4 | 102 | 7 分 47 秒 | 5.4456 |
| product | 4 | 9 | 5 分 14 秒 | 1.9529 |
| review | 2 | 23 | 1 分 22 秒 | 1.3196 |
| smoke | 3 | 24 | 12 分 49 秒 | 4.8128 |
