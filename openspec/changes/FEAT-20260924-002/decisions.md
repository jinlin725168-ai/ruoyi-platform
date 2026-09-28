# Decisions for FEAT-20260924-002

## Idea

采购单列表可以按供应商名称模糊搜索（忽略首尾空白、不区分大小写），导出遵守同样的筛选

## Product revisions

- r1 (2026-09-24T10:43:33.577527Z): Q1 选推荐项：用采购单上记录的供应商名称（列表和导出中显示的名称）匹配

## Clarifications

- [2026-09-24] 按供应商名称搜索采购单时，应该用哪个名称来匹配？ → 采购单上记录的供应商名称（即列表和导出中显示的名称）

## Answers to agent questions

- none

## Manual acceptance

- A27 (2026-09-28T01:27:08+00:00): 用户在本地环境核对后确认：采购单导出 Excel 列标题为中文且含供应商分类，状态显示草稿/已提交，每单一行带合计金额，按供应商名称筛选后数据行与页面一致；本次未改导出列

## Resets

- none

## Smoke suite repairs

- none
