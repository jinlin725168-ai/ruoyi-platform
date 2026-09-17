# ruoyi-platform

用 RuoYi-Vue-Plus 作为底座，验证 StoryLoop 通用迭代闭环的单仓库工程。

## 目录与边界

| 目录 | 来源 | 分层 | 说明 |
|---|---|---|---|
| `backend/` | git subtree `RuoYi-Vue-Plus` 分支 `6.X` | 底座 + 可变区 | `ruoyi-modules/` 为可变区，其余为底座 |
| `frontend/` | git subtree `plus-ui` 分支 `6.X-Vue` | 底座 + 可变区 | `src/`、`public/` 为可变区，配置与 `.env.*` 为底座 |
| `sql/biz/` | 本仓库 | 可变区 | 每个变更的增量 DDL 和菜单 SQL |
| `infra/` | 本仓库 | 底座 | 本地 MySQL(3307)/Redis(6380) 容器 |
| `acceptance/` | 本仓库 | 底座 | StoryLoop 设置与冒烟执行器 |

可变区（`module_roots`）：`backend/ruoyi-modules`、`frontend/src`、`frontend/public`、`sql/biz`。
可变区内的文件随用户故事迭代自由修改；可变区之外的一切改动都走 StoryLoop 的 BASE 迭代。
集成点（各级 `pom.xml`、`package.json`、`pnpm-lock.yaml`）始终属于底座。

新业务功能统一落在 `backend/ruoyi-modules/ruoyi-biz`（包 `org.dromara.biz`）、
`frontend/src/views/biz`、`frontend/src/api/biz` 和 `sql/biz`。

## 上游同步

```bash
git subtree pull --prefix=backend  /home/jinlin/work/RuoYi/RuoYi-Vue-Plus 6.X     --squash
git subtree pull --prefix=frontend /home/jinlin/work/RuoYi/plus-ui         6.X-Vue --squash
```

上游同步会修改底座文件，因此在 StoryLoop 初始化之后必须作为一次 BASE 迭代执行。

## 本地环境

```bash
docker compose -f infra/docker-compose.yml up -d
```

`backend/ruoyi-admin/src/main/resources/application-dev.yml` 已指向 3307/6380。
