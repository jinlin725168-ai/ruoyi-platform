import { describe, expect, it } from 'vitest';
import source from './index.vue?raw';

// FEAT-20260928-002：备注表单项在源码中排在供应商之前，避免"供应商名称含『备注』"时按文字定位到供应商表单项；
// 通过 flex order 仍渲染在该行最后
const compact = source.replace(/\s+/g, ' ');

const addEditDialog = () => {
  const start = compact.indexOf('<el-dialog v-model="dialog.visible"');
  const end = compact.indexOf('</el-dialog>', start);
  expect(start).toBeGreaterThanOrEqual(0);
  return compact.slice(start, end);
};

describe('purchaseOrder remark form item order', () => {
  it('places the remark item before the supplier item in source order', () => {
    const dialog = addEditDialog();
    const remarkIndex = dialog.indexOf('<el-form-item label="备注" prop="remark">');
    const supplierIndex = dialog.indexOf('<el-form-item label="供应商" prop="supplierId">');
    expect(remarkIndex).toBeGreaterThanOrEqual(0);
    expect(supplierIndex).toBeGreaterThanOrEqual(0);
    expect(remarkIndex).toBeLessThan(supplierIndex);
  });

  it('keeps the remark item rendered last in the row via a scoped order style', () => {
    const dialog = addEditDialog();
    expect(dialog).toMatch(/<el-col class="remark-col" :span="24"> <el-form-item label="备注" prop="remark">/);
    const style = compact.slice(compact.indexOf('<style'));
    expect(style).toMatch(/\.remark-col \{ order: 1; \}/);
  });
});
