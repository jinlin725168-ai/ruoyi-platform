import { describe, expect, it } from 'vitest';
import source from './index.vue?raw';

// 采购单备注变更（FEAT-20260928-002）前锁定的采购单页面既有行为
// 仓库没有组件测试依赖，这里只对页面源码做包含式断言
const compact = source.replace(/\s+/g, ' ');

/** 取出带某个属性片段的单个标签，便于检查同一标签上的属性组合 */
const tagWith = (tagName: string, fragment: string) => {
  const tags: string[] = compact.match(new RegExp(`<${tagName}\\b[^>]*>`, 'g')) ?? [];
  return tags.filter((tag) => tag.includes(fragment));
};

describe('purchaseOrder page characterization', () => {
  it('keeps the query fields', () => {
    for (const prop of ['orderNo', 'supplierName', 'supplierCategory', 'status']) {
      expect(compact).toContain(`prop="${prop}"`);
    }
    expect(compact).toContain('label="下单日期"');
    expect(compact).toContain('SUPPLIER_CATEGORY_NONE');
  });

  it('keeps the toolbar permissions', () => {
    for (const perm of ['add', 'edit', 'remove', 'export', 'query', 'submit']) {
      expect(compact).toContain(`v-hasPermi="['biz:purchaseOrder:${perm}']"`);
    }
  });

  it('keeps the list columns including the truncated remark column', () => {
    const columns = [
      ['采购单号', 'orderNo'],
      ['供应商', 'supplierName'],
      ['供应商分类', 'supplierCategoryLabel'],
      ['下单日期', 'orderDate'],
      ['状态', 'status'],
      ['合计金额', 'totalAmount'],
      ['备注', 'remark'],
      ['创建时间', 'createTime']
    ];
    for (const [label, prop] of columns) {
      const tags = tagWith('el-table-column', `label="${label}"`).filter((tag) => tag.includes(`prop="${prop}"`));
      expect(tags.length, `${label} column`).toBeGreaterThan(0);
    }
    const remarkColumn = tagWith('el-table-column', 'prop="remark"');
    expect(remarkColumn.some((tag) => tag.includes(':show-overflow-tooltip="true"'))).toBe(true);
  });

  it('keeps the remark form item as a textarea limited to 500 characters', () => {
    expect(compact).toMatch(/<el-form-item label="备注" prop="remark">/);
    const remarkInput = tagWith('el-input', 'v-model="form.remark"');
    expect(remarkInput.length).toBe(1);
    expect(remarkInput[0]).toContain('type="textarea"');
    expect(remarkInput[0]).toContain('maxlength="500"');
  });

  it('keeps the required form rules', () => {
    expect(compact).toContain("supplierId: [{ required: true, message: '供应商不能为空', trigger: 'change' }]");
    expect(compact).toContain("orderDate: [{ required: true, message: '下单日期不能为空', trigger: 'change' }]");
  });

  it('keeps the detail view items including remark', () => {
    for (const label of ['采购单号', '供应商', '下单日期', '状态', '合计金额', '创建时间', '备注']) {
      expect(compact).toContain(`<el-descriptions-item label="${label}"`);
    }
    expect(compact).toContain('{{ viewOrder?.remark }}');
  });

  it('keeps remark in the initial form, edit backfill and submit payload', () => {
    expect(compact).toMatch(/const initFormData: PurchaseOrderForm = \{[^}]*remark: ''/);
    expect(compact).toContain('form.value.remark = order.remark;');
    expect(compact).toContain('remark: form.value.remark,');
  });

  it('keeps the draft status code and the save and export endpoints', () => {
    expect(compact).toContain("const STATUS_DRAFT = '0';");
    expect(compact).toContain('await updatePurchaseOrder(payload)');
    expect(compact).toContain('await addPurchaseOrder(payload)');
    expect(compact).toContain("'biz/purchaseOrder/export'");
  });
});
