# API 路由与权限

## 通用约定

- 除 `@SaIgnore` 的类或方法、`security.excludes` 里的路径外，所有接口都要求登录，并同时带上 `Authorization: Bearer <token>` 和 `clientid` 两个请求头。
- 响应统一为 `R`，即 `{code, msg, data}`。分页接口的 `data` 是 `{rows, total}`。
- 通用分页参数：`pageNum`、`pageSize`、`orderByColumn`、`isAsc`。
- 导出接口都是 `POST .../export`，参数用表单编码，响应为 xlsx 二进制。
- 下文“登录即可”指只需登录、没有权限注解。

## ruoyi-admin（认证与公共）

| 方法 | 路径 | 权限与说明 |
|---|---|---|
| POST | `/auth/login` | 免登录，`@ApiEncrypt`（smoke 运行档关闭加密）。请求体：`clientId`、`grantType`、`username`、`password`、`code`、`uuid`。返回 `access_token`、`expire_in`、`client_id` |
| POST | `/auth/register` | 免登录，`@ApiEncrypt`，需要系统参数开启注册 |
| POST | `/auth/logout` | 退出登录 |
| GET | `/auth/binding/{source}` | 获取第三方绑定跳转地址 |
| POST | `/auth/social/callback` | 第三方登录回调 |
| DELETE | `/auth/unlock/{socialId}` | 解绑第三方账号 |
| GET | `/auth/code` | 免登录，图形验证码（返回 `captchaEnabled`、`uuid`、`img`），按 IP 限流 |
| GET | `/resource/sms/code?phoneNumber=` | 免登录，短信验证码，按号码限流 |
| GET | `/resource/email/code?email=` | 免登录，邮箱验证码 |
| GET | `/` | 免登录，首页提示 |

## ruoyi-biz（业务，可变区）

### 供应商 `/biz/supplier`（`BizSupplierController`）

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/biz/supplier/list` | `biz:supplier:list` | 查询参数 `supplierName`（模糊）、`status`、`supplierCategory`（字典值，或 `__none__` 表示未分类）；每行带 `supplierCategoryLabel` |
| POST | `/biz/supplier/export` | `biz:supplier:export` | 筛选条件与列表相同，不分页 |
| GET | `/biz/supplier/{supplierId}` | `biz:supplier:query` | 已删除的记录返回的 data 为空 |
| POST | `/biz/supplier` | `biz:supplier:add` | 编码重复或分类无效时返回 500 和可读提示 |
| PUT | `/biz/supplier` | `biz:supplier:edit` | 编码不可修改，提交的编码会被忽略 |
| DELETE | `/biz/supplier/{supplierIds}` | `biz:supplier:remove` | 逻辑删除，多个 ID 用逗号分隔 |

### 采购单 `/biz/purchaseOrder`（`BizPurchaseOrderController`）

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/biz/purchaseOrder/list` | `biz:purchaseOrder:list` | 查询参数 `orderNo`（模糊）、`supplierId`、`supplierName`、`status`，以及 `params[beginOrderDate]`、`params[endOrderDate]` |
| GET | `/biz/purchaseOrder/supplierOptions` | `biz:purchaseOrder:list` | 返回启用状态的供应商 |
| POST | `/biz/purchaseOrder/export` | `biz:purchaseOrder:export` | 只导出主表 |
| GET | `/biz/purchaseOrder/{orderId}` | `biz:purchaseOrder:query` | 包含 `details` 明细；单据不存在时返回 500 |
| POST | `/biz/purchaseOrder` | `biz:purchaseOrder:add` | 单号、金额、状态都由系统计算，提交的值会被忽略 |
| PUT | `/biz/purchaseOrder` | `biz:purchaseOrder:edit` | 只能修改草稿，明细以本次提交的整体为准 |
| PUT | `/biz/purchaseOrder/submit/{orderId}` | `biz:purchaseOrder:submit` | 草稿变为已提交 |
| DELETE | `/biz/purchaseOrder/{orderIds}` | `biz:purchaseOrder:remove` | 只能删除草稿，明细一并删除 |

## ruoyi-system

### 用户 `/system/user`

