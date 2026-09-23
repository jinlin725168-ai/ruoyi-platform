# 可复用构件

## 后端

### 响应、分页与异常（ruoyi-common-core、ruoyi-common-mybatis）

- `R<T>`：
  - 成功：`R.ok()`、`R.ok(data)`、`R.ok(msg, data)`。
  - 失败：`R.fail(msg)`（500）、`R.fail(code, msg)`。
  - 警告：`R.warn(msg)`（601）。
  - 判断：`R.isSuccess(r)`。
- `PageResult<T>`：`PageResult.build(rows, total)`、`PageResult.build(list)`。
- `PageQuery`：`build()` 生成 MyBatis-Plus 的 `Page`，并处理 `orderByColumn`/`isAsc` 的驼峰转下划线和防注入；`getFirstNum()` 返回当前页起始行号。
- `BaseController`：`toAjax(int rows)`、`toAjax(boolean)`、`redirect(url)`。
- 异常：`ServiceException(msg)` 是可读的业务失败，可以用 `setCode` 指定 code；另有 `BaseException`、`UserException`。
- 常量：
  - `SystemConstants.NORMAL`、`SystemConstants.DISABLE`（对应 `sys_normal_disable`）、`SystemConstants.SUPER_ADMIN_ROLE_KEY`。
  - `HttpStatus` 各 code，`CacheNames`、`GlobalConstants`、`Constants`。
- 校验：
  - 分组 `AddGroup`、`EditGroup`、`QueryGroup`。
  - 注解 `@DictPattern`（值必须在某个字典里）、`@EnumPattern`、`@Xss`、`@JsonPattern`。
  - `ValidatorUtils.validate(obj, groups...)`。

### 数据访问（ruoyi-common-mybatis）

- `BaseEntity`：审计字段，自动填充。
- `BaseMapperPlus<T, V>`：见 `architecture.md`。常用方法：
  - 查询：`selectVoById`、`selectVoList(wrapper)`、`selectVoPage(page, wrapper)`、`exists(wrapper)`、`selectCount`。
  - 批量：`insertBatch`、`updateBatchById`。
  - 链式：`lambda().eq(...).voOne()` / `voList()`，`lambdaUpdate()`。
- `QueryBuilder`、`LambdaQueryBuilder`、`LambdaJoinQueryBuilder`、`AggregateLambdaQueryWrapper`：条件构造辅助，以及聚合查询。
- `@DataPermission` 加 `@DataColumn(key, value)`：写在 Mapper 方法上；`DataPermissionHelper` 可以临时忽略数据权限。
- `DataBaseHelper`：处理数据库方言差异，例如 `find_in_set`。
- `IdGeneratorUtil`：雪花 ID。

### 对象转换与工具（ruoyi-common-core）

- `MapstructUtils.convert(source, Target.class)`：转换单个对象或列表，依赖类上的 `@AutoMapper` 注解。它从 Spring 容器取 `Converter`，所以纯单元测试里不能直接触发。
- `StringUtils`：扩展了 hutool，提供 `isBlank`、`format`、`splitList`、`str2List`、`toUnderScoreCase`、`leftPad`、`matches` 等。
- `StreamUtils`：`toList`、`toMap`、`groupByKey`、`join`、`filter`。
- 其他：`DateUtils`、`ObjectUtils`、`TreeBuildUtils`、`SpringUtils`、`ServletUtils`、`MessageUtils.message(key, args)`（取 i18n 文案）、`RegexUtils`。

### 字典与跨模块服务

- `DictService`（core，由 `SysDictTypeServiceImpl` 实现）：
  - `getDictLabel(type, value)`、`getDictValue(type, label)`：值与标签互转。
  - `getAllDictByDictType(type)`：返回值到标签的 Map，带缓存，字典变更后同步。
  - `getDictType(type)`、`getDictData(type)`。
- `ruoyi-api` 系统接口：
  - `UserService`：`selectUserNameById`、`selectNicknameById`、`selectById`、`selectListByIds`、`selectUsersByRoleIds/DeptIds/PostIds`、`selectUserNicksByIds`。
  - `DeptService`：`selectDeptNameByIds`、`selectDeptLeaderById`、`selectDeptsByList`、`selectDeptNamesByIds`。
  - `RoleService.selectRoleNamesByIds`、`PostService.selectPostNamesByIds`。
  - `ConfigService`：`getConfigValue`、`getConfigBool/Int/Long/Decimal`、`getConfigObject`、`getConfigArray`。
  - `OssService`：`selectUrlByIds`、`selectByIds`。
  - `MessageService`：`sendMessage`、`publishMessage`、`publishAll`。
- `ruoyi-api` 工作流接口 `WorkflowService`：`startWorkFlow`、`completeTask`、`startCompleteTask`、`getBusinessStatus`、`deleteInstance`、`setVariable`、`instanceVariable`；另有流程事件 `ProcessEvent` 等，供业务监听。

### 横切注解

