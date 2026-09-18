# StoryLoop 验收报告：FEAT-20260918-001

- 状态：PASSED
- 需求摘要：在『业务管理』目录下提供供应商管理功能。有权限的用户可以维护供应商档案，包括供应商编码、名称、联系人、联系电话、启用/停用状态和备注。用户可以按名称和状态分页查询，也可以新增、修改、删除供应商并导出 Excel。列表、新增、修改、删除、导出分别受按钮级权限控制。后端接口和前端页面都要交付。
- 审批摘要：`e5d268a189f12acfabbca95859ad91602bfd0ba45745931684650cd87a1087fb`
- 实现提交：`019f1620b8f491198a335aa1c1786502319c7e64`
- 集成提交：`7b96a87492445184dda1368ca62c6126a2d2470a`

## 需求追溯

| 用户故事 | 验收条件 | 测试 | 结果 | 证据 SHA-256 |
|---|---|---|---|---|
| S1 『业务管理』目录与供应商管理菜单 | A1 列表中有顶级目录『业务管理』，其下有菜单『供应商管理』，该菜单下有查询、新增、修改、删除、导出五个按钮权限 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S1 『业务管理』目录与供应商管理菜单 | A2 导航中出现『供应商管理』，点击后打开供应商列表页面 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S2 分页查询供应商 | A4 返回成功，结果含当前页记录和总条数，每条记录包含编码、名称、联系人、联系电话、状态、备注 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S2 分页查询供应商 | A5 结果只包含停用的供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S2 分页查询供应商 | A6 结果包含该供应商，且不包含名称不匹配的供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S2 分页查询供应商 | A25 结果包含名称已知的供应商，且不包含名称里没有这段文字的供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S2 分页查询供应商 | A7 请求被拒绝，并提示未登录 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S2 分页查询供应商 | A8 表格只显示符合条件的供应商，并显示分页控件 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A9 返回成功，之后按该名称查询能查到这条新供应商，各字段与提交的一致 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A10 新增失败，并提示编码重复，系统中编码为 X 的供应商仍只有一条 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A11 新增失败，并提示名称必填 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A26 新增失败，并提示编码必填，系统中没有新增这条供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A27 返回成功，按名称 N 查询能查到两条供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A28 返回成功，再查询该供应商时联系人和联系电话为空，状态为启用（0） | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A29 返回成功，再查询该供应商时联系电话与提交的一致 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S3 新增供应商 | A12 弹窗关闭，页面提示操作成功，列表中出现新增的供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S4 修改供应商 | A13 返回成功，再查询该供应商时联系人为新值，状态为停用（1） | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S4 修改供应商 | A14 返回该供应商的完整档案信息 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S4 修改供应商 | A30 再查询该供应商时编码仍为 X，系统中没有编码为 Y 的供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S4 修改供应商 | A31 修改失败，并提示名称必填，再查询该供应商时名称仍为原值 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S4 修改供应商 | A15 弹窗关闭，页面提示操作成功，列表中这一行显示新名称 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S5 删除供应商 | A16 返回成功，之后查询列表时不再出现该供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S5 删除供应商 | A17 返回成功，之后查询列表时这两条都不再出现 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S5 删除供应商 | A32 返回成功，之后查询列表时不再出现该供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S5 删除供应商 | A33 不再返回该供应商的档案信息 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S5 删除供应商 | A18 页面提示删除成功，该供应商从列表中消失 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S6 导出供应商 Excel | A19 返回一个非空的 Excel 文件，表头包含供应商编码、名称、联系人、联系电话、状态、备注 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S6 导出供应商 Excel | A34 导出文件的数据行数等于按同一条件查询得到的总条数，且每一行的状态都是该状态 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S6 导出供应商 Excel | A20 浏览器下载一个 Excel 文件 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S6 导出供应商 Excel | A21 文件中该供应商各列的值与系统一致，状态显示为正常或停用 | human | ACCEPTED | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S7 按钮级权限控制 | A22 每次调用都被拒绝，并提示没有权限，供应商数据没有变化 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S7 按钮级权限控制 | A35 返回成功，结果中包含 admin 新增的那条供应商 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |
| S7 按钮级权限控制 | A24 每项操作都成功 | FEAT-20260918-001-supplier-core | PASS | `14b241be59bb2e7070499f77bae5e63924a7f6e2e89634876613726e7f172a8b` |

## 独立审查

I checked the untracked implementation files against approved contract revision 3 and did not find any problems. Backend: the controller at /biz/supplier checks biz:supplier:list for the list, query for detail, add, edit, remove and export. Every one of these permission strings matches a button row in sql/biz/FEAT-20260918-001.sql. The add and edit endpoints carry @Log and @RepeatSubmit, and the delete and export endpoints carry @Log. Name search uses a partial (contains) match and status uses an exact match. The same filter builds both the paged list and the unpaged export. Deletion is logical: del_flag uses @TableLogic, so deleted suppliers are excluded from the list, the detail view, export and the code uniqueness check. The uniqueness check therefore only looks at undeleted suppliers, which means the code of a deleted supplier can be reused, as decided in Q12. Code is required when adding. Name is required when adding and when editing. Contact and phone are optional, with no format check. Status is restricted to 0 or 1 and defaults to 0 on insert. On update the submitted code is set to null before saving, so the code cannot be changed. No data-permission annotation is applied, so there is no per-department isolation. The export object maps the status column through the sys_normal_disable dictionary and has headers for code, name, contact, phone, status and remark. SQL: the table is created with if-not-exists and the menus are deleted and re-inserted, so the script can be run repeatedly. It includes the required audit columns and del_flag, and uses menu IDs from the 1770… range: a top-level 业务管理 directory (type M), the 供应商管理 menu (type C, component biz/supplier/index) and five button permissions (type F). Frontend: the API paths match the backend. The page has name and status search fields, a paged table showing the total count, and an add/edit dialog in which the code field is disabled when editing. Buttons are gated with v-hasPermi, deletion asks for confirmation, export downloads through the shared download helper, and there is no status toggle in the list. Evidence: the smoke run passed for 32 of the 33 acceptance criteria (25 Python tests and 6 Playwright tests). A21 is manual and was not run. The Maven regression tests passed and the boundary check found no violations. I did not rerun compilation or the frontend type check myself; I relied on the regression and smoke evidence.
