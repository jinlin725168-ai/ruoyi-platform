# 可复用积木

对应底座版本：1.0.19，生成日期：2026-09-28

## 一、后端

| 名字 | 路径（模块 / 类） | 用途 | 典型调用 |
|---|---|---|---|
| `R<T>` | common-core `org.dromara.common.core.domain.R` | 统一返回 | `R.ok(data)`、`R.fail(msg)`、`R.warn(msg)` |
| `PageResult<T>` | common-core `...core.domain.PageResult` | 分页结果 `{rows,total}` | `PageResult.build(page.getRecords(), page.getTotal())` |
| `PageQuery` | common-mybatis `...mybatis.core.page.PageQuery` | 分页和排序参数，带防注入 | `mapper.selectVoPage(pageQuery.build(), lqw)` |
| `BaseController` | common-web `...web.core.BaseController` | 控制器基类 | `toAjax(service.insertByBo(bo))` |
| `BaseEntity` | common-mybatis | 审计字段自动填充 | 实体 `extends BaseEntity` |
| `BaseMapperPlus<T,V>` | common-mybatis | VO 查询、批量操作、链式查询 | `selectVoById`、`selectVoList(w)`、`insertBatch(list)`、`exists(w)`、`lambda().eq(..).voOne()` |
| `ServiceException` | common-core `...core.exception.ServiceException` | 可读的业务失败（code 500） | `throw new ServiceException("采购单不存在或已被删除")` |
| 校验分组与注解 | common-core `...core.validate.*`、`@DictPattern` | 新增、修改分组校验；字典值校验 | `@NotBlank(groups = {AddGroup.class, EditGroup.class})` |
| `MapstructUtils` | common-core `...core.utils.MapstructUtils` | BO、实体、VO 互转（基于 `@AutoMapper`） | `MapstructUtils.convert(bo, BizX.class)` |
| `StringUtils` / `StreamUtils` | common-core | 字符串与集合工具（hutool 扩展） | `StringUtils.trim/isNotEmpty/defaultString/leftPad`、`StreamUtils.toList` |
| `SystemConstants` | common-core | `NORMAL`、`DISABLE`、超级管理员角色 key | `SystemConstants.NORMAL.equals(status)` |
| `DictService` | common-core 接口，实现在 `SysDictTypeServiceImpl` | 字典值与标签互转，带缓存 | `dictService.getAllDictByDictType(type)`、`getDictLabel(type, value)` |
| `ruoyi-api` 系统接口 | `org.dromara.system.api.*` | 跨模块获取用户、部门、角色、岗位、参数、OSS、消息 | `userService.selectNicknameById(id)`、`configService.getConfigValue(key)`、`messageService.publishMessage(..)` |
| `WorkflowService` | `org.dromara.workflow.api.WorkflowService` | 发起和办理流程 | `startWorkFlow`、`completeTask`、`getBusinessStatus` |
| `LoginHelper` | common-satoken | 当前登录人信息 | `LoginHelper.getUserId()`、`getDeptId()`、`isSuperAdmin()` |
| `@Log` / `BusinessType` | common-log | 操作日志 | `@Log(title = "供应商管理", businessType = BusinessType.INSERT)` |
| `@RepeatSubmit` / `@RateLimiter` / `@Lock4j` | common-redis、lock4j | 防重复提交、限流、分布式锁 | 写在控制器写接口上 |
| `ExcelBuilder` 及注解 | common-excel `...excel.utils.ExcelBuilder` | 导出、导入、模板导出；字典列转换 | `ExcelBuilder.of(list, Vo.class).sheetName("供应商").toResponse(response)`；`@ExcelDictFormat` 配合 `ExcelDictConvert` |
| `RedisUtils` / `CacheUtils` / `SequenceUtils` / `QueueUtils` | common-redis | 手工缓存、按缓存名读写、流水号、队列 | `RedisUtils.setCacheObject(k, v)`、`CacheUtils.evict(name, key)` |
| `@Translation` / `@Sensitive` / `@EncryptField` | common-translation、sensitive、encrypt | 响应字段翻译、脱敏、库字段加密 | `@Translation(type = TransConstant.USER_ID_TO_NAME)` |
| `@DataPermission` / `DataPermissionHelper` | common-mybatis | 按角色数据范围过滤 | 写在 Mapper 方法上（示例 `TestDemoMapper`） |
| 业务内可参考的写法 | `org.dromara.biz.*` | 哨兵值查询、服务端填充标签、按未删除行校验唯一、主子表整体替换、单号生成加冲突重试、状态守卫、去空白且忽略大小写的模糊查询 | `BizSupplierServiceImpl.buildQueryWrapper/fillCategoryLabel/checkCodeUnique`；`BizPurchaseOrderServiceImpl.insertWithGeneratedOrderNo/loadDraft/saveDetails` |

