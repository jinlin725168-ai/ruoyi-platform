<template>
  <section class="login-brand">
    <span class="brand-pill">{{ BRAND_SHORT_NAME }}</span>
    <h1 class="brand-title">{{ BRAND_FULL_NAME }}</h1>
    <p class="brand-desc">集中处理供应商管理与采购单管理，使用现有账号和权限开展日常工作。</p>
    <div class="brand-highlights">
      <span v-for="item in highlights" :key="item" class="highlight-chip">{{ item }}</span>
    </div>
    <div class="brand-metrics">
      <article v-for="item in capabilities" :key="item.label" class="metric-card">
        <strong>{{ item.value }}</strong>
        <span>{{ item.label }}</span>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { BRAND_FULL_NAME, BRAND_SHORT_NAME } from '@/constants/brand';
const highlights = ['供应商管理', '采购单管理', '动态菜单', '深浅色主题'];
const capabilities = [
  { label: '供应商档案', value: '维护与查询' },
  { label: '采购单流程', value: '草稿与提交' },
  { label: '业务数据', value: '详情与导出' }
];
</script>

<style scoped lang="scss">
.login-brand {
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: 0 30px 80px rgba(2, 8, 23, 0.32);
  backdrop-filter: blur(18px);
}

.login-brand {
  padding: 42px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #eef4ff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02)),
    linear-gradient(135deg, rgba(53, 109, 255, 0.32), rgba(15, 23, 42, 0.24));
}

.brand-pill {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.brand-title {
  margin: 22px 0 14px;
  font-size: clamp(34px, 4vw, 52px);
  line-height: 1.08;
  letter-spacing: -0.03em;
}

.brand-desc {
  margin: 0;
  max-width: 580px;
  color: rgba(226, 232, 240, 0.88);
  font-size: 15px;
  line-height: 1.8;
}

.brand-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 28px 0 34px;
}

.highlight-chip {
  padding: 9px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #f8fbff;
  font-size: 13px;
}

.brand-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  padding: 18px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 6px;

  strong {
    font-size: 24px;
    color: #fff;
  }

  span {
    color: rgba(226, 232, 240, 0.72);
    font-size: 13px;
  }
}

@media (max-width: 960px) {
  .login-brand {
    padding: 28px 24px;
  }
  .brand-metrics {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .login-brand {
    display: none;
  }
}
</style>
