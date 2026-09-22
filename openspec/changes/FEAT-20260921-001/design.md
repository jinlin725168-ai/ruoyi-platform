## Context
Supplier management (FEAT-20260918-001) already has CRUD, paging, a 名称/状态 filter and Excel export on biz_supplier. This change adds a single category per supplier. The category values live in the system dictionary. Legacy suppliers with no category, and suppliers whose category value has been deleted from the dictionary, must show as 『未分类』 and be returned by the 『未分类』 filter.

## Goals
- Provide a `biz_supplier_category` dictionary (供应商分类) seeded with 原材料 / 服务 / 设备, maintained only through dictionary management.
- Require a category on create and edit, and reject any value that is not currently in the dictionary with the message 『供应商分类无效』.
- Show the category label in the list, detail and export, falling back to 『未分类』.
- Filter by category, including a 『未分类』 option that matches both empty and deleted category values. Export uses the same filter.
- Keep the SQL re-runnable and leave legacy data unchanged.

## Decisions
### Store the dictionary value in a nullable column
- Choice: add `biz_supplier.supplier_category varchar(100) null` after `supplier_name`. The SQL checks information_schema and only adds the column if it is missing. The dictionary type and data are deleted and re-inserted using IDs in the 1770… range.
- Rationale: this is the standard RuoYi dictionary pattern. The SQL can be re-run safely, and legacy rows stay NULL as required by the no-migration non-goal.
- Alternatives considered: a separate category table, rejected because the contract says no dedicated maintenance page; storing the label text, rejected because it breaks when a label is renamed.

### Validate against the live dictionary through DictService
- Choice: `@NotBlank(groups = {AddGroup, EditGroup})` on `BizSupplierBo.supplierCategory` (分类必填), plus `checkCategoryValid` in the controller for add and edit, using `DictService.getAllDictByDictType`.
- Rationale: DictService is the common-layer API, so no cross-module service dependency is needed. The dictionary cache is evicted when dictionary data is added or deleted, so a new value can be used immediately and a deleted one is rejected immediately (A37, A55).
- Alternatives considered: a custom annotation validator, which needs more plumbing for the same behaviour; a database foreign key, not possible with sys_dict_data.

### Resolve labels on the server with a 『未分类』 fallback
- Choice: `BizSupplierVo.supplierCategoryLabel` is filled after each query (list, detail, export) from the dictionary map. It falls back to `SupplierConstants.CATEGORY_NONE_LABEL` = 『未分类』. The Excel category column uses this label.
- Rationale: the list and export show the same text, and deleted values show as 『未分类』 without extra frontend logic.
- Alternatives considered: `@ExcelDictFormat` or frontend `dict-tag`, which would show the raw value or nothing for deleted values instead of 『未分类』.

### 『未分类』 filter uses a sentinel value
- Choice: the query value `__none__` (`SupplierConstants.CATEGORY_NONE`, mirrored as `SUPPLIER_CATEGORY_NONE` in types.ts) becomes `category is null or = '' or not in (current dictionary values)`. If the dictionary has no values left, no category condition is added, because every supplier then shows as 『未分类』 (fix for review F1).
- Rationale: the filter always matches the displayed label, including the edge case where every dictionary value has been deleted.
- Alternatives considered: an extra boolean query field, which is harder to keep consistent between the select, the list and export.

### Edit form forces re-selection for invalid categories
- Choice: `handleUpdate` clears `form.supplierCategory` when it is not among the current dictionary options. The form has a required rule on category (trigger `change`).
- Rationale: legacy and deleted-category suppliers cannot be saved until a valid category is chosen (A47, A48), and the select never shows a raw code.
- Alternatives considered: showing the raw stored value, which is confusing and fails server validation anyway.

## Risks And Trade-Offs
- `not in (...)` over all dictionary values is fine for a small dictionary but scales with the number of values.
- The label is filled per request from the cached dictionary. Renaming a label changes history-free displays immediately (acceptable; no change log required).
- The existing regression test acceptance/ui/supplier-management/supplier-menu.spec.ts checks for the old header list without 供应商分类. It conflicts with S2 and needs to be updated outside this change; I did not edit it.
- Snowflake 『Clock moved backwards』 errors seen in smoke come from the host clock, not from this code.
- Stopping a category from being selectable without deleting it is out of scope until the dictionary supports enable/disable.

## Files
- sql/biz/FEAT-20260921-001.sql: adds the supplier_category column only if missing; creates the biz_supplier_category dictionary with 原材料/服务/设备.
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/constant/SupplierConstants.java: dictionary type, 『未分类』 sentinel value and label.
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/domain/BizSupplier.java: supplierCategory field.
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/domain/bo/BizSupplierBo.java: supplierCategory, required for AddGroup/EditGroup.
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/domain/vo/BizSupplierVo.java: supplierCategory plus the exported supplierCategoryLabel column.
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/IBizSupplierService.java: checkCategoryValid contract.
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/service/impl/BizSupplierServiceImpl.java: category and 『未分类』 filter, label fill with fallback, dictionary validation.
- backend/ruoyi-modules/ruoyi-biz/src/main/java/org/dromara/biz/supplier/controller/BizSupplierController.java: rejects invalid categories on add/edit with 『供应商分类无效』.
- frontend/src/api/biz/supplier/types.ts: category fields on VO/Form/Query and the SUPPLIER_CATEGORY_NONE constant.
- frontend/src/views/biz/supplier/index.vue: category filter (dictionary values plus 未分类), 供应商分类 column, required category select in the dialog, clears invalid categories on edit, filter passed to export.
