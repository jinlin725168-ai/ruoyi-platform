## Context
The supplier list (`GET /biz/supplier/list`) and export (`POST /biz/supplier/export`) both build their query in `BizSupplierServiceImpl.buildQueryWrapper(bo)`, through `queryPageList` and `queryList`. FEAT-20260923-002 already made the name condition a contains match that trims leading and trailing whitespace, ignores letter case and keeps inner whitespace (`lqw.apply("LOWER(supplier_name) LIKE {0}", ...)`). `BizSupplierBo.supplierCode` already exists, because add and edit use it. The controller binds list and export query strings to `BizSupplierBo`, so `supplierCode` already reaches the service, but `buildQueryWrapper` ignores it. The page `views/biz/supplier/index.vue` only has name, status and category search fields. `download('biz/supplier/export', {...queryParams})` and `listSupplier(queryParams)` both send the whole `queryParams` object, so a new query field reaches list and export without API changes.

## Goals
- Add a code condition to list and export: contains match, leading and trailing whitespace removed (half-width and full-width spaces, tabs, line breaks), letter case ignored, inner whitespace kept. A code that is empty after trimming counts as no condition.
- Combine the code condition with the name, status and category conditions using AND. Export filters exactly like the list, because both share one builder.
- Add a 供应商编码 search field to the page.
- Non-goals, kept unchanged: name, status and category rules; storing the code as entered on add and edit; `checkCodeUnique` stays a case-sensitive `eq`; columns, paging, permissions and sort order.

## Decisions
- **Choice:** Add the code condition inside the existing private `buildQueryWrapper`, just before the name condition, using the same pattern: `String code = StringUtils.trim(bo.getSupplierCode()); if (StringUtils.isNotEmpty(code)) { lqw.apply("LOWER(supplier_code) LIKE {0}", "%" + code.toLowerCase(Locale.ROOT) + "%"); }`. Also update the method's Javadoc and inline comment to mention code.
  **Rationale:** List and export already share this builder, so they cannot drift apart. It mirrors the approved name rule exactly, which the contract requires ("与名称条件相同"). `StringUtils.trim` (Hutool `CharUtil.isBlankChar`) covers U+3000, `\t`, `\r` and `\n`. `{0}` is a bound parameter, so there is no SQL injection risk. `LOWER()` makes the match independent of column collation.
  **Alternatives considered:** `lqw.like(BizSupplier::getSupplierCode, ...)` relies on the `_ci` collation for case-insensitivity, which is implicit. Normalizing in the controller or BO touches more files, and the BO is also the add/edit input, so the code would risk being normalized on save, which the non-goals forbid. A shared private helper `applyContainsIgnoreCase(lqw, column, value)` for both name and code would be optional; it is not required, and the implementer may introduce it only if the characterization and name tests stay green.
- **Choice:** Do not change `BizSupplierBo`. `supplierCode` keeps its `AddGroup`-only `@NotBlank`/`@Size`.
  **Rationale:** List and export bind the BO without validation groups, so a long or blank query code is never rejected. Store-as-entered and uniqueness behaviour stay the same.
  **Alternatives considered:** A separate query DTO. That duplicates fields for no benefit.
- **Choice:** On the frontend, add one `el-form-item label="供应商编码" prop="supplierCode"` with a clearable `el-input` (placeholder `请输入供应商编码`, `@keyup.enter="handleQuery"`) as the first item of the search form. Add `supplierCode: undefined` to the initial `queryParams`, and `supplierCode?: string` to `SupplierQuery`. Leave the value untouched on the client; the server normalizes it.
  **Rationale:** This satisfies "在查询区提供编码查询条件". `useSearchReset` resets fields by `prop`, so the reset button clears the new field. Export picks it up through `...queryParams`. Server-side normalization is the single source of truth, so API callers get the same result.
  **Alternatives considered:** Trimming on the client as well. That is redundant, and it could make UI behaviour differ from API behaviour.

## Files
- Modify `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/impl/BizSupplierServiceImpl.java`: add the code condition in `buildQueryWrapper` (trim, skip if empty, `LOWER(supplier_code) LIKE %lower%`) and update the Javadoc. No other method changes; `checkCodeUnique`, `insertByBo` and `updateByBo` stay as they are.
- Modify `frontend/src/api/biz/supplier/types.ts`: add `supplierCode?: string` (commented 供应商编码（模糊匹配）) to `SupplierQuery`.
- Modify `frontend/src/views/biz/supplier/index.vue`: add the code input to the search form, and add `supplierCode: undefined` to the initial `queryParams`.
- Create `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/supplier/BizSupplierCodeConditionTest.java` (`@Tag("dev")`, Mockito, no Spring, `TableInfoHelper.initTableInfo` like the characterization test). Capture the wrapper passed to `selectVoPage` (list) and `selectVoList` (export) and cover:
  - fragment in the middle of the code: `%b0%`;
  - half-width spaces around the code, e.g. `"  AB01  "` gives `%ab01%`;
  - full-width space and tab before, line break after;
  - upper case gives lower-cased parameter and `LOWER(supplier_code) LIKE` in the SQL;
  - inner space kept: `"ab 01"` gives `%ab 01%`;
  - null, empty and mixed whitespace-only code gives no `supplier_code` in the SQL;
  - code combined with name and status gives all three conditions.
