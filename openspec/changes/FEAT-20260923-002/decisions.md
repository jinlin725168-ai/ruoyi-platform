# Decisions for FEAT-20260923-002

## Idea

供应商列表按名称搜索时忽略输入的首尾空格，并且不区分大小写；搜索结果和导出都遵守这个规则

## Product revisions

- r1 (2026-09-23T11:36:38.388918Z): Q1 选推荐项：去掉半角空格、全角空格以及制表符、换行等所有空白字符

## Clarifications

- [FEAT-20260923-002] 名称条件里要去掉的“首尾空格”具体包括哪些字符？ → 去掉半角空格、全角空格以及制表符、换行等所有空白字符

## Answers to agent questions

- none

## Manual acceptance

- A21 (2026-09-23T12:43:24+00:00): 用户在本地环境核对后确认：供应商导出 Excel 含供应商分类列，空分类显示未分类；本次只改名称搜索匹配规则，导出列未变

## Resets

- none

## Smoke suite repairs

- none
