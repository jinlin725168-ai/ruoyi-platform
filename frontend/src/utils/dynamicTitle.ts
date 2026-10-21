import { formatBrandTitle } from '@/constants/brand';
import { useSettingsStore } from '@/store/modules/settings';

/** 根据当前页面与设置更新浏览器标题。 */
export const useDynamicTitle = () => {
  const settingsStore = useSettingsStore();
  document.title = formatBrandTitle(settingsStore.title, settingsStore.dynamicTitle);
};
