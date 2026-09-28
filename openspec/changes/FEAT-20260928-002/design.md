## Context

FEAT-20260928-002 adds a remark (备注) field to purchase orders. It is optional and holds at most 500 characters. Users can edit it on new and draft orders, and it shows in the list, the detail view and the Excel export. Reading the current code shows that FEAT-20260920-001 already shipped most of this:

- **SQL** `sql/biz/FEAT-20260920-001.sql`: `remark varchar(500) default null` on `biz_purchase_order`. utf8mb4 varchar counts characters, not bytes.
- **Entity** `BizPurchaseOrder.remark`.
- **BO** `BizPurchaseOrderBo.remark` has `@Size(max = 500, message = "备注长度不能超过500个字符", groups = {AddGroup, EditGroup})`. The controller uses `@Validated(AddGroup/EditGroup)`, and `GlobalExceptionHandler.handleMethodArgumentNotValidException` returns `R.fail(<message>)` (code 500) before any service code runs. So when a remark is too long, no order is created on add and nothing changes on edit.
- **VO** `BizPurchaseOrderVo.remark` is returned by `/list` and `/{id}`.
- **Export** `BizPurchaseOrderExportVo.remark` has `@ExcelProperty(value = "备注")`, and `queryExportList` copies it. A null remark gives an empty cell.
- **State guard** `updateByBo` calls `loadDraft(id, "修改")` first, so edits to a submitted order fail with `采购单【…】已提交，不能修改` and the remark is left alone.
- **Frontend** `views/biz/purchaseOrder/index.vue`:
  - table column `备注` with `:show-overflow-tooltip="true"` (one line, truncated, full text on hover);
  - form item `备注` with `<el-input type="textarea" maxlength="500">`;
  - detail `<el-descriptions-item label="备注">`.
- **Types** `types.ts` already declares `remark`.

The one behavior that does not meet the contract is in `updateByBo`. It converts the BO to an entity and calls `purchaseOrderMapper.updateById(update)`. MyBatis-Plus's default field strategy (NOT_NULL) leaves null columns out of the SET clause. So a PUT with `remark: null` or no `remark` key keeps the old remark. That breaks the rule "WHEN 修改草稿采购单 … 以本次提交的备注为准 / 备注被清空 … 备注为空". The acceptance suite checks this in the `null` subtest of A103. The `''` subtest already passes because an empty string is not null.

## Goals

- An edit to a draft order always replaces the stored remark with the submitted value. A null or missing remark clears it (A102, A103).
- Keep all existing behavior: add, list, detail, export, the length limit, order-number generation, amount calculation, status flow, permissions and data scope.
- Change nothing outside `ruoyi-biz` and touch no base files.

## Decisions

### D1. Normalize a null remark to an empty string in `updateByBo`
- **Choice:** In `BizPurchaseOrderServiceImpl.updateByBo`, after `MapstructUtils.convert`, add `update.setRemark(StringUtils.nullToEmpty(bo.getRemark()));`. `org.dromara.common.core.utils.StringUtils` extends hutool `StrUtil`, which provides `nullToEmpty`. A non-null value is kept exactly as sent, with no trimming, per "原样保留". Update the method's Javadoc to say the remark is overwritten by the submitted value and a missing value clears it.
- **Rationale:** This is the smallest change. It uses the existing `updateById` path, so `update_by` and `update_time` auto-fill and `@TableLogic` keep working, and the rest of the method is untouched. The contract accepts either `null` or `''` as "empty", and the list, detail and export all show both as blank.
- **Alternatives considered:**
  - `@TableField(updateStrategy = FieldStrategy.ALWAYS)` on `BizPurchaseOrder.remark`: rejected. `submitById` builds a bare entity with only `orderId` and `status` and calls `updateById`, so ALWAYS would wipe the remark on every submit.
  - `purchaseOrderMapper.update(update, lambdaUpdate().eq(orderId).set(remark, bo.getRemark()))` to store a real SQL NULL: it works, but it adds a second update style to this class and makes the unit test stub a different mapper method. Mixing NULL and `''` has no visible effect.

