import { describe, expect, it } from 'vitest';
import { SUPPLIER_CATEGORY_NONE } from './types';
import type { SupplierQuery } from './types';

// 编码查询条件变更（FEAT-20260924-001）前锁定的既有行为
describe('supplier types characterization', () => {
  it('keeps the uncategorized query value', () => {
    expect(SUPPLIER_CATEGORY_NONE).toBe('__none__');
  });

  it('keeps existing query fields', () => {
    const query: SupplierQuery = {
      pageNum: 1,
      pageSize: 10,
      supplierName: '钢铁',
      status: '1',
      supplierCategory: SUPPLIER_CATEGORY_NONE
    };
    expect(Object.keys(query)).toEqual(expect.arrayContaining(['pageNum', 'pageSize', 'supplierName', 'status', 'supplierCategory']));
  });
});