## 二、前端

| 名字 | 路径 | 用途 | 典型调用 |
|---|---|---|---|
| `request` / `download` | `src/utils/request.ts` | axios 实例（token、clientid、错误提示）；文件导出 | `request({ url: '/biz/supplier/list', method: 'get', params })`；`download('biz/supplier/export', {...q}, 'x.xlsx')` |
| `AxiosPromise` / `PageResult` | `src/utils/api-types`、`src/api/types.ts` | 返回类型 | `AxiosPromise<PageResult<SupplierVO>>` |
| 全局类型 | `src/types/global.d.ts` | `PageQuery`、`BaseEntity`、`DictDataOption`、`DialogOption`，不需要 import | `interface XQuery extends PageQuery` |
| `useDict` | `src/utils/dict.ts` | 字典选项，带缓存 | `const { sys_normal_disable } = toRefs<any>(useDict('sys_normal_disable'))` |
| `useLoading` | `src/hooks/async/useLoading` | loading 状态 | `const { loading, withLoading } = useLoading()` |
| `useFormDialog` / `useDialogState` | `src/hooks/dialog/*` | 弹窗与表单重置 | `openDialog('新增')` |
| `useSearchReset` / `useSearchToggle` / `useDateRangeQuery` | `src/hooks/form/*` | 查询重置、显隐、日期区间（写入 `params[begin<Prop>]`、`params[end<Prop>]`） | `useDateRangeQuery('OrderDate')` |
| `useTableSelection` / `useTableSortQuery` / `useFullHeightTable` | `src/hooks/table/*` | 多选、排序参数、表格高度 | `useTableSelection(row => row.supplierId)` |
| `modal` 等插件 | `src/plugins/*`（也可通过 `proxy.$modal` 访问） | 提示、确认、标签页、缓存、下载 | `modal.msgSuccess('新增成功')`、`modal.confirm(..)` |
| 指令 | `src/directive/*` | 按钮权限 | `v-hasPermi="['biz:supplier:add']"` |
| 全局组件 | `src/components/*`（自动注册） | `Pagination`、`RightToolbar`、`DictTag`、`FileUpload`、`ImageUpload`、`Editor`、`UserSelect` 等 | `<pagination v-model:page=.. v-model:limit=.. @pagination=getList />` |
| 页面样式 | `src/assets/styles/components/page-shell` | 列表页统一外观 | `@include pageShell.table-crud-page;` |
| 工具函数 | `src/utils/ruoyi.ts`、`validate.ts`、`permission.ts` | `parseTime`、`addDateRange`、`handleTree`、`checkPermi` | `parseTime(row.createTime)` |

## 三、验收