- Unchanged (for the record): `BizSupplierController.java`, `BizSupplierBo.java`, `frontend/src/api/biz/supplier/index.ts`, `BizSupplierMapper.xml`. No `sql/biz` file is needed: no new table, column, dictionary entry or menu.

## Data And Interfaces
- Table `biz_supplier`: no schema change. Queries use the existing column `supplier_code`, which has an ordinary index.
- `GET /biz/supplier/list`: new optional query parameter `supplierCode` (string), next to `supplierName`, `status`, `supplierCategory`, `pageNum` and `pageSize`. Response `R<PageResult<BizSupplierVo>>` does not change.
- `POST /biz/supplier/export`: the same optional form or query parameter `supplierCode`, with the same filter semantics. Excel columns do not change.
- Condition added to the SQL: `LOWER(supplier_code) LIKE ?`, with parameter `'%' + trim(code).toLowerCase(ROOT) + '%'`. It is combined with the other conditions using AND and applied before `ORDER BY supplier_id DESC`. Logical deletion is still added automatically.
- Permissions do not change: `biz:supplier:list` for the list and `biz:supplier:export` for the export.
- Frontend: `SupplierQuery.supplierCode?: string`; the new form item uses `prop="supplierCode"`.

## Risks And Trade-Offs
- `LOWER(supplier_code)` with a leading `%` cannot use the `supplier_code` index. That is acceptable at current data volume and matches the name condition. Exact-code lookups through this endpoint become scans. `checkCodeUnique` keeps its indexed `eq`.
- `%` and `_` typed by the user still act as SQL wildcards, the same as the name condition. The contract does not require escaping them.
- `Locale.ROOT` lower-casing only matters for English letters, which is all the contract requires. Non-ASCII case folding is not specified.
- Contract rule: "仅大小写不同的编码不视为重复". Search may now return several suppliers whose codes differ only in case. That is intended, because the uniqueness check is unchanged.
- The characterization test `noConditionQueriesAllOrderedByIdDesc` only asserts `supplier_name`, `status` and `supplier_category`, so it stays green. The existing name, category and characterization tests must stay green without edits.

## Implementation record

## Context
The supplier list (`GET /biz/supplier/list`) and export (`POST /biz/supplier/export`) both build their query in `BizSupplierServiceImpl.buildQueryWrapper(bo)`. `BizSupplierBo.supplierCode` already existed for add and edit, and the controller already binds it for list and export, but the builder ignored it. FEAT-20260923-002 had already made the name condition a trimmed, case-insensitive contains match. The page `views/biz/supplier/index.vue` had only name, status and category search fields. It sends the whole `queryParams` to both `listSupplier` and the export download.

## Goals
- Add a code condition to list and export: contains match, leading and trailing whitespace removed (half-width and full-width spaces, tabs, CR/LF), letter case ignored, inner whitespace kept. A code that is empty after trimming counts as no condition.
- Combine the code condition with name, status and category using AND. Export filters exactly like the list.
- Add a 供应商编码 search input to the page.
- Unchanged: name, status and category rules; codes are stored as entered; `checkCodeUnique` stays a case-sensitive `eq`; columns, paging, permissions and sort order.

## Tests First
Backend: `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/supplier/BizSupplierCodeConditionTest.java` (`@Tag("dev")`, Mockito, no Spring context, `TableInfoHelper.initTableInfo`). Each test captures the wrapper passed to `selectVoPage` (list) and to `selectVoList` (export) and asserts on both.
- `matchesCodeFragmentAsContains`: input `b0` should give `LOWER(supplier_code) LIKE` with parameter `%b0%`. **Red:** the SQL segment was only ` ORDER BY supplier_id DESC`.
- `trimsHalfWidthSpacesAroundCode`: `"   AB01  "` should give `%ab01%`. **Red:** the parameter list was `[]`.
- `trimsFullWidthSpaceTabAndNewlineAroundCode`: `"　\tAB01\r\n"` should give `%ab01%`. **Red:** the parameter list was `[]`.
- `matchesCodeIgnoringCase`: `SUP-AB`, `sup-ab` and `Sup-aB` should all give `lower(supplier_code) like` with `%sup-ab%`. **Red:** there was no code condition in the SQL.
- `keepsInnerWhitespaceInCode`: `" Ab 01 "` should give `%ab 01%`. **Red:** the parameter list was `[]`.
- `combinesCodeWithNameAndStatus`: the SQL should contain the code, name and status conditions, with parameters `%ab01%`, `%acme%` and `0`. **Red:** the SQL was `(LOWER(supplier_name) LIKE … AND status = …)` with no code condition.
- `blankOrWhitespaceOnlyCodeIsTreatedAsNoCodeCondition`: a null, empty, or mixed whitespace-only code gives no `supplier_code` in the SQL, and the only parameter is the status. This test already passed before the change, as expected, because the builder ignored the code entirely. It guards that the new code does not add an empty condition.
- **Green:** after the change the class ran 7/7 green. The regression command `mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test` passed with no edits to the existing characterization, name and category tests. Biz failsafe `integration-test`/`verify`, `spotless:check` and `checkstyle:check` also passed.

