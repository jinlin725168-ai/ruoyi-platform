import { describe, expect, expectTypeOf, it } from 'vitest';
import type { SupplierQuery } from './types';

// 编码查询条件（FEAT-20260924-001）：原样发给后端，由后端去首尾空白并忽略大小写
describe('supplier code query', () => {
  it('accepts an optional supplierCode condition', () => {
    expectTypeOf<SupplierQuery>().toHaveProperty('supplierCode').toEqualTypeOf<string | undefined>();
    const query: SupplierQuery = { pageNum: 1, pageSize: 10, supplierCode: ' Ab 01 ' };
    expect(query.supplierCode).toBe(' Ab 01 ');
  });
});
