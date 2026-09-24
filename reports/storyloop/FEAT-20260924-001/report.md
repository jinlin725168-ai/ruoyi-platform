# StoryLoop 验收报告：FEAT-20260924-001

- 状态：PASSED
- 需求摘要：供应商列表和导出新增『编码』查询条件，匹配时和名称条件一样用模糊匹配：编码包含输入内容即命中，去掉首尾空白字符，不区分英文大小写，保留中间空白字符。导出的筛选范围和列表查询保持一致。
- 审批摘要：`c8e81e13083d8b9da4070c6a3aa11cd17f2b4e32844a5682439c1384c6e36be6`
- 实现提交：`060da6a0700a26261e0ddb4ef9b2453cca4f5fff`

## 需求追溯

| 用户故事 | 验收条件 | 测试 | 结果 | 证据 SHA-256 |
|---|---|---|---|---|
| S2 分页查询供应商 | A4 返回成功，结果含当前页记录和总条数，每条记录包含编码、名称、分类、联系人、联系电话、状态、备注 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A5 结果只包含停用的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A6 结果包含该供应商，且不包含名称不匹配的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A25 结果包含名称已知的供应商，且不包含名称里没有这段文字的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A61 结果包含名称为 N 的供应商，且不包含名称不包含 N 的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A69 结果包含名称为 N 的供应商，且不包含名称不包含 N 的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A70 结果包含名称为 N 的供应商，且不包含名称不包含 N 的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A62 结果包含该供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A63 结果包含该供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A64 结果包含名称含这段文字的供应商，且不包含名称不含这段文字的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A65 结果包含名称为『Acme Steel』的供应商，且不包含名称为『AcmeSteel』的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A66 返回成功，总条数与不带任何条件查询得到的总条数相同 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A71 返回成功，总条数与不带任何条件查询得到的总条数相同 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A82 结果包含编码已知的供应商，且不包含编码里没有这段文字的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A73 结果包含编码为 X 的供应商，且不包含编码与 X 无关的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A74 结果包含编码为 X 的供应商，且不包含编码与 X 无关的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A75 结果包含该供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A76 结果包含该供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A83 结果包含编码含这段文字的供应商，且不包含编码不含这段文字的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A77 结果包含编码为『Ab 01』的供应商，且不包含编码为『Ab01』的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A78 返回成功，总条数与不带任何条件查询得到的总条数相同 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A79 结果只包含编码为 X 的那条供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A41 结果包含分类为『原材料』的供应商，且每条结果的分类都是『原材料』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A42 结果只包含分类为『设备』的那条供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A51 结果包含这条分类为空的历史供应商，且不包含分类为『原材料』的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A58 结果包含分类为 C 的这条供应商，且不包含分类为『服务』的供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A7 请求被拒绝，并提示未登录 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A8 表格只显示符合条件的供应商，并显示分页控件 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A43 表格中每一行的分类列都显示『服务』，且包含这条供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A44 该供应商所在行的分类列显示『未分类』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A52 表格中每一行的分类列都显示『未分类』，且包含这条历史供应商 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A56 该供应商所在行的分类列显示『未分类』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S2 分页查询供应商 | A59 表格中包含这条供应商，其分类列显示『未分类』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A19 返回一个非空的 Excel 文件，表头包含供应商编码、名称、分类、联系人、联系电话、状态、备注 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A34 导出文件的数据行数等于按同一条件查询得到的总条数，且每一行的状态都是该状态 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A49 导出文件的数据行数等于按同一条件查询得到的总条数，且每一行的分类列都显示『原材料』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A54 导出文件中该供应商所在行的分类列显示『未分类』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A57 导出文件中该供应商所在行的分类列显示『未分类』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A60 导出文件包含前两条供应商、不包含分类为『服务』的供应商，数据行数等于按同一条件查询得到的总条数，且每一行的分类列都显示『未分类』 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A67 导出文件包含该供应商，数据行数等于以同一名称条件查询得到的总条数 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A72 导出文件包含该供应商，数据行数等于以同一名称条件查询得到的总条数 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A68 导出文件的数据行数等于只以状态为停用查询得到的总条数，且每一行的状态都是停用 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A84 导出文件包含编码已知的供应商、不包含编码里没有这段文字的供应商，数据行数等于以同一编码条件查询得到的总条数 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A80 导出文件包含该供应商，数据行数等于以同一编码条件查询得到的总条数 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A81 导出文件的数据行数等于只以状态为停用查询得到的总条数，且每一行的状态都是停用 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A20 浏览器下载一个 Excel 文件 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |
| S6 导出供应商 Excel | A21 文件中该供应商各列的值与系统一致，分类显示为分类名称，状态显示为正常或停用 | FEAT-20260924-001-supplier-code-search | PASS | `e6d072c5d8fe105fddfb22aebd1b91f9f8ded16309af7dbe072015e61a141682` |

