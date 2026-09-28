## Context

- The purchase-order capability (`org.dromara.biz.purchase`, FEAT-20260920-001, with supplier category added by FEAT-20260924-001) already has `GET /biz/purchaseOrder/list` and `POST /biz/purchaseOrder/export`. Both build their conditions with the private method `BizPurchaseOrderServiceImpl.buildQueryWrapper(bo)`: `queryPageList` calls `selectVoPage` and `queryExportList` calls `selectVoList`.
- The current supplier-name condition is `lqw.like(StringUtils.isNotBlank(bo.getSupplierName()), BizPurchaseOrder::getSupplierName, bo.getSupplierName())`. It uses the raw input, so leading or trailing spaces, full-width spaces, tabs and newlines cause misses. Case handling depends on the column collation. An input made only of full-width spaces is not blank to `isNotBlank` (commons-lang), so it still becomes a filter.
- It already matches against `biz_purchase_order.supplier_name`, the name stored on the order when it was saved. That is what the clarification requires (A96/A97). It does not look at the supplier master data.
- The supplier module already has exactly this rule (`BizSupplierServiceImpl.buildQueryWrapper`): `StringUtils.trim` (the dromara `StringUtils.trim` delegates to Hutool `StrUtil.trim`, which removes every blank character including U+3000, `\t` and `\n`), then `lqw.apply("LOWER(supplier_name) LIKE {0}", "%" + name.toLowerCase(Locale.ROOT) + "%")`, with the condition skipped when the trimmed value is empty. `BizSupplierNameConditionTest` pins that behaviour.
- Frontend `views/biz/purchaseOrder/index.vue` already has the query field `supplierName` (label '供应商', placeholder '请输入供应商名称'). It sends the value unchanged to both list and export (`applyDateRange(queryParams)`), which matches what the Playwright suite expects.

## Goals

- For list and export, the supplier-name condition strips all leading and trailing whitespace (half-width space, full-width space, tab, newline and so on), ignores English letter case, keeps inner whitespace unchanged, and does a contains (fuzzy) match on the supplier name stored on the order.
- A supplier-name condition that is empty after trimming counts as not filled: no SQL condition is added and the total equals the unfiltered query (A91, A95).
- The condition combines with order number, supplier, status, order-date range and supplier category exactly as before (A92). Columns, sorting, paging and export format stay unchanged.
- Export uses exactly the same filter as the list (A94), because both keep sharing one wrapper builder.

## Decisions

### D1 Normalize in `buildQueryWrapper` of the service
- **Choice:** In `BizPurchaseOrderServiceImpl.buildQueryWrapper`, replace the current `lqw.like(... getSupplierName ...)` line with: `String supplierName = StringUtils.trim(bo.getSupplierName()); if (StringUtils.isNotEmpty(supplierName)) { lqw.apply("LOWER(supplier_name) LIKE {0}", "%" + supplierName.toLowerCase(Locale.ROOT) + "%"); }`. Add a one-line comment in the same style as the supplier module and update the method Javadoc ("供应商名称去首尾空白后忽略大小写模糊匹配"). Add the import `java.util.Locale`.
- **Rationale:** List and export already go through this one method, so a single change covers S1 and S7 and guarantees the same filter. It reuses the proven supplier-module rule (building block: dromara `StringUtils.trim` via Hutool, which handles U+3000; parameterized `apply` placeholder, no SQL injection). The contract says the supplier module "已具备同样的名称匹配规则", so copying it keeps the two capabilities consistent.
- **Alternatives considered:** (a) Trim in the controller or with a Jackson/`@InitBinder` setter on the BO. Rejected: the export binds from a form, the list binds from a query string, and the service unit tests would not cover it. (b) Rely on the MySQL `_ci` collation instead of `LOWER()`. Rejected: that depends on column collation, which the base does not guarantee, and it diverges from the supplier rule. (c) Share a static helper with the supplier module. Rejected: it would make purchase depend on a supplier-internal implementation detail or require a new common utility in the protected base, for two lines of code.

### D2 Match target stays `biz_purchase_order.supplier_name`
- **Choice:** Filter only on the purchase order's own `supplier_name` column. Do not join the supplier master data and do not call `IBizSupplierService` for the name.
- **Rationale:** Required by the clarification and rules A96/A97. The column is already written from the master data at insert and update time, and later renames in the master data must not affect it.
- **Alternatives considered:** Filtering by supplier ids looked up by name from the master data. Rejected by the contract.

### D3 No LIKE-wildcard escaping, no frontend change
- **Choice:** Keep the current behaviour for `%` and `_` in the input (not escaped), the same as the supplier module and MyBatis-Plus `like`. Leave `frontend/src/**` unchanged; the server does the trimming.
- **Rationale:** Escaping is outside the contract and would make the two capabilities behave differently. The server is the single source of truth, so direct API calls (the Python suite) and the UI behave identically.
- **Alternatives considered:** Trimming in the frontend as well. Unnecessary, and it could hide backend defects.