- `@Log(title, businessType = BusinessType.INSERT/UPDATE/DELETE/EXPORT/IMPORT/GRANT/...)`：记录操作日志。
- `@RepeatSubmit(interval, timeUnit, message)`：防重复提交，默认间隔 5 秒。
- `@RateLimiter(key, time, count, limitType)`：限流。
- `@Lock4j`：分布式锁。
- `@SaCheckPermission`、`@SaCheckRole`、`@SaIgnore`：鉴权。
- `@ApiEncrypt`：接口加密。
- `@EncryptField`：数据库字段加密。
- `@Sensitive(strategy = SensitiveStrategy.PHONE/ID_CARD/...)`：响应脱敏。
- `@Translation(type = TransConstant.USER_ID_TO_NAME/DICT_TYPE_TO_LABEL/..., mapper, other)`：响应字段翻译。

### 登录上下文（ruoyi-common-satoken）

`LoginHelper`：`getLoginUser()`、`getUserId()`、`getUsername()`、`getDeptId()`、`getDeptName()`、`isSuperAdmin()`、`isLogin()`。

### Excel（ruoyi-common-excel）

- 导出：`ExcelBuilder.of(list, Vo.class)`，可链式调用 `.sheetName(..)`、`.merge()`、`.options(dropDowns)`、`.includeFields(..)`、`.excludeFields(..)`、`.columnWidth(..)`、`.zip()`，最后 `.toResponse(response)` 或 `.toStream(out)`。
- 导入：`ExcelBuilder.read(inputStream, ImportVo.class)`，可链式调用 `.validate(true)`、`.listener(..)`，最后 `.doRead()`（返回 `ExcelResult`，含 `getList()` 和 `getAnalysis()`）或 `.doReadSync()`。
- 模板导出：`ExcelBuilder.template(path).data(..).toResponse(..)`。
- 注解与转换器：`@ExcelDictFormat(dictType | readConverterExp)` 配合 `ExcelDictConvert`，`@ExcelEnumFormat` 配合 `ExcelEnumConvert`，以及 `@CellMerge`、`@ExcelRequired`、`@ExcelNotation`。

### Redis 与缓存（ruoyi-common-redis）

- `RedisUtils`：
  - 对象：`setCacheObject`、`getCacheObject`、`deleteObject`、`setObjectIfAbsent`、`expire`。
  - 集合与 Map：`setCacheList`、`getCacheList`、`setCacheSet`、`setCacheMap`、`getCacheMapValue`。
  - 原子数：`incrAtomicValue`。
  - 发布订阅：`publish`、`subscribe`。
  - 限流：`rateLimiter`。
  - 客户端：`getClient()`。
- `CacheUtils`：`get`、`put`、`evict`、`clear`，按缓存名操作。
- `SequenceUtils`：`getNextId`、`getPaddedNextIdString`、`getDateId(prefix)`、`getDateTimeId`，基于 Redis 的流水号。采购单号没有用它，而是用数据库最大值加一，再靠唯一索引兜底重试。
- `QueueUtils`：普通队列、优先队列、阻塞队列。

### 业务模块内可参考的写法（org.dromara.biz）

- 哨兵查询值加字典有效性过滤：`BizSupplierServiceImpl.buildQueryWrapper`，用 `CATEGORY_NONE` 时追加 `isNull / eq '' / notIn(有效值)`。
- 服务端生成标签字段：`BizSupplierServiceImpl.fillCategoryLabel`。
- 按未删除行校验唯一性：`checkCodeUnique` 用 `mapper.exists(...)`，修改时排除自身。
- 主子表保存：先删除全部旧明细，再批量插入新明细（`saveDetails`、`removeDetails`），放在同一个事务里。
- 单号生成加冲突重试：`generateOrderNo`、`insertWithGeneratedOrderNo`，XML 里的 `selectMaxOrderNoByPrefix`。
- 状态守卫：`loadDraft(id, action)`。
- 金额计算：`BigDecimal` 保留 2 位，`RoundingMode.HALF_UP`。
- 选项接口：`GET /biz/purchaseOrder/supplierOptions` 复用 `IBizSupplierService.queryList`。

## 前端

### 请求与类型

- `@/utils/request`：
  - 默认导出 axios 实例 `request({ url, method, params | data })`。
  - `download(url, params, fileName)`：导出文件。
  - `globalHeaders()`：返回 Authorization 和 clientid 请求头，给上传组件用。
  - `isHandledRequestError(err)`、`extractErrorMessage`。
- `@/utils/api-types`：`AxiosPromise<T>`，即 `Promise<{code,msg,data:T}>`。
- `@/api/types`：`PageResult<T>`、`LoginData`、`VerifyCodeResult`。
- 全局类型（`src/types/global.d.ts`，不需要 import）：`PageData<Form, Query>`、`PageQuery`、`BaseEntity`、`DictDataOption`、`DialogOption`、`FieldOption`、`UploadOption`、`ImportOption`，以及 Element 组件实例类型（如 `ElFormInstance`，见 `types/element.d.ts`）。

### 组合函数（`src/hooks`）

