# Decisions for FEAT-20260924-001

## Idea

供应商列表按编码搜索时，同样忽略输入的首尾空白并且不区分大小写，与名称搜索保持一致；导出遵守同样规则

## Product revisions

- r1 (2026-09-24T09:20:58.286206Z): Q1 选推荐项：模糊匹配，编码包含输入内容即命中，与名称条件相同

## Clarifications

- [FEAT-20260924-001] 编码查询条件采用哪种匹配方式？ → 模糊匹配：编码包含输入内容即命中，与名称条件相同

## Answers to agent questions

- none

## Manual acceptance

- none

## Resets

- none

## Smoke suite repairs

- none