## Files

| File | Action | Responsibility |
|---|---|---|
| `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/service/impl/BizPurchaseOrderServiceImpl.java` | modify | `buildQueryWrapper`: trimmed, lower-cased contains match on `supplier_name` via `apply`; skip when empty after trim; Javadoc/comment update; import `java.util.Locale`. Nothing else in the class changes. |
| `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/purchase/BizPurchaseOrderSupplierNameConditionTest.java` | create (test) | `@Tag("dev")` Mockito unit test. It follows the setup of `BizPurchaseOrderSupplierCategoryTest` (TableInfo init, captured wrapper) and the assertions of `BizSupplierNameConditionTest`: half-width, full-width, tab and newline trimming → param `%acme%`/`%钢铁%`; SQL segment contains `lower(supplier_name) like`; inner space kept (`%acme steel%`); whitespace-only input produces no `supplier_name` segment; combines with `status =`; export (`queryExportList`) captures the same condition. |

No changes to BO/VO/entity, mapper XML, controller, `sql/biz`, menus or `frontend/src`.

## Data And Interfaces

- **Tables/columns:** none added; the filter uses the existing `biz_purchase_order.supplier_name varchar(100)`.
- **Endpoints (unchanged signatures):** `GET /biz/purchaseOrder/list` (`biz:purchaseOrder:list`) and `POST /biz/purchaseOrder/export` (`biz:purchaseOrder:export`). The `supplierName` query/form parameter changes meaning: trim all leading and trailing blank characters, then run a case-insensitive contains match on the order's stored supplier name; empty after trimming means no filter. Other parameters (`orderNo`, `supplierId`, `status`, `supplierCategory`, `params[beginOrderDate]`, `params[endOrderDate]`, `pageNum`, `pageSize`) are unchanged.
- **Generated SQL fragment:** `... AND LOWER(supplier_name) LIKE ?` with parameter `%<trimmed lower-case input>%`.
- **Permissions/menus:** none added or changed.

## Risks And Trade-Offs

- `LOWER(supplier_name)` prevents index use on `supplier_name`. The existing `LIKE '%…%'` could not use an index either, so performance does not change.
- `%` and `_` in user input are still treated as wildcards (same as the supplier module). This is an accepted consistency trade-off.
- `toLowerCase(Locale.ROOT)` combined with SQL `LOWER` covers English letters as the contract requires; the contract explicitly excludes other normalizations (pinyin, traditional/simplified, segmentation).
- The `supplierId` exact filter is untouched, and supplier category still uses id lists. The new condition is ANDed with them, so combinations (A92) behave as before.
- `api.md` describes `supplierName` only as a parameter. Documenting the trim/case rule there is a foundation (base) update for the maintenance flow, not part of this change.

## Implementation record

## Context

- `GET /biz/purchaseOrder/list` and `POST /biz/purchaseOrder/export` both build their filters with the private `BizPurchaseOrderServiceImpl.buildQueryWrapper(bo)`. `queryPageList` passes the result to `selectVoPage`; `queryExportList` passes it to `selectVoList`.
- Before this change the supplier-name condition was `lqw.like(StringUtils.isNotBlank(name), BizPurchaseOrder::getSupplierName, name)`. It used the raw input, so leading or trailing spaces, full-width spaces, tabs and newlines caused misses, and case handling depended on the column collation.
- The supplier module already applies the required rule in `BizSupplierServiceImpl.buildQueryWrapper`: `StringUtils.trim`, then `LOWER(supplier_name) LIKE {0}`. `BizSupplierNameConditionTest` pins that behaviour.
- The clarification says to match the supplier name stored on the order (`biz_purchase_order.supplier_name`), which is what is displayed. The column already stores that name.

## Goals

- For both list and export, the supplier-name condition:
  - strips all leading and trailing whitespace: half-width spaces, full-width spaces (U+3000), tabs, CR and LF;
  - ignores English letter case;
  - keeps inner whitespace;
  - does a contains match on the name stored on the order.
- An input that is empty after trimming adds no condition (A91, A95).
- The condition still combines with order number, supplier, status, date range and supplier category (A92).
- Columns, sort order, paging and export format do not change.

## Tests First

New file: `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/purchase/BizPurchaseOrderSupplierNameConditionTest.java`.

Setup:
- `@Tag("dev")`, Mockito, lenient strictness, no Spring context.
- `TableInfoHelper.initTableInfo` for `BizPurchaseOrder`.
- `ArgumentCaptor` on `selectVoPage` (list) and `selectVoList` (export). Every test checks both wrappers.

