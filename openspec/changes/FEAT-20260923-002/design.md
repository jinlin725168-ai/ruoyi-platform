## Context
On the supplier list (`/biz/supplier/list`) and export (`/biz/supplier/export`), the name condition was a plain `like` on the raw input. Extra spaces before or after the name, whitespace picked up when pasting (full-width spaces, tabs, newlines), or different letter case caused missed matches. Both endpoints build their query in `BizSupplierServiceImpl.buildQueryWrapper`: `queryPageList` for the list and `queryList` for the export.

## Goals
- Remove all leading and trailing whitespace from the name condition (half-width spaces, full-width spaces, tabs, newlines) before matching.
- Ignore letter case when matching; keep the existing contains-style match.
- Keep whitespace inside the name exactly as typed.
- Treat a name that is empty after trimming as no name condition.
- Apply the same rule to list and export. Leave status and category matching unchanged.

## Tests First
Test class: `BizSupplierNameConditionTest` (`@Tag("dev")`, Mockito, no Spring context). Each test captures the `LambdaQueryWrapper` passed to both `selectVoPage` (list) and `selectVoList` (export) and checks the SQL fragment and the bound parameters.

To see red, I temporarily restored the original `lqw.like(isNotBlank(name), supplierName, name)`:
- `trimsHalfWidthSpacesAroundName`: failed. The parameter was `%   Acme   %`; the test expected `%acme%`.
- `trimsFullWidthSpacesAroundName`: failed. The parameter was `%　　钢铁　%`; the test expected `%钢铁%`.
- `trimsTabsNewlinesAndMixedWhitespaceAroundName`: failed. The parameter still contained the full-width space, tab and CRLF.
- `matchesNameIgnoringCase`: failed. The SQL was `(supplier_name LIKE ...)` with no `lower(supplier_name) like`.
- `keepsInnerWhitespaceAfterTrimAndLowerCase`: failed. The parameter was `%  Acme Steel\t%`; the test expected `%acme steel%`.
- `whitespaceOnlyNameIsTreatedAsNoNameCondition`: already passed on the old code. Apache `isNotBlank` uses `Character.isWhitespace`, which counts U+3000 as whitespace, so an all-whitespace name was already skipped. I kept the test as a guard for the new trim-then-`isNotEmpty` path.

Green: with the implementation restored, the class passes 6/6. The characterization test `BizSupplierServiceImplCharacterizationTest` still passes 8/8. The regression command `mvn -q -o -f backend/pom.xml -Dmaven.test.skip=false -DskipTests=false -pl ruoyi-admin -am test` exits 0, the failsafe integration layer exits 0, and `vue-tsc --noEmit` exits 0.

## Decisions
- **Choice:** Trim with the project's `StringUtils.trim`, which calls Hutool `StrUtil.trim`.
  **Rationale:** It is an existing building block, and `CharUtil.isBlankChar` covers half-width spaces, U+3000, tabs, CR and LF, as the clarification requires.
  **Alternatives considered:** `String.strip()` (also covers U+3000, but differs from the rest of the codebase); a custom regex (re-implements what already exists).
- **Choice:** Match case-insensitively with `lqw.apply("LOWER(supplier_name) LIKE {0}", "%" + lower + "%")`, lower-casing with `Locale.ROOT`.
  **Rationale:** It does not depend on the column collation, and `{0}` binds as a parameter, so there is no SQL injection risk.
  **Alternatives considered:** Relying on MySQL's `utf8mb4_general_ci` collation (implicit and fragile if the collation changes); `ILIKE` (not supported by MySQL).
- **Choice:** Change only the shared `buildQueryWrapper`.
  **Rationale:** The list and export then cannot drift apart.
  **Alternatives considered:** Normalizing in the controller or BO (would touch more files and would not protect other service callers).

## Risks And Trade-Offs
- `LOWER(column)` prevents MySQL from using an index on `supplier_name`. The previous `%x%` pattern already could not use one, so performance does not get worse.
- `%` and `_` typed by the user still act as SQL wildcards, as before. This behaviour is unchanged.
- Only the query condition is normalized. Stored names are not modified, which the non-goals require.

## Files
- `backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/impl/BizSupplierServiceImpl.java`: the name condition is trimmed, checked for emptiness, and matched case-insensitively with a contains match; shared by list and export.
- `backend/ruoyi-modules/ruoyi-biz/src/test/java/org/dromara/biz/supplier/BizSupplierNameConditionTest.java`: unit tests for trimming, case-insensitivity, kept inner whitespace, and whitespace-only input on both the list and export paths.
