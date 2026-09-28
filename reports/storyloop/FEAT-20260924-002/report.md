# StoryLoop 验收报告：FEAT-20260924-002

- 状态：PASSED
- 需求摘要：采购单列表和导出可以按供应商名称模糊搜索：先去掉输入首尾的空白字符，并且不区分英文大小写；导出使用与列表完全相同的筛选口径，让采购员少输一段、多敲空格或大小写不一致时也不会漏掉单据
- 审批摘要：`240c5e20257fa6245bf73ce904536ea1e51fed76efe22a7c9d55cee1cae7b951`
- 实现提交：`2200856bfb8a8a1f7f72118afa01f4434e33a3cc`
- 集成提交：`9abac7424652769382ccf73e1b98b2d1ccde9f6e`

## 需求追溯

| 用户故事 | 验收条件 | 测试 | 结果 | 证据 SHA-256 |
|---|---|---|---|---|
| S1 采购单分页查询 | A1 返回结果只包含该单号匹配的单据，总条数为 1 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A2 返回结果只包含下单日期落在该范围内（含起止当天）的单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A3 返回结果中全部单据的状态均为草稿 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A4 表格只展示匹配的单据，且展示单号、供应商、供应商分类、下单日期、状态、合计金额列 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A36 该单据所在行的供应商分类为『原材料』 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A37 该单据所在行的供应商分类为『未分类』 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A38 该单据所在行的供应商分类为『未分类』 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A39 返回结果只包含供应商分类为『服务』的单据，总条数与这类单据数量一致 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A40 返回结果包含分类为空和已失效的单据，不包含分类为『原材料』的单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A41 返回结果包含该单据，且该行的供应商分类为『设备』 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A42 返回结果中每张单据的供应商分类都是『服务』，状态都是已提交 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A43 表格只展示该供应商分类的单据，且每行的供应商分类列都显示该分类名称 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A44 该单据仍出现在列表中，供应商分类为『原材料』 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A47 返回结果包含该单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A48 返回结果不包含该单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A85 返回结果包含供应商名称为 N 的单据，不包含供应商名称里没有这段文字的单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A86 返回结果包含供应商名称为 N 的单据，不包含供应商名称不包含 N 的单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A87 返回结果包含供应商名称为 N 的单据，不包含供应商名称不包含 N 的单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A88 返回结果包含该单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A89 返回结果包含该单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A90 返回结果包含供应商名称为『Acme Steel』的单据，不包含供应商名称为『AcmeSteel』的单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A91 返回成功，总条数与不带供应商名称条件查询时相同 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A92 返回结果中每张单据的供应商名称都是 N，状态都是已提交 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A93 表格只展示供应商名称包含这段文字的单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A96 返回结果包含该单据，且该行显示的供应商名称仍为 N | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S1 采购单分页查询 | A97 返回结果不包含该单据 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S7 导出采购单 Excel | A25 接口返回成功且响应为 Excel 文件内容（非空二进制） | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S7 导出采购单 Excel | A26 接口返回无权限，不产生任何文件内容 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S7 导出采购单 Excel | A27 列标题为中文业务名称并包含『供应商分类』，状态显示为『草稿』或『已提交』，供应商分类显示中文名称或『未分类』，每张采购单占一行且带合计金额，数据行与页面查询结果一致 | human | ACCEPTED | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S7 导出采购单 Excel | A45 导出的 Excel 包含『供应商分类』列，所有数据行的该列都是『服务』，行数与同条件列表查询的总条数一致 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S7 导出采购单 Excel | A46 导出的 Excel 中该单据所在行的供应商分类为『未分类』 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S7 导出采购单 Excel | A94 导出文件中每个数据行的供应商名称都包含这段文字（忽略大小写），数据行数等于以同一条件查询列表得到的总条数 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |
| S7 导出采购单 Excel | A95 导出文件的数据行数等于只以状态=已提交查询列表得到的总条数 | FEAT-20260924-002-purchase-order-supplier-name-search | PASS | `139c1a9c8928fc11b7bdfbe558fde8ce3e68868a98bfbff5cdd5a5e3ee28cc36` |

## 分层验证

| 层 | 状态 | 命令 / 用例 | 说明 |
|---|---|---|---|
| unit（单元测试） | PASSED | 1/1 |  |
| integration（集成测试） | PASSED | 1/1 |  |
| acceptance（变更验收） | PASSED | 1/1 |  |
| smoke（系统冒烟） | PASSED | 1/1 |  |
| checks（静态检查） | PASSED | 4/4 |  |

## 独立审查

Final review of FEAT-20260924-002. None of the four reviewers reported a finding or a question, so no finding was dropped. I read git diff myself. It matches what the reviewers described. BizPurchaseOrderServiceImpl.buildQueryWrapper now trims the supplier name with the base building block StringUtils.trim (Hutool, which also strips U+3000, tabs, CR and LF). When the trimmed value is not empty, it adds apply("LOWER(supplier_name) LIKE {0}", "%" + lower(Locale.ROOT) + "%"). The only other edits are the Javadoc, an inline comment and the java.util.Locale import. The only other file is the new unit test, and the boundary check found no violations. Correctness: pass. The filter is a contains match that trims leading and trailing whitespace, ignores English case and keeps inner spaces. It runs on the supplier_name stored on the order, not on the supplier master data (A96/A97). A name that is empty after trimming adds no condition (A91/A95). List and export use the same buildQueryWrapper, so they filter identically (A94). The other conditions, sorting, columns and paging are unchanged. A27 is a manual criterion and was not checked by hand, but this change does not touch export columns or formatting. Security: pass. The user value is passed as a bound parameter, so there is no SQL injection. The permissions on /list and /export are unchanged, and A26 confirms export is refused without the export permission. The design records that % and _ are not escaped, as an accepted trade-off. No secrets were added. Architecture: pass. The change follows design_plan D1–D3 and its Files table exactly. It reuses the base StringUtils.trim and mirrors the rule already in BizSupplierServiceImpl. No base files changed and no cross-module dependency was added. Tests: pass. BizPurchaseOrderSupplierNameConditionTest exists and is tagged @Tag("dev") with Mockito and no Spring context. It contains the 7 tests listed under Tests First, and each test checks both the list and export wrappers. 6 of the 7 would fail on the old code. The design openly states that the whitespace-only test already passed before the fix and is kept as a regression guard. The evidence reports that all five layers passed: unit, integration, acceptance (29 API tests and 3 Playwright tests), smoke and static checks. No builds were rerun during this read-only review.

## 成本与耗时

- 代理调用：7 次（失败 0 次），代理累计 10 分 45 秒
- 闭环墙钟：5203 分 35 秒，实现尝试 1 轮
- 费用：6.2135 USD

| 角色 | 调用 | 轮数 | 耗时 | 费用 |
|---|---|---|---|---|
| acceptance | 1 | 17 | 3 分 50 秒 | 1.5757 |
| characterize | 1 | 12 | 1 分 23 秒 | 0.7402 |
| design | 1 | 15 | 1 分 7 秒 | 0.5490 |
| implement | 1 | 18 | 1 分 35 秒 | 0.7378 |
| product | 2 | 12 | 2 分 4 秒 | 0.7606 |
| review | 1 | 26 | 0 分 43 秒 | 1.8502 |
