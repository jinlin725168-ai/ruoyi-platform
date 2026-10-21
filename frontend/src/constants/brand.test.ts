import { describe, expect, it } from 'vitest';
import { BRAND_FULL_NAME, BRAND_SHORT_NAME, formatBrandTitle } from './brand';

describe('brand titles', () => {
  it('provides the approved brand names', () => {
    expect(BRAND_FULL_NAME).toBe('红魔业务工作台');
    expect(BRAND_SHORT_NAME).toBe('红魔');
  });
  it('combines a page title when enabled', () => {
    expect(formatBrandTitle('首页', true)).toBe(`首页 - ${BRAND_FULL_NAME}`);
  });
  it('uses only the brand for empty or omitted titles', () => {
    expect(formatBrandTitle('')).toBe(BRAND_FULL_NAME);
    expect(formatBrandTitle()).toBe(BRAND_FULL_NAME);
  });
  it('uses only the brand when dynamic titles are disabled', () => {
    expect(formatBrandTitle('首页', false)).toBe(BRAND_FULL_NAME);
  });
});