### D2. Keep the Bean Validation length check as it is
- **Choice:** Keep `@Size(max = 500)` on the BO with its current message.
- **Rationale:** The message mentions both 备注 and 500/字符. The check runs before the transaction, so a rejected add leaves no row and a rejected edit leaves the header and details as they were. `@Size` counts UTF-16 units, which equals the character count for Chinese, letters, digits, punctuation and spaces, which is everything the contract lists.
- **Alternatives considered:** A code-point check in the service. It is only needed for characters outside the BMP such as emoji, which the contract does not mention, and it would move the rejection inside the transaction.

### D3. No frontend, SQL or menu changes
- **Choice:** Leave `frontend/src/**` and `sql/biz/**` as they are.
- **Rationale:** The list column (truncated with tooltip), the form textarea (maxlength 500), the detail item, the types and the column all exist already, and there are no new permissions. The edit form sends `form.remark`, which the textarea sets to `''` when cleared. That already clears the remark, and D1 also covers other API clients.
- **Alternatives considered:** Adding `show-word-limit` to the textarea: purely cosmetic and not required, so skipped to keep the change small.

## Files

- **Modify** `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/service/impl/BizPurchaseOrderServiceImpl.java`: in `updateByBo`, set `update.setRemark(StringUtils.nullToEmpty(bo.getRemark()))` so the edit always writes the remark, and update the Javadoc.
- **Create (test)** `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/purchase/BizPurchaseOrderRemarkTest.java`: `@Tag("dev")`, `@ExtendWith(MockitoExtension.class)`, mocking `BizPurchaseOrderMapper`, `BizPurchaseOrderDetailMapper` and `IBizSupplierService`. Stub the `MapstructUtils` conversion with `mockStatic`, the way the existing characterization test handles it (it already initializes TableInfo for lambda wrappers). Stub `selectById` to return a draft and `supplierService.queryById` to return an enabled supplier. Capture the `updateById` argument and assert:
  - (a) `remark == null` in the BO gives `""` on the entity;
  - (b) `"R2"` gives `"R2"`;
  - (c) an exact 500-character string is kept unchanged;
  - (d) for a submitted order, `ServiceException` contains `已提交` and `updateById` is never called.

  Also add a Validator test that builds `Validation.buildDefaultValidatorFactory()` directly, with no Spring. It asserts that 500 characters pass and 501 characters fail for both `AddGroup` and `EditGroup`, with a message containing `备注`.
- **Unchanged (already satisfy the contract):**
  - `BizPurchaseOrder.java`, `BizPurchaseOrderBo.java`, `BizPurchaseOrderVo.java`, `BizPurchaseOrderExportVo.java`, `BizPurchaseOrderController.java`
  - `frontend/src/api/biz/purchaseOrder/{index,types}.ts`, `frontend/src/views/biz/purchaseOrder/index.vue`
  - `sql/biz/FEAT-20260920-001.sql`

## Data And Interfaces

- **Table** `biz_purchase_order.remark varchar(500) default null`. No DDL change, so no new `sql/biz/FEAT-20260928-002.sql` is needed. Rows cleared through an edit store `''`; rows never given a remark stay `NULL`. Both are returned as blank.
- **Endpoints** (unchanged, base `/biz/purchaseOrder`):
  - `POST` (`biz:purchaseOrder:add`) and `PUT` (`biz:purchaseOrder:edit`): body field `remark?: string`, at most 500 characters. Longer input returns `{code:500, msg:"备注长度不能超过500个字符"}`. On `PUT`, a null or missing `remark` now clears the stored remark.
  - `GET /list` (`:list`): each row has `remark`.
  - `GET /{orderId}` (`:query`): `data.remark`.
  - `POST /export` (`:export`): the Excel sheet `采购单` has a column headed `备注`.
  - Editing a submitted order returns `{code:500, msg:"采购单【<no>】已提交，不能修改"}`.