| hook | 返回值与用途 |
|---|---|
| `useLoading(initial)` | `loading`、`withLoading(fn)` |
| `useSearchToggle()` | `showSearch`，配合 `right-toolbar` 使用 |
| `useTableSelection(row => row.id)` | `ids`、`single`、`multiple`、`handleSelectionChange` |
| `useFormDialog({ form, formRef, initialFormData })` | `dialog`、`resetForm`、`openDialog(title)`、`showDialog(title)`、`closeDialog` |
| `useDialogState(title)` | 轻量的弹窗状态 |
| `useSearchReset({ queryFormRef, queryParams, pageNumKey, pageSizeKey, initialPageSize, afterReset })` | `resetQuery` |
| `useDateRangeQuery(propName)` | `dateRange`、`applyDateRange(query)`（写入 `params[begin<Prop>]` 和 `params[end<Prop>]`）、`resetDateRange` |
| `useTableSortQuery(queryParams, ...)` | 表头排序映射到 `orderByColumn` 和 `isAsc` |
| `useFullHeightTable()` | 表格高度自适应 |
| `useTreeTableExpand`、`useTreeCollapsed` | 树表展开与折叠 |

### 工具、插件、指令、组件

- **工具**：
  - `@/utils/dict` 的 `useDict(...types)`：返回响应式对象，键为字典类型，值为 `DictDataOption[]`（`label/value/elTagType/elTagClass`），有缓存，并合并并发请求。
  - `@/utils/ruoyi`：`parseTime`、`addDateRange`、`selectDictLabel(s)`、`handleTree`、`tansParams`、`blobValidate`。
  - `@/utils/validate`：`isHttp`、`isPathMatch`、`isEmail` 等。
  - `@/utils/permission`：`checkPermi`、`checkRole`。
  - `@/utils/auth`：`getToken`、`setToken`、`removeToken`。
- **插件**（也可以通过 `proxy.$modal` 等访问）：
  - `modal`：`msg`、`msgSuccess`、`msgError`、`msgWarning`、`confirm`、`prompt`、`loading`、`closeLoading`、`notify*`。
  - `tab`：`openPage`、`closePage`、`refreshPage`。
  - `cache`：`session`、`local`。
  - `download`：`oss`、`zip`。
  - `auth`：`hasPermi`、`hasRole`。
- **指令**：`v-hasPermi="['biz:x:add']"`、`v-hasRoles`、`v-copyText`。
- **全局组件**（自动注册）：`Pagination`（`v-model:page`、`v-model:limit`、`@pagination`）、`RightToolbar`（`v-model:show-search`、`@query-table`）、`DictTag`（`:options`、`:value`）、`FileUpload`、`ImageUpload`、`ImagePreview`、`Editor`、`UserSelect`、`RoleSelect`、`IconSelect`、`TreePanel`、`SvgIcon`、`Process`（工作流）、`Breadcrumb`、`ParentView`、`iFrame`。
- **样式**：`@/assets/styles/components/page-shell` 的 mixin `table-crud-page`，用于业务列表页的统一外观。

## 验收与冒烟工具（acceptance/tools，底座）

- **`ruoyi_client.py`**（只用标准库）：
  - `Client(base_url=SMOKE_BASE_URL, client_id=SMOKE_CLIENT_ID 或默认值)`。
  - `login(username, password)`：默认参数就是默认管理员账号；登录体里多带的 `tenantId` 会被后端忽略。
  - `get(path, params, expect=200)`、`post(path, body, expect)`、`put(...)`、`delete(path, expect)`、`request(method, path, body, params, expect)`。
  - 断言规则：HTTP 状态不是 200，或 `code` 不等于 `expect`，都抛 `ApiError`（带 `status`、`body`、`path`）。`expect=None` 表示不校验 code，适合断言失败场景。
- **`smoke_harness.py`**：`sync_scratch`、`visible_files`、`split_cases`、`run_python_cases`（按路径加载 unittest，0 个用例也算失败）、`free_port`、`wait_http`、`stop`、`env_error`。
- **`ruoyi_smoke.py`**：`Stack` 类负责 `build()`、`start_backend()`、`start_frontend()`、`stop()`，可以复用，`ui_regression.py` 就复用了它；`run_playwright`；内部的 `_Mysql` 通过 `docker exec` 操作 MySQL 容器。
- **`playwright.config.ts`**：`testDir` 为 `acceptance/`，`workers` 为 1，超时 60 秒，只有 chromium 项目，headless；`baseURL` 取 `SMOKE_UI_URL`，输出目录取 `SMOKE_OUTPUT_DIR`。
- **`selftest_backend.py`、`selftest_ui.spec.ts`**：执行器自检，覆盖登录、`/system/user/getInfo` 和未登录返回 401；UI 自检覆盖登录页到 `/index`。
- **`ui_regression.py`**：配合 `playwright-agents/`（planner、generator、healer 三个代理的提示和工具清单，以及 `mcp.json`），对着冒烟栈生成 `acceptance/ui/<capability>/` 下的回归资产。
- **已验证的 UI 定位器和文案**：`acceptance/ui/supplier-management/plan.md` 和其中的 `*.spec.ts`，覆盖菜单进入、按名称查询、直接访问、未授权访问等。