| 方法 | 路径 | 权限 |
|---|---|---|
| GET | `/list` | `system:user:list` |
| POST | `/export` | `system:user:export` |
| POST | `/importData` | `system:user:import` |
| POST | `/importTemplate` | 登录即可 |
| GET | `/getInfo` | 登录即可（当前用户、角色、权限） |
| GET | `/`、`/{userId}` | `system:user:query` |
| POST | 根路径 | `system:user:add` |
| PUT | 根路径 | `system:user:edit` |
| DELETE | `/{userIds}` | `system:user:remove` |
| GET | `/optionselect` | `system:user:query` |
| PUT | `/resetPwd` | `system:user:resetPwd` |
| PUT | `/changeStatus` | `system:user:edit` |
| GET | `/unlock/{userId}` | `system:user:edit` |
| GET | `/authRole/{userId}` | `system:user:query` |
| PUT | `/authRole` | `system:user:edit` |
| GET | `/deptTree` | `system:user:list` |
| GET | `/list/dept/{deptId}` | `system:user:list` |

个人中心 `/system/user/profile`：GET 和 PUT 根路径、`PUT /updatePwd`，都是登录即可。

### 角色 `/system/role`

| 方法 | 路径 | 权限 |
|---|---|---|
| GET | `/list` | `system:role:list` |
| POST | `/export` | `system:role:export` |
| GET | `/{roleId}` | `system:role:query` |
| POST | 根路径 | `system:role:add` |
| PUT | 根路径 | `system:role:edit` |
| PUT | `/permission` | `system:role:edit` |
| PUT | `/changeStatus` | `system:role:edit` |
| DELETE | `/{roleIds}` | `system:role:remove` |
| GET | `/optionselect` | `system:role:query` |
| GET | `/authUser/allocatedList`、`/authUser/unallocatedList` | `system:role:list` |
| PUT | `/authUser/cancel`、`/authUser/cancelAll`、`/authUser/selectAll` | `system:role:edit` |
| GET | `/deptTree/{roleId}` | `system:role:list` |

### 菜单 `/system/menu`

| 方法 | 路径 | 权限 |
|---|---|---|
| GET | `/getRouters` | 登录即可（前端动态路由） |
| GET | `/list` | `system:menu:list` |
| GET | `/{menuId}` | `system:menu:query` |
| GET | `/treeselect` | `system:menu:query` |
| GET | `/roleMenuTreeselect/{roleId}` | `system:menu:query` |
| POST | 根路径 | `system:menu:add`，且需要超级管理员角色 |
| PUT | 根路径 | `system:menu:edit`，且需要超级管理员角色 |
| DELETE | `/{menuId}` | `system:menu:remove`，且需要超级管理员角色 |
| DELETE | `/cascade/{menuIds}` | `system:menu:remove`，且需要超级管理员角色 |

### 其他系统管理

| 路径前缀 | 接口与权限 |
|---|---|
| `/system/dept` | `GET /list`、`GET /list/exclude/{deptId}`：`system:dept:list`；`GET /{deptId}`、`GET /optionselect`：`system:dept:query`；POST 根路径：`system:dept:add`；PUT 根路径：`system:dept:edit`；`DELETE /{deptId}`：`system:dept:remove` |
| `/system/post` | `GET /list`、`GET /deptTree`：`system:post:list`；`POST /export`：`system:post:export`；`GET /{postId}`、`GET /optionselect`：`system:post:query`；POST、PUT、DELETE `/{postIds}`：`system:post:add/edit/remove` |
| `/system/dict/type` | `GET /list`：`system:dict:list`；`POST /export`：`system:dict:export`；`GET /{dictId}`：`system:dict:query`；POST、PUT：`system:dict:add/edit`；`DELETE /{dictIds}`、`DELETE /refreshCache`：`system:dict:remove`；`GET /optionselect` 登录即可 |
| `/system/dict/data` | `GET /list`：`system:dict:list`；`POST /export`：`system:dict:export`；`GET /{dictCode}`：`system:dict:query`；`GET /type/{dictType}` 登录即可（前端 `useDict` 调用它）；POST、PUT、`DELETE /{dictCodes}`：`system:dict:add/edit/remove` |
| `/system/config` | `GET /list`：`system:config:list`；`POST /export`：`system:config:export`；`GET /{configId}`：`system:config:query`；`GET /configKey/{configKey}` 登录即可；POST：`system:config:add`；PUT、`PUT /updateByKey`：`system:config:edit`；`DELETE /{configIds}`、`DELETE /refreshCache`：`system:config:remove` |
| `/system/notice` | `GET /list`：`system:notice:list`；`GET /{noticeId}`：`system:notice:query`；POST、PUT、`DELETE /{noticeIds}`：`system:notice:add/edit/remove` |
| `/system/client` | `GET /list`：`system:client:list`；`POST /export`：`system:client:export`；`GET /{id}`：`system:client:query`；POST：`system:client:add`；PUT、`PUT /changeStatus`：`system:client:edit`；`DELETE /{ids}`：`system:client:remove` |
| `/system/social` | `GET /list` 登录即可（当前用户绑定的第三方账号） |
| `/resource/oss` | `GET /list`：`system:oss:list`；`GET /listByIds/{ossIds}`：`system:oss:query`；`POST /upload`（multipart）：`system:oss:upload`；`GET /download/{ossId}`：`system:oss:download`；`DELETE /{ossIds}`：`system:oss:remove` |
| `/resource/oss/config` | `GET /list`、`GET /{ossConfigId}`：`system:ossConfig:list`；POST：`system:ossConfig:add`；PUT、`PUT /changeStatus`：`system:ossConfig:edit`；`DELETE /{ossConfigIds}`：`system:ossConfig:remove` |
| `/resource/message` | `GET /box` 登录即可（站内消息盒） |

