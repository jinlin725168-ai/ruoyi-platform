# StoryLoop 验收报告：FEAT-20260923-002

- 状态：PASSED
- 需求摘要：供应商列表按名称搜索时，忽略输入内容首尾的空白字符（半角空格、全角空格、制表符、换行等），并且英文字母不区分大小写。列表查询和按条件导出都遵守同一规则，业务人员不必记住供应商名称的准确大小写，也不会因为多敲的空格或粘贴时带进来的空白字符而搜不到。
- 审批摘要：`c945cddfa240d14d681bf490b404e5401ac7a53e9216c21e907fe2b0cf26cf8a`
- 实现提交：`ddf4105c05685b7b4dff5bd9a21bcaa9b9aac6cb`
- 集成提交：`4cfb44ead55cadf30b78738567297e6906f0b62f`

## 需求追溯

| 用户故事 | 验收条件 | 测试 | 结果 | 证据 SHA-256 |
|---|---|---|---|---|
| S2 分页查询供应商 | A4 返回成功，结果含当前页记录和总条数，每条记录包含编码、名称、分类、联系人、联系电话、状态、备注 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A5 结果只包含停用的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A6 结果包含该供应商，且不包含名称不匹配的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A25 结果包含名称已知的供应商，且不包含名称里没有这段文字的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A61 结果包含名称为 N 的供应商，且不包含名称不包含 N 的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A69 结果包含名称为 N 的供应商，且不包含名称不包含 N 的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A70 结果包含名称为 N 的供应商，且不包含名称不包含 N 的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A62 结果包含该供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A63 结果包含该供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A64 结果包含名称含这段文字的供应商，且不包含名称不含这段文字的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A65 结果包含名称为『Acme Steel』的供应商，且不包含名称为『AcmeSteel』的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A66 返回成功，总条数与不带任何条件查询得到的总条数相同 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A71 返回成功，总条数与不带任何条件查询得到的总条数相同 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A41 结果包含分类为『原材料』的供应商，且每条结果的分类都是『原材料』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A42 结果只包含分类为『设备』的那条供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A51 结果包含这条分类为空的历史供应商，且不包含分类为『原材料』的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A58 结果包含分类为 C 的这条供应商，且不包含分类为『服务』的供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A7 请求被拒绝，并提示未登录 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A8 表格只显示符合条件的供应商，并显示分页控件 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A43 表格中每一行的分类列都显示『服务』，且包含这条供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A44 该供应商所在行的分类列显示『未分类』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A52 表格中每一行的分类列都显示『未分类』，且包含这条历史供应商 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A56 该供应商所在行的分类列显示『未分类』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S2 分页查询供应商 | A59 表格中包含这条供应商，其分类列显示『未分类』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A19 返回一个非空的 Excel 文件，表头包含供应商编码、名称、分类、联系人、联系电话、状态、备注 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A34 导出文件的数据行数等于按同一条件查询得到的总条数，且每一行的状态都是该状态 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A49 导出文件的数据行数等于按同一条件查询得到的总条数，且每一行的分类列都显示『原材料』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A54 导出文件中该供应商所在行的分类列显示『未分类』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A57 导出文件中该供应商所在行的分类列显示『未分类』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A60 导出文件包含前两条供应商、不包含分类为『服务』的供应商，数据行数等于按同一条件查询得到的总条数，且每一行的分类列都显示『未分类』 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A67 导出文件包含该供应商，数据行数等于以同一名称条件查询得到的总条数 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A72 导出文件包含该供应商，数据行数等于以同一名称条件查询得到的总条数 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A68 导出文件的数据行数等于只以状态为停用查询得到的总条数，且每一行的状态都是停用 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A20 浏览器下载一个 Excel 文件 | FEAT-20260923-002-supplier-name-search | PASS | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |
| S6 导出供应商 Excel | A21 文件中该供应商各列的值与系统一致，分类显示为分类名称，状态显示为正常或停用 | human | ACCEPTED | `98b7ffc1a8f1606cb1aaae770f4f973e7992aedc3459bb5bc6232d333f9d5231` |

## 分层验证

| 层 | 状态 | 命令 / 用例 | 说明 |
|---|---|---|---|
| unit（单元测试） | PASSED | 1/1 |  |
| integration（集成测试） | PASSED | 1/1 |  |
| acceptance（变更验收） | PASSED | 1/1 |  |
| smoke（系统冒烟） | PASSED | 1/1 |  |
| checks（静态检查） | SKIPPED | 0/0 | NO_REGRESSION_COMMANDS |

## 独立审查

I reviewed the uncommitted diff in BizSupplierServiceImpl.buildQueryWrapper and the new BizSupplierNameConditionTest against stories S2 and S6, reading openspec/foundation building-blocks.md and testing.md first. I found no problems.  **Implementation:** The name condition now goes through the project's StringUtils.trim, which delegates to Hutool StrUtil.trim. Its CharUtil.isBlankChar check covers half-width spaces, U+3000 full-width spaces, tabs, CR and LF, as the clarification requires. After trimming, the code checks isNotEmpty, so a name made only of whitespace is treated as no name condition. It then adds a bound parameter `LOWER(supplier_name) LIKE {0}` with the value `%lower(name, Locale.ROOT)%`. That keeps the contains match, ignores case and keeps the whitespace inside the name.  **List and export:** The change is in the shared buildQueryWrapper, which both queryPageList (list) and queryList (export) use, so the two apply the same rule. Status and category matching are unchanged. The only other caller, purchase order queryEnabledSuppliers, sets no name, so its behaviour is also unchanged. Stored names are not modified, which matches the non-goals.  **Foundation:** The change reuses existing building blocks (StringUtils, LambdaQueryWrapper) and re-implements nothing. It stays inside ruoyi-biz, and the boundary check reports ALLOWED with only the two expected files.  **Tests First:** The design's section is complete. All six tests it names exist in BizSupplierNameConditionTest. The class has @Tag("dev"), uses Mockito without a Spring context, and captures the wrapper passed to both selectVoPage and selectVoList. The tests check the SQL fragment and bound parameters for: - half-width, full-width and mixed tab/newline trimming - case-insensitive matching (LOWER in the SQL plus a lower-cased parameter) - kept inner whitespace - whitespace-only input, where only the status parameter remains  The design also honestly records that the whitespace-only test already passed on the old code.  **Evidence:** Unit and integration layers PASSED. The change acceptance suite PASSED: 27 Python cases and 7 Playwright cases, covering every automated criterion. The system smoke run PASSED. A21 is a manual criterion and is not covered by automation. I did not re-run any builds or tests; I relied on the evidence in the payload.

## 成本与耗时

- 代理调用：8 次（失败 1 次），代理累计 13 分 11 秒
- 闭环墙钟：66 分 47 秒，实现尝试 3 轮
- 费用：4.2006 USD

| 角色 | 调用 | 轮数 | 耗时 | 费用 |
|---|---|---|---|---|
| acceptance | 2 | 12 | 5 分 50 秒 | 1.0687 |
| characterize | 1 | 18 | 1 分 35 秒 | 0.7687 |
| implement | 2 | 34 | 3 分 20 秒 | 1.1378 |
| product | 2 | 7 | 1 分 57 秒 | 0.7373 |
| review | 1 | 10 | 0 分 28 秒 | 0.4881 |
