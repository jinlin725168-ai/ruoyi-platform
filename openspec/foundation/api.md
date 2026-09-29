# 接口清单

对应底座版本：1.0.19，生成日期：2026-09-28

## 一、约定

- **前缀**：后端没有全局 context-path，控制器的 `@RequestMapping` 就是完整路径。前端通过 `VITE_APP_BASE_API` 前缀走 vite 代理，代理会去掉该前缀。
- **认证**：除 `@SaIgnore` 和 `security.excludes` 外，所有接口都要求登录，并同时带 `Authorization: Bearer <token>` 和 `clientid` 两个请求头。
- **返回结构**：`R<T>` 即 `{code, msg, data}`。分页接口的 `data` 为 `PageResult`，即 `{rows, total}`。
- **业务码**：200 成功；401 未登录；403 无权限；500 业务失败或校验失败（msg 可读）；409 唯一键冲突；400 请求体格式错误；404、405；503 获取锁失败；601 警告。HTTP 状态恒为 200。
- **分页参数**：`pageNum`、`pageSize`、`orderByColumn`、`isAsc`。
- **导出**：`POST .../export`，参数用表单编码，响应为 xlsx 二进制。
- **权限串格式**：`<模块>:<功能>:<动作>`，例如 `biz:supplier:list`。超级管理员拥有 `*:*:*`。「登录即可」表示只需登录、没有权限注解。

## 二、按模块的接口

### ruoyi-biz · 供应商 `/biz/supplier`（实现类 `org.dromara.biz.supplier.controller.BizSupplierController`）

| 方法 路径 | 用途 | 权限串 |
|---|---|---|
| GET `/biz/supplier/list` | 分页查询。参数：`supplierCode`、`supplierName`（都去首尾空白、不区分大小写、模糊匹配）、`status`、`supplierCategory`（字典值，或 `__none__` 表示未分类）；每行带 `supplierCategoryLabel` | `biz:supplier:list` |
| POST `/biz/supplier/export` | 按列表条件导出，不分页 | `biz:supplier:export` |
| GET `/biz/supplier/{supplierId}` | 详情；已删除的记录返回 data 为空 | `biz:supplier:query` |
| POST `/biz/supplier` | 新增；编码重复或分类无效时返回 500 和可读提示（`R.fail`） | `biz:supplier:add` |
| PUT `/biz/supplier` | 修改；编码不可改，提交的编码会被忽略；分类会重新校验 | `biz:supplier:edit` |
| DELETE `/biz/supplier/{supplierIds}` | 逻辑删除，多个 ID 用逗号分隔 | `biz:supplier:remove` |

### ruoyi-biz · 采购单 `/biz/purchaseOrder`（实现类 `org.dromara.biz.purchase.controller.BizPurchaseOrderController`）

| 方法 路径 | 用途 | 权限串 |
|---|---|---|
| GET `/biz/purchaseOrder/list` | 分页查询。参数：`orderNo`（模糊）、`supplierId`、`supplierName`（去首尾空白、不区分大小写、模糊）、`supplierCategory`（含 `__none__`）、`status`、`params[beginOrderDate]`、`params[endOrderDate]`；每行带 `supplierCategoryLabel` 和 `remark` | `biz:purchaseOrder:list` |
| GET `/biz/purchaseOrder/supplierOptions` | 启用状态的供应商下拉选项 | `biz:purchaseOrder:list` |
| POST `/biz/purchaseOrder/export` | 只导出主表，含供应商分类和备注列 | `biz:purchaseOrder:export` |
| GET `/biz/purchaseOrder/{orderId}` | 详情，含 `details`；不存在时返回 500 | `biz:purchaseOrder:query` |
| POST `/biz/purchaseOrder` | 新增；单号、金额、状态由系统计算；remark 可选，最多 500 字符 | `biz:purchaseOrder:add` |
| PUT `/biz/purchaseOrder` | 修改草稿；明细以本次提交为准；备注以本次提交为准，未填写时清空 | `biz:purchaseOrder:edit` |
| PUT `/biz/purchaseOrder/submit/{orderId}` | 草稿变为已提交 | `biz:purchaseOrder:submit` |
| DELETE `/biz/purchaseOrder/{orderIds}` | 只能删除草稿，明细一并删除 | `biz:purchaseOrder:remove` |

### ruoyi-admin · 认证（实现类 `org.dromara.web.controller.AuthController`、`CaptchaController`、`IndexController`）

| 方法 路径 | 用途 | 权限 |
|---|---|---|
| POST `/auth/login` | 登录，请求体含 `clientId`、`grantType`、`username`、`password`、`code`、`uuid`；带 `@ApiEncrypt`，smoke 运行档关闭加密 | 免登录 |
| POST `/auth/register` | 注册，需要系统参数开启注册 | 免登录 |
| POST `/auth/logout` | 退出 | 免登录（类上 `@SaIgnore`） |
| GET `/auth/binding/{source}`、POST `/auth/social/callback`、DELETE `/auth/unlock/{socialId}` | 第三方账号绑定、回调、解绑 | 同上 |
| GET `/auth/code` | 图形验证码 | 免登录 |
| GET `/resource/sms/code`、`/resource/email/code` | 短信、邮箱验证码 | 免登录 |
| GET `/` | 首页提示 | 免登录 |

## 三、上游系统能力