### 系统监控

| 路径前缀 | 接口与权限 |
|---|---|
| `/monitor/operlog` | `GET /list`：`monitor:operlog:list`；`POST /export`：`monitor:operlog:export`；`DELETE /{operIds}`、`DELETE /clean`：`monitor:operlog:remove` |
| `/monitor/loginInfo` | `GET /list`：`monitor:logininfo:list`；`POST /export`：`monitor:logininfo:export`；`DELETE /{infoIds}`、`DELETE /clean`：`monitor:logininfo:remove`；`GET /unlock/{userName}`：`monitor:logininfo:unlock` |
| `/monitor/online` | `GET /list`：`monitor:online:list`；`DELETE /{tokenId}`：`monitor:online:forceLogout`；`GET /` 和 `DELETE /myself/{tokenId}` 登录即可（当前用户自己的会话） |
| `/monitor/cache` | `GET /`：`monitor:cache:list` |

## 消息推送（ruoyi-common-push）

路径由 `message.path` 配置：

- `GET {message.path}`：SSE 连接。
- `GET {message.path}/close`：`@SaIgnore`。
- `GET {message.path}/send`、`GET {message.path}/sendAll`：发送消息（示例用途）。

当 `message.transport=websocket` 时，改为注册 WebSocket 端点。

## ruoyi-workflow

| 路径前缀 | 接口与权限 |
|---|---|
| `/workflow/category` | `GET /list`：`workflow:category:list`；`POST /export`：`workflow:category:export`；`GET /{categoryId}`：`workflow:category:query`；POST、PUT、`DELETE /{categoryId}`：`workflow:category:add/edit/remove`；`GET /categoryTree` 登录即可 |
| `/workflow/definition` | `GET /list`、`GET /unPublishList`：`workflow:definition:list`；`GET /{id}`、`GET /xmlString/{id}`：`workflow:definition:query`；POST：`workflow:definition:add`；PUT：`workflow:definition:edit`；`PUT /publish/{id}`、`PUT /unPublish/{id}`：`workflow:definition:publish`；`DELETE /{ids}`：`workflow:definition:remove`；`POST /copy/{id}`：`workflow:definition:copy`；`POST /importDef`：`workflow:definition:import`；`POST /exportDef/{id}`：`workflow:definition:export`；`PUT /active/{id}`：`workflow:definition:active` |
| `/workflow/instance` | `GET /pageByRunning`、`GET /pageByFinish`：`workflow:instance:list`；`GET /getInfo/{businessId}`、`GET /flowHisTaskList/{businessId}`：`workflow:instance:query`；`DELETE /deleteByBusinessIds/{businessIds}`、`DELETE /deleteByInstanceIds/{instanceIds}`、`DELETE /deleteHisByInstanceIds/{instanceIds}`：`workflow:instance:remove`；`PUT /cancelProcessApply`：`workflow:instance:cancel`；`PUT /active/{id}`：`workflow:instance:active`；`GET /pageByCurrent`：`workflow:instance:currentList`；`GET /instanceVariable/{instanceId}`：`workflow:instance:variableQuery`；`PUT /updateVariable`：`workflow:instance:variable`；`POST /invalid`：`workflow:instance:invalid` |
| `/workflow/task` | 登录即可：`POST /startWorkFlow`、`POST /completeTask`、`GET /pageByTaskWait`、`GET /pageByTaskFinish`、`GET /pageByTaskCopy`、`GET /getTask/{taskId}`、`POST /getNextNodeList`、`POST /terminationTask`、`POST /taskOperation/{taskOperation}`、`POST /backProcess`、`GET /getBackTaskNode/{taskId}/{nowNodeCode}`、`GET /currentTaskAllUser/{taskId}`。`GET /pageByAllTaskWait`、`GET /pageByAllTaskFinish`：`workflow:task:list`；`PUT /updateAssignee/{userId}`、`POST /urgeTask`：`workflow:task:edit` |
| `/workflow/spel` | `GET /list`：`workflow:spel:list`；`GET /{id}`：`workflow:spel:query`；POST、PUT、`DELETE /{ids}`：`workflow:spel:add/edit/remove` |
| `/workflow/leave`（请假示例） | `GET /list`：`workflow:leave:list`；`POST /export`：`workflow:leave:export`；`GET /{id}`：`workflow:leave:query`；POST、`POST /submitAndFlowStart`：`workflow:leave:add`；PUT：`workflow:leave:edit`；`DELETE /{ids}`：`workflow:leave:remove` |