## 分层验证

| 层 | 状态 | 命令 / 用例 | 说明 |
|---|---|---|---|
| unit（单元测试） | PASSED | 1/1 |  |
| integration（集成测试） | PASSED | 1/1 |  |
| acceptance（变更验收） | PASSED | 1/1 |  |
| smoke（系统冒烟） | PASSED | 1/1 |  |
| checks（静态检查） | PASSED | 4/4 |  |

## 独立审查

The implementation matches the approved stories S2 and S6, the architect's design_plan and the implementer's design record. Backend: BizSupplierServiceImpl.buildQueryWrapper now adds a code condition. It uses Hutool StringUtils.trim, which removes half-width and full-width spaces, tabs and CR/LF. An empty result is treated as no condition. Otherwise it applies the bound parameter `LOWER(supplier_code) LIKE {0}` with '%'+lower(Locale.ROOT)+'%'. This is placed before the name condition and follows the same pattern as the existing name rule. List (queryPageList) and export (queryList) share this builder, so export filtering stays consistent with the list. checkCodeUnique, insert/update, the BO, the controller, index.ts, the mapper XML and the SQL files are unchanged, as planned, so the non-goals hold: codes are stored as entered and uniqueness stays case-sensitive. Frontend: SupplierQuery.supplierCode?: string was added. index.vue has a clearable 供应商编码 input with prop=supplierCode as the first search item, and supplierCode: undefined in the initial queryParams. Both list and export pick it up through the whole queryParams object. The changed files are exactly the planned files plus the two new test files, and the boundary check is ALLOWED. The design's Tests First section is concrete. All 7 backend tests it lists exist in BizSupplierCodeConditionTest (@Tag("dev"), Mockito, no Spring context). They check both the selectVoPage (list) and selectVoList (export) wrappers for these behaviours: fragment contains-match, half-width trim, full-width/tab/newline trim, case-insensitivity, kept inner whitespace, blank or whitespace-only input treated as no condition, and AND-combination with name and status. The frontend query.test.ts checks the supplierCode type contract with expectTypeOf. The code follows the extension.md buildQueryWrapper convention and mirrors the existing name condition, so no building block is re-implemented. All layers passed on the same candidate (sha 3415a518…): the unit regression, integration, acceptance (40 API tests plus 7 Playwright tests covering A4–A84), system smoke, spotless, checkstyle, frontend_check and gitleaks. I did not re-run any builds or tests myself; this review relied on the evidence supplied.

## 成本与耗时

- 代理调用：7 次（失败 0 次），代理累计 10 分 49 秒
- 闭环墙钟：13 分 57 秒，实现尝试 1 轮
- 费用：4.4216 USD

| 角色 | 调用 | 轮数 | 耗时 | 费用 |
|---|---|---|---|---|
| acceptance | 1 | 13 | 3 分 46 秒 | 1.1598 |
| characterize | 1 | 18 | 1 分 11 秒 | 0.6107 |
| design | 1 | 14 | 0 分 53 秒 | 0.6753 |
| implement | 1 | 24 | 2 分 4 秒 | 0.7241 |
| product | 2 | 9 | 2 分 32 秒 | 0.8653 |
| review | 1 | 6 | 0 分 21 秒 | 0.3864 |