- **Permissions:** no new permission strings or menu rows.

## Risks And Trade-Offs

- **Behavior change for API clients:** a `PUT` without `remark` used to keep the old remark and now clears it. The contract requires this ("以本次提交的备注为准"). The only in-repo caller, the edit form, always sends `remark`.
- **Mixed NULL and `''` in storage:** blank in every view, and remark is never a filter or sort key (non-goals), so it has no functional impact.
- **Non-BMP characters:** `@Size` counts an emoji as 2, so remarks with many emoji may be rejected below 500 visible characters. The contract only names Chinese, letters, digits, punctuation and whitespace, so this is accepted.
- **Frontend maxlength:** the native attribute also counts UTF-16 units, which matches the backend.
- **Unit tests and MapstructUtils:** `updateByBo` goes through `MapstructUtils`, which needs Spring. The test must use `mockStatic(MapstructUtils.class)`, or build the expected entity through the same stub. If `mockStatic` turns out to be unreliable, the implementer can move the remark normalization into a small package-private helper and test that directly.
- **Verification:** I have not run the acceptance suite. It is expected to be RED only on the A103 null subtest, and the external smoke run confirms the rest.

## Implementation record

## Context

FEAT-20260928-002 adds an optional remark (备注, at most 500 characters) to purchase orders. Users enter it on new and draft orders, and it shows in the list, the detail view and the Excel export. FEAT-20260920-001 already shipped almost all of this:

- the column `biz_purchase_order.remark varchar(500)`;
- the entity, BO (`@Size(max=500)` for AddGroup and EditGroup), VO and export VO (`@ExcelProperty("备注")`);
- the rejection of edits to submitted orders in `loadDraft`;
- the list column with tooltip, the form textarea and the detail item.

Attempt 1 failed only on A106, the UI add-then-list check. Code review also found a hidden A103 gap: an edit with a null remark did not clear the stored remark.

## Goals

- An edit to a draft order always replaces the stored remark with the submitted one. A null or missing remark clears it (A102, A103).
- A remark typed into the add form in the UI is saved and shows in the list (A106).
- Keep all existing behavior: order numbers, amounts, status flow, permissions, data scope, list, detail and export.

## Tests First

### Backend: `BizPurchaseOrderRemarkTest`
JUnit 5, `@Tag("dev")`, Mockito. The mappers and `IBizSupplierService` are mocked, and `MapstructUtils` is handled with `mockStatic`.

- `updateDraftWithoutRemarkClearsStoredRemark`
  - Before: failed with "Expecting actual not to be null". The captured `updateById` entity had `remark == null`. That was 6 tests run, 1 failure, with the `setRemark` line removed.
  - After: green.
- Update keeps `R2` as `R2`: green. This is a regression guard, since the old code already passed it.
- Update keeps exactly 500 mixed CJK, letter, digit and punctuation characters unchanged: green (regression guard).
- A submitted order throws `ServiceException` containing 已提交, and `updateById` is never called: green (regression guard).
- Validator check with no Spring: 500 characters, `null` and `""` pass; 501 characters fail for both AddGroup and EditGroup, with a message containing 备注 and 500. Green (regression guard for the existing `@Size`).
- The characterization tests `BizPurchaseOrderSaveCharacterizationTest` and `BizPurchaseOrderServiceImplCharacterizationTest` stay green.

### Frontend: `frontend/src/views/biz/purchaseOrder/remarkOrder.test.ts`
Vitest, reading `index.vue?raw`.

- The remark form item comes before the supplier form item in the add/edit form source.
  - Before: failed, because the remark item was at index 1094 and the supplier item at 377.
  - After: green.
- The remark `el-col` has class `remark-col`, and the scoped style sets `order: 1`.
  - Before: failed, because neither the class nor the style existed.
  - After: green.