First run: `mvn … -Dtest=BizPurchaseOrderSupplierNameConditionTest test` → Tests run: 7, Failures: 6.

| Test | Before the fix | After |
|---|---|---|
| `trimsHalfWidthSpacesAroundName` (`"   Acme   "`) | FAIL: param was `%   Acme   %`, expected `%acme%` | green |
| `trimsFullWidthSpacesAroundName` (`"　　钢铁　"`) | FAIL: param was `%　　钢铁　%`, expected `%钢铁%` | green |
| `trimsTabsNewlinesAndMixedWhitespaceAroundName` (`"　\t 钢铁\r\n"`) | FAIL: param kept the full-width space, tab and CRLF | green |
| `matchesOrderSupplierNameIgnoringCase` (ACME/acme/AcMe) | FAIL: SQL was `(supplier_name LIKE …)`, expected `lower(supplier_name) like` | green; also verifies the supplier master data is not queried |
| `keepsInnerWhitespaceAfterTrimAndLowerCase` (`"  Acme Steel\t"`) | FAIL: param was `%  Acme Steel\t%`, expected `%acme steel%` | green |
| `trimmedCaseInsensitiveNameCombinesWithStatus` | FAIL: SQL had no `LOWER(supplier_name)` | green; params are exactly `%acme steel%` and `1`, SQL contains `status =` |
| `whitespaceOnlyNameIsTreatedAsNoNameCondition` (`" 　\t\r\n "` with status 1) | Already passed before the fix: commons-lang `isBlank` treats U+3000 as whitespace. Kept as a regression guard. | green |

Final runs:
- `-Dtest=BizPurchaseOrder*`: everything green, including `BizPurchaseOrderServiceImplCharacterizationTest` and `BizPurchaseOrderSupplierCategoryTest`.
- `spotless:check` and `checkstyle:check`: clean.
- Regression `mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test`: green.

## Decisions

### D1 Normalize inside the shared `buildQueryWrapper`
- **Choice:** Replace the `like` line with: `String supplierName = StringUtils.trim(bo.getSupplierName()); if (StringUtils.isNotEmpty(supplierName)) { lqw.apply("LOWER(supplier_name) LIKE {0}", "%" + supplierName.toLowerCase(Locale.ROOT) + "%"); }`. Add an inline comment, update the Javadoc and import `Locale`.
- **Rationale:**
  - List and export share this one method, so one change covers S1 and S7 and keeps their filters identical.
  - It is the same rule the supplier module uses.
  - It reuses the base `StringUtils.trim` (Hutool), which strips U+3000.
  - The placeholder in `apply` is parameterized, so user input cannot inject SQL.
- **Alternatives considered:**
  - Trim in the controller or when binding the BO: that would have to be done for both request styles (query string for the list, form for export), and the service unit tests would not cover it.
  - Rely on a `_ci` column collation: whether it is case-insensitive depends on the database collation.
  - A shared helper: that would need a change to the base or a cross-feature dependency, for two lines of code.

### D2 Match on `biz_purchase_order.supplier_name` only
- **Choice:** Do not join the supplier master data or call the supplier service to resolve the name.
- **Rationale:** The clarification and A96/A97 require that later renames in the supplier master data do not change which orders match.
- **Alternatives considered:** Resolving supplier ids by name from the master data. The contract rejects this.

### D3 No wildcard escaping and no frontend change
- **Choice:** `%` and `_` in the input keep the current wildcard behaviour. The frontend already sends `supplierName` to both list and export, so it is unchanged.
- **Rationale:** This stays consistent with the supplier module, and the server is the single source of truth for the rule.
- **Alternatives considered:** Trimming on the client as well. Not needed, and it could hide backend defects.

## Risks And Trade-Offs

- `LOWER(supplier_name)` prevents index use. The previous `%…%` LIKE could not use an index either, so performance does not change.
- User-typed `%` and `_` are still treated as wildcards, the same as in the supplier module.
- Case folding covers English letters, as the contract requires. Pinyin, traditional/simplified and segmentation are out of scope.
- `openspec/foundation/api.md` does not describe the trim and case rule for `supplierName`. Updating it is a base change for the maintenance flow and is not part of this change.

## Files

- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/service/impl/BizPurchaseOrderServiceImpl.java`: `buildQueryWrapper` now applies the trimmed, lower-cased contains match on the order's `supplier_name` through `apply`, and skips it when the trimmed value is empty. Also updated the Javadoc and comment and imported `java.util.Locale`. Nothing else in the class changed.
- `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/purchase/BizPurchaseOrderSupplierNameConditionTest.java`: unit tests for the supplier-name matching rule, run against both the list and export query paths.
