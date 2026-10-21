/** 工作台完整品牌名称。 */
export const BRAND_FULL_NAME = '红魔业务工作台';
/** 适用于侧栏等紧凑位置的品牌名称。 */
export const BRAND_SHORT_NAME = '红魔';

/** 根据页面名称和动态标题开关生成浏览器标题。 */
export function formatBrandTitle(pageTitle = '', dynamicTitle = true): string {
  return dynamicTitle && pageTitle ? `${pageTitle} - ${BRAND_FULL_NAME}` : BRAND_FULL_NAME;
}