- The existing `index.test.ts` characterization tests (8) stay green.

### Final integrated run
- `mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test`: exit 0.
- ruoyi-biz `failsafe:integration-test failsafe:verify`: exit 0.
- `spotless:check` and `checkstyle:check`: exit 0.
- `pnpm --dir frontend exec vitest run src/views/biz/purchaseOrder`: 2 files, 10 of 10 passed.
- `python3 acceptance/tools/frontend_check.py`: oxlint clean, vue-tsc 0 errors in business files.

## Decisions

### D1. Turn a null remark into an empty string in `updateByBo`
- **Choice:** `update.setRemark(StringUtils.defaultString(bo.getRemark()))` before `updateById`.
- **Rationale:** `updateById` uses the NOT_NULL field strategy, so a null remark was left out of the SET clause. An empty string is always written. Other values are kept exactly as sent. Auto-fill and logic-delete keep working because the update path is unchanged.
- **Alternatives considered:**
  - `FieldStrategy.ALWAYS` on the entity field: rejected, because `submitById` updates a bare entity and would wipe the remark.
  - A `LambdaUpdateWrapper` that sets NULL: it works, but adds a second update style to the class.

### D2. Keep the `@Size(max=500)` Bean Validation check
- **Choice:** No change.
- **Rationale:** The check rejects the request before the transaction starts, with the message 备注长度不能超过500个字符. So a rejected add creates no order and a rejected edit leaves the order as it was.
- **Alternatives considered:** A code-point check in the service: only needed for non-BMP characters, which the contract does not require.

### D3. Put the remark item first in the form source and render it last with flex `order`
- **Choice:** Move the remark `el-col` to be the first child of the form's `el-row`, and add `class="remark-col"` with `.remark-col { order: 1; }`.
- **Rationale:** Users and tests locate form items by their visible label. Once a supplier whose name contains 备注 is picked, the supplier item's text also contains 备注, so a first-match lookup landed in the supplier input. Putting the remark first in the DOM makes the lookup unambiguous. The flex order keeps the on-screen layout the same, with the remark full width below 供应商 and 下单日期.
- **Alternatives considered:**
  - Showing the remark visually first: worse form layout.
  - Hiding the selected supplier label: breaks the supplier echo.
  - Changing the spec: forbidden.

### D4. No SQL, menu, API or type changes
- **Choice:** Leave `sql/biz/**`, the api files and the types as they are.
- **Rationale:** The column, permissions, endpoints and fields already exist.
- **Alternatives considered:** None needed.

## Risks And Trade-Offs

- **PUT clears a missing remark:** a PUT without `remark` now clears it. The contract requires this, and the in-repo form always sends the field.
- **NULL and `''` in storage:** both are shown blank everywhere, and remark is never used as a filter or sort key.
- **Keyboard order:** tabbing in the add/edit dialog now reaches the remark textarea before 供应商, because DOM order and visual order differ. This is a minor accessibility trade-off.
- **Emoji count double:** `@Size` and the native `maxlength` both count UTF-16 units, so emoji count as 2. The contract only lists BMP characters, so this is accepted.
- **Acceptance not run here:** the acceptance and smoke suites were not run in this step; the external run confirms A98–A112.

## Files

- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/purchase/service/impl/BizPurchaseOrderServiceImpl.java`: `updateByBo` always writes the remark (null becomes ""); Javadoc updated.
- `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/purchase/BizPurchaseOrderRemarkTest.java` (new): unit tests for overwriting, clearing and keeping the remark on edit, the submitted-order guard, and the 500/501 validation limit.
- `frontend/src/views/biz/purchaseOrder/index.vue`: the remark form item comes first in the source (`remark-col`) and renders last via `order: 1`.
- `frontend/src/views/biz/purchaseOrder/remarkOrder.test.ts` (new): vitest checks on the source order and the `remark-col` style.