Frontend: `frontend/src/api/biz/supplier/query.test.ts`.
- `accepts an optional supplierCode condition`: `expectTypeOf<SupplierQuery>().toHaveProperty('supplierCode')` is `string | undefined`, and a query object carrying `' Ab 01 '` keeps the value unchanged. Vitest does not type-check at runtime, so I observed red with `vue-tsc --noEmit`: TS2345 `"supplierCode"` is not assignable to `keyof SupplierQuery`, and TS2353 `supplierCode` does not exist in type `SupplierQuery`. **Green:** after adding the field, `vitest run query.test.ts types.test.ts` passed (3 tests), and `acceptance/tools/frontend_check.py` reported 0 errors in business files.

## Decisions
- **Choice:** Add the code condition in the existing private `buildQueryWrapper`, before the name condition, in the same form: `StringUtils.trim`, then `isNotEmpty`, then `lqw.apply("LOWER(supplier_code) LIKE {0}", "%" + code.toLowerCase(Locale.ROOT) + "%")`. Update the Javadoc and add an inline comment. **Rationale:** List and export share the builder, so they cannot drift apart. It mirrors the approved name rule exactly. Hutool's trim covers U+3000, tab, CR and LF. `{0}` is a bound parameter, so there is no injection risk. `LOWER()` makes the match independent of column collation. **Alternatives considered:** `lqw.like(...)`, which would rely on the implicit `_ci` collation. Normalizing in the controller or BO, which would risk normalizing codes on save, and the non-goals forbid that. A shared helper for name and code, which I skipped because two short blocks read clearly and a helper would add churn to tested code.
- **Choice:** Leave `BizSupplierBo`, the controller, `index.ts` and the mapper XML unchanged. **Rationale:** The field is already bound for list and export, and the frontend already sends the whole `queryParams`. **Alternatives considered:** A separate query DTO. It would only duplicate fields.
- **Choice:** Add a clearable `el-input` with `prop="supplierCode"` as the first search item, plus `supplierCode: undefined` in the initial `queryParams`. The value is sent unchanged, and the server normalizes it. **Rationale:** This meets "查询区提供编码查询条件". The reset button clears the field by `prop`, and export picks it up through `...queryParams`. With one source of truth, UI and API callers get the same results. **Alternatives considered:** Also trimming on the client. It would be redundant and could make UI behaviour differ from API behaviour.
- **Choice:** Test the frontend type contract in a new `query.test.ts` with `expectTypeOf`, and leave the characterization file `types.test.ts` untouched. **Rationale:** The only frontend logic is a type field, and `vue-tsc` enforces `expectTypeOf`, which gave a real red. **Alternatives considered:** A component test, which is not possible because the repo has no `@vue/test-utils`.

## Risks And Trade-Offs
- `LOWER(supplier_code) LIKE '%…%'` cannot use the `supplier_code` index. That is acceptable at current data volume and matches the name condition. `checkCodeUnique` keeps its indexed `eq`.
- `%` and `_` typed by the user still act as SQL wildcards, the same as the name condition. The contract does not require escaping them.
- `Locale.ROOT` lower-casing is only specified for English letters.
- Search can now return several suppliers whose codes differ only in case. That is intended, because uniqueness stays case-sensitive by contract.
- The frontend type test runs only under `vue-tsc` and manual vitest; neither is in the automated regression. Page behaviour is verified by the external acceptance run.

## Files
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/impl/BizSupplierServiceImpl.java`: adds the code condition to `buildQueryWrapper` (trim, skip if empty, case-insensitive contains) and updates its Javadoc.
- `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/supplier/BizSupplierCodeConditionTest.java` (new): unit tests for the code condition on both the list and export paths.
- `frontend/src/api/biz/supplier/types.ts`: `SupplierQuery.supplierCode?: string` (供应商编码（模糊匹配）).
- `frontend/src/api/biz/supplier/query.test.ts` (new): type and value contract for the `supplierCode` query field.
- `frontend/src/views/biz/supplier/index.vue`: the 供应商编码 search input and `supplierCode: undefined` in the initial `queryParams`.
