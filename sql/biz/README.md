# sql/biz

每个 StoryLoop 变更的增量 SQL（建表 DDL + 菜单 sys_menu 插入）放在此目录，文件名 `<change-id>.sql`。
基础全量脚本在 `backend/script/sql/`（底座，不在此目录重复）。冒烟执行器会在临时库上先导入基础脚本，再按文件名顺序导入此目录。