另外，Warm-Flow 设计器 UI 的接口（`/warm-flow/**`、`/warm-flow-ui/config`）由 Warm-Flow 插件提供。

## ruoyi-gen `/tool/gen`

| 方法 | 路径 | 权限 |
|---|---|---|
| GET | `/list`、`/db/list`、`/column/{tableId}`、`/getDataNames` | `tool:gen:list` |
| GET | `/{tableId}` | `tool:gen:query` |
| POST | `/importTable` | `tool:gen:import` |
| PUT | 根路径 | `tool:gen:edit` |
| GET | `/synchDb/{tableId}` | `tool:gen:edit` |
| DELETE | `/{tableIds}` | `tool:gen:remove` |
| GET | `/preview/{tableId}` | `tool:gen:preview` |
| GET | `/download/{tableId}`、`/batchGenCode` | `tool:gen:code` |

## ruoyi-demo（上游演示，不要在业务中依赖）

- `/demo/demo`（TestDemo）：`GET /list`、`GET /page`：`demo:demo:list`；`POST /importData`：`demo:demo:import`；`POST /export`：`demo:demo:export`；`GET /{id}`：`demo:demo:query`；POST、PUT、`DELETE /{ids}`：`demo:demo:add/edit/remove`。
- `/demo/tree`（TestTree）：`demo:tree:list/export/query/add/edit/remove`。
- 其余演示路由大多不带业务权限：`/demo/cache`、`/demo/redisLock`、`/demo/rateLimiter`、`/demo/redis/pubsub`、`/demo/queue/priority`、`/demo/excel`、`/demo/encrypt`、`/demo/sensitive`、`/demo/i18n`、`/demo/mail`、`/demo/sms`、`/demo/mqtt`、`/demo/websocket`、`/demo/mcp`、`/demo/batch`、`/es`、`/swagger/demo`。
- `/demo/saTokenDoc`：演示各种 `@SaCheckPermission` 写法（AND/OR 模式、通配符、orRole）。

## ruoyi-ai

`POST /snail-ai/user/register`（Snail AI 用户注册）。另有 MCP 服务端端点，由 `spring.ai.mcp.server.streamable-http.mcp-endpoint` 配置；`/snail-chat/**` 和 `/api/snail/chat/**` 在 `security.excludes` 里。

## 菜单与前端页面对照（业务）

| 菜单 | menu_id | path / component | 前端 URL |
|---|---|---|---|
| 业务管理（目录，menu_type M） | 1770000000000000000 | `biz` | 顶部或侧边菜单目录 |
| 供应商管理（C） | 1770000000000000001 | `supplier` / `biz/supplier/index` | `/biz/supplier` |
| 采购单管理（C） | 1770000000000000010 | `purchaseOrder` / `biz/purchaseOrder/index` | `/biz/purchaseOrder` |