| 路由前缀 | 实现类 | 主要接口与权限串 |
|---|---|---|
| `/system/user` | `SysUserController` | `GET /list` `system:user:list`；`POST /export` `:export`；`POST /importData` `:import`；`GET /getInfo` 登录即可；`GET /{userId}` `:query`；POST、PUT、`DELETE /{userIds}` `:add/:edit/:remove`；`PUT /resetPwd` `:resetPwd`；`PUT /changeStatus`、`PUT /authRole` `:edit`；`GET /deptTree` `:list` |
| `/system/user/profile` | `SysProfileController` | 个人信息与改密，登录即可 |
| `/system/role` | `SysRoleController` | `system:role:list/export/query/add/edit/remove`；`/authUser/*` 分配用户；`/deptTree/{roleId}` |
| `/system/menu` | `SysMenuController` | `GET /getRouters` 登录即可；`system:menu:list/query`；增、改、删还要求超级管理员角色 |
| `/system/dept` | `SysDeptController` | `system:dept:list/query/add/edit/remove` |
| `/system/post` | `SysPostController` | `system:post:list/export/query/add/edit/remove` |
| `/system/dict/type` | `SysDictTypeController` | `system:dict:list/export/query/add/edit/remove`；`DELETE /refreshCache` |
| `/system/dict/data` | `SysDictDataController` | `GET /type/{dictType}` 登录即可（前端 `useDict` 调用）；`system:dict:*` |
| `/system/config` | `SysConfigController` | `GET /configKey/{configKey}` 登录即可；`system:config:*` |
| `/system/notice` | `SysNoticeController` | `system:notice:list/query/add/edit/remove` |
| `/system/client` | `SysClientController` | `system:client:*` |
| `/system/social` | `SysSocialController` | `GET /list` 登录即可 |
| `/resource/oss` | `SysOssController` | `system:oss:list/query/upload/download/remove` |
| `/resource/oss/config` | `SysOssConfigController` | `system:ossConfig:list/add/edit/remove` |
| `/resource/message` | `SysMessageController` | 站内消息盒，登录即可 |
| `/monitor/operlog` | `SysOperlogController` | `monitor:operlog:list/export/remove` |
| `/monitor/loginInfo` | `SysLoginInfoController` | `monitor:logininfo:list/export/remove/unlock` |
| `/monitor/online` | `SysUserOnlineController` | `monitor:online:list/forceLogout` |
| `/monitor/cache` | `CacheController` | `monitor:cache:list` |
| `/workflow/category` | `FlwCategoryController` | `workflow:category:*` |
| `/workflow/definition` | `FlwDefinitionController` | `workflow:definition:list/query/add/edit/publish/remove/copy/import/export/active` |
| `/workflow/instance` | `FlwInstanceController` | `workflow:instance:list/query/remove/cancel/active/currentList/variableQuery/variable/invalid` |
| `/workflow/task` | `FlwTaskController` | 办理类接口登录即可；`workflow:task:list/edit` |
| `/workflow/spel` | `FlwSpelController` | `workflow:spel:*` |
| `/workflow/leave` | `TestLeaveController` | 请假示例，`workflow:leave:*` |
| `/tool/gen` | `GenController` | `tool:gen:list/query/import/edit/remove/preview/code` |
| `/demo/demo`、`/demo/tree` | `TestDemoController`、`TestTreeController` | `demo:demo:*`、`demo:tree:*`（上游演示，不要在业务中依赖） |
| `/demo/*` 其他、`/es`、`/swagger/demo` | `ruoyi-demo` 下的各 Controller | 演示用途 |
| `/snail-ai` | `SnailAiController` | Snail AI 用户注册 |
| `{message.path}` | `ruoyi-common-push` 的 `SseController` | SSE 推送；smoke 运行档关闭 |

Warm-Flow 设计器接口（`/warm-flow/**`）由 Warm-Flow 插件提供。

**业务菜单与页面对照**：

| 菜单 | menu_id | path / component | 前端 URL |
|---|---|---|---|
| 业务管理（M） | 1770000000000000000 | `biz` | 目录 |
| 供应商管理（C） | 1770000000000000001 | `supplier` / `biz/supplier/index` | `/biz/supplier` |
| 采购单管理（C） | 1770000000000000010 | `purchaseOrder` / `biz/purchaseOrder/index` | `/biz/purchaseOrder` |

## 四、前端 api 封装

- **目录**：`frontend/src/api/<module>/<feature>/index.ts` 放请求函数，`types.ts` 放类型。上游模块有 `api/system/**`、`api/monitor/**`、`api/workflow/**`、`api/tool/**`；公共的有 `api/login.ts`、`api/menu.ts`、`api/types.ts`。
- **命名**：`list<X>`、`get<X>`、`add<X>`、`update<X>`、`del<X>`，自定义动作如 `submitPurchaseOrder`、`listPurchaseOrderSuppliers`；类型为 `<X>VO`、`<X>Form`、`<X>Query`。
- **业务现有**：
  - `api/biz/supplier`：`listSupplier`、`getSupplier`、`addSupplier`、`updateSupplier`、`delSupplier`；常量 `SUPPLIER_CATEGORY_NONE`。
  - `api/biz/purchaseOrder`：`listPurchaseOrder`、`listPurchaseOrderSuppliers`、`getPurchaseOrder`、`addPurchaseOrder`、`updatePurchaseOrder`、`submitPurchaseOrder`、`delPurchaseOrder`。
- **导出**：不写在 api 文件里，由页面直接调用 `@/utils/request` 的 `download('biz/<feature>/export', params, fileName)`。