| 名字 | 路径 | 用途 | 典型调用 |
|---|---|---|---|
| `ruoyi_client.Client` | `acceptance/tools/ruoyi_client.py`（只用标准库） | 后端用例的 HTTP 客户端；`code` 不等于 `expect` 时抛 `ApiError`（带 `status`、`body`、`path`） | `c = Client(); c.login(); c.get('/biz/supplier/list', params={..})`；`c.post(path, body, expect=None)` 用于断言失败场景 |
| `ruoyi_smoke.py` / `Stack` | `acceptance/tools/ruoyi_smoke.py` | 构建、建临时库、启动后端和 vite、运行 unittest 与 Playwright；退出码 0/1/2 | `python3 acceptance/tools/ruoyi_smoke.py <suite>/test_x.py <suite>/x.spec.ts` |
| `smoke_harness` | `acceptance/tools/smoke_harness.py` | `sync_scratch`、`run_python_cases`、`free_port`、`wait_http`、`env_error` | 被各执行器 import |
| `run_manifest.py` | `acceptance/tools/run_manifest.py` | 不依赖引擎，按顺序执行一份 manifest 的全部命令（CI 用） | `python3 acceptance/tools/run_manifest.py acceptance/smoke/manifest.json` |
| `frontend_unit.py` | `acceptance/tools/frontend_unit.py` | 同步到 scratch 后运行 `vitest run --passWithNoTests` | 单元层自动运行；CI 用 `--in-place` |
| `frontend_check.py` | `acceptance/tools/frontend_check.py` | 同步到 scratch 后运行 oxlint 和 vue-tsc，只有业务文件的类型错误才判失败 | 检查层自动运行；CI 用 `--in-place` |
| `playwright.config.ts` | `acceptance/tools/playwright.config.ts` | 单 worker、chromium、headless；`baseURL` 取 `SMOKE_UI_URL` | 由执行器传入 `-c` |
| UI 回归资产 | `acceptance/ui/supplier-management/`（`plan.md` 和 4 个 spec） | 已验证的定位器和文案，写浏览器用例时复用 | 复制其中的登录、菜单进入写法 |
| 已有验收套件 | `acceptance/changes/<id>/`、`acceptance/smoke/purchase-order/` | 数据准备、权限用户构造、直接改临时库等写法 | 参考 `test_purchase_order_category.py` |
| self-test | `acceptance/tools/selftest_backend.py`、`selftest_ui.spec.ts`、`tools/tests/test_frontend_unit.py` | 执行器自检 | `python3 acceptance/tools/ruoyi_smoke.py acceptance/tools/selftest_backend.py` |
| `ui_regression.py` | `acceptance/tools/ui_regression.py` 加 `playwright-agents/` | 用 planner、generator、healer 代理生成 UI 回归资产 | 由 `.storyloop` 的 ui_regression 配置调用 |

## 四、什么时候不该自己写

1. **分页**：用 `PageQuery.build()` 加 `selectVoPage` 加 `PageResult.build`，不要手写 limit/offset，也不要自定义分页返回结构。
2. **字典查询与翻译**：后端用 `DictService`，前端用 `useDict` 加 `DictTag`，导出用 `@ExcelDictFormat`；不要自己查 `sys_dict_data` 表或写死标签。
3. **Excel 导出和导入**：用 `ExcelBuilder`，不要直接调用 POI 或 Fesod。
4. **文件上传**：用 `OssService`（ruoyi-api）和前端 `FileUpload`、`ImageUpload`，不要自己写本地文件存储。
5. **审计字段和主键**：交给 `BaseEntity`、`InjectionMetaObjectHandler` 和雪花 ID，不要手动 set `createBy`、`createTime` 或生成 ID。
6. **登录人、部门、用户名**：用 `LoginHelper` 和 `UserService`、`DeptService`，不要解析 token，也不要查 `sys_user`。
7. **权限判断**：用 `@SaCheckPermission` 和 `v-hasPermi`，不要在代码里比较角色名。
8. **操作日志、防重复提交、限流**：用 `@Log`、`@RepeatSubmit`、`@RateLimiter`，不要自己写日志表或 Redis 键。
9. **对象转换**：用 `@AutoMapper` 加 `MapstructUtils.convert`，不要逐字段手工拷贝（导出用的 VO 除外）。
10. **前端请求、弹窗、表格多选、查询重置**：用 `@/utils/request`、`modal`、`useTableSelection`、`useSearchReset` 等 hooks，不要新建 axios 实例。
11. **验收 HTTP 调用**：用 `ruoyi_client.Client`，不要在用例里手写 urllib 登录和 token 处理。
