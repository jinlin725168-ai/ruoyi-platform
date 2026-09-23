# 架构与运行机制

## 运行拓扑

请求链路是：浏览器 → Vite dev server → `ruoyi-admin.jar`（Jetty）→ MySQL（dynamic-datasource 的 `master`）和 Redis（Redisson）。

- Vite 把以 `VITE_APP_BASE_API` 开头的请求代理到后端。目标取环境变量 `VITE_PROXY_TARGET`，没有设置时用 `vite.config.ts` 里的默认地址，并去掉前缀。
- 本地中间件由 `infra/docker-compose.yml` 提供，端口约定见仓库根目录的 `README.md`。

## 启动顺序

1. `DromaraApplication.main` 创建 `SpringApplication`（带 `BufferingApplicationStartup`）。
2. 构建时，Maven 资源过滤把 `@profiles.active@`、`@logging.level@`、`@monitor.username@`、`@monitor.password@` 写进 `application*.yml`，默认 profile 为 dev。运行时可以用 `--spring.profiles.active=...` 覆盖，冒烟用的是 `dev,smoke`。
3. 各 `ruoyi-common-*` 的自动配置按 `@AutoConfiguration` 装配：Jackson、Redisson 与缓存、MyBatis-Plus 插件、Sa-Token、`SecurityConfig`、过滤器、springdoc、push、encrypt、translation、sensitive 等。带 `enabled` 开关的模块按配置跳过。
4. MyBatis 扫描 Mapper 和 XML：
   - 接口包由 `mybatis-plus.mapperPackage` 指定（`org.dromara.**.mapper`），XML 位置由 `mapperLocations` 指定（`classpath*:mapper/**/*Mapper.xml`），别名包由 `typeAliasesPackage` 指定（`org.dromara.**.domain`）。
   - 所以新 Mapper 只要放在 `org.dromara.biz.<feature>.mapper`，XML 放在 `resources/mapper/biz/`，就会被扫描到，不需要注册。
5. `SystemApplicationRunner.run` 调用 `ossConfigService.init()`，初始化 OSS 配置。
6. LiteFlow 加载 `classpath:liteflow/*.el.xml`。它的开关跟随 `warm-flow.enabled`。

## 配置（只列键和位置，不抄值）

### `backend/ruoyi-admin/src/main/resources/application.yml`（所有环境共享）

- **Web**：`server.port`、`server.jetty.*`、`spring.servlet.multipart.*`、`spring.mvc.format.date-time`、`spring.jackson.*`、`spring.messages.basename`、`spring.task.execution.*`、`spring.threads.virtual.enabled`、`logging.*`。
- **认证**：`captcha.enable/type/numberLength/charLength`、`user.password.maxRetryCount/lockTime`、`sa-token.token-name/is-concurrent/is-share/jwt-secret-key`、`security.excludes`（免登录路径）。
- **数据**：`mybatis-plus.enableLogicDelete/mapperPackage/mapperLocations/typeAliasesPackage/global-config.dbConfig.idType`、`mybatis-encryptor.*`（字段加密，默认关闭）。
- **加密与防护**：`api-decrypt.enabled/headerFlag/publicKey/privateKey`（接口加密）、`xss.enabled/excludeUrls`。
- **文档**：`springdoc.api-docs.enabled`、`springdoc.info.*`、`springdoc.group-configs`（分组包括 demo、web、system、gen、workflow，不包括 biz）。
- **其他**：`lock4j.*`、`management.*`、`message.enabled/transport/path/...`、`warm-flow.*`、`liteflow.*`、`mqtt.client.*`（关闭）、`easy-es.*`（关闭）、`spring.ai.mcp.server.*`、`spring.ai.mcp.client.*`（关闭）。

### `application-dev.yml`（本地开发，数据源和 Redis 指向 infra 容器）

- **监控与任务**：`spring.boot.admin.client.*`（关闭）、`snail-job.*`（关闭）、`snail-ai.*`（关闭）。
- **数据源**：`mybatis-plus.sql-log.enabled/output`；`spring.datasource.type`、`spring.datasource.dynamic.primary/strict`、`spring.datasource.dynamic.datasource.master.*`、`spring.datasource.dynamic.hikari.*`。
- **Redis**：`spring.data.redis.host/port/database/password/timeout/ssl.enabled`、`redisson.keyPrefix/threads/nettyThreads/singleServerConfig.*`。
- **外部集成**：`mail.*`（关闭）、`sms.*`、`justauth.*`。
- 文件末尾覆盖了 `server.port`，本地后端端口固定，见仓库 README。

### `application-prod.yml`

上游的生产模板，结构与 dev 相同。

### `application-smoke.yml`（本仓库新增，与 dev 叠加）

- 关闭 `captcha.enable`、`api-decrypt.enabled`、`spring.boot.admin.client.enabled`、`snail-job.enabled`、`message.enabled`、`springdoc.api-docs.enabled`，并把 `logging.level.*` 降到 warn。
- 端口、`spring.datasource.dynamic.datasource.master.url` 和 `spring.data.redis.database` 由 `acceptance/tools/ruoyi_smoke.py` 通过命令行参数注入。

### 其他位置

- `ruoyi-gen/src/main/resources/generator.yml`：`gen.author/packageName/autoRemovePre/tablePrefix`。默认包是 `org.dromara.system`，StoryLoop 不直接使用生成器的输出。
- `frontend/.env.development`、`frontend/.env.production`：`VITE_APP_TITLE`、`VITE_APP_LOGO_TITLE`、`VITE_APP_ENV`、`VITE_APP_BASE_API`、`VITE_APP_CONTEXT_PATH`、`VITE_APP_PORT`、`VITE_APP_ENCRYPT`、`VITE_APP_RSA_PUBLIC_KEY`、`VITE_APP_RSA_PRIVATE_KEY`、`VITE_APP_CLIENT_ID`、`VITE_APP_MESSAGE_ENABLED/TRANSPORT/PATH`、`VITE_APP_MONITOR_ADMIN`、`VITE_APP_SNAILJOB_ADMIN`、`VITE_APP_SNAILAI_ADMIN`；production 另有 `VITE_BUILD_COMPRESS`。
- `frontend/vite.config.ts`：`base` 取 `VITE_APP_CONTEXT_PATH`；`server.port` 取 `VITE_APP_PORT`；`server.open` 在 `CI` 环境变量存在时关闭；代理目标取 `VITE_PROXY_TARGET`。

## 请求管线（后端）

按执行顺序：

### 1. Servlet 过滤器

- `SaTokenContextFilterForJakartaServlet`：由 `SecurityConfig.saTokenContextFilterRegistration` 注册，优先级最高，覆盖 REQUEST、ASYNC 和 ERROR 分发。
- `CryptoFilter`：`ApiDecryptAutoConfiguration` 注册，只在 `api-decrypt.enabled` 打开时生效。对 `@ApiEncrypt` 接口，按请求头 `api-decrypt.headerFlag` 做 RSA 加 AES 解密，并加密响应。
- `FilterConfig` 注册 `RepeatableFilter`（让请求体可重复读）和 `XssFilter`（受 `xss.enabled` 控制，排除 `xss.excludeUrls`）。
- `SecurityConfig.getSaServletFilter`：`/actuator/**` 走 Basic Auth，凭据取 `spring.boot.admin.client.username/password`。

### 2. 拦截器（`SecurityConfig.addInterceptors`）

`SaInterceptor` 覆盖 `AllUrlHandler` 收集到的所有路由，排除 `security.excludes`，`@SaIgnore` 由 Sa-Token 自行跳过。对其余请求：

1. `StpUtil.checkLogin()` 检查登录。
2. 请求头或请求参数里的 `clientid` 必须与 token 扩展里的 `clientid` 一致，否则按未登录处理（401）。
3. 按 `sys_client` 配置的访问路径（token 扩展 `clientAccessPath`）和 IP 白名单（`clientIpWhitelist`）校验，不满足时报 403。

另有 `PlusWebInvokeTimeInterceptor` 记录接口耗时。前端和冒烟客户端都会同时带上 `Authorization: Bearer <token>` 和 `clientid` 两个请求头。

### 3. 注解鉴权（Sa-Token 注解拦截）

- 注解：`@SaCheckPermission("biz:x:list")`、`@SaCheckRole`、`@SaIgnore`、`@SaCheckLogin`。
- 权限来源：`SaPermissionImpl` 读取当前 `LoginUser.menuPermission` 和 `rolePermission`。这两项在登录时由 `SysPermissionServiceImpl` 计算；超级管理员得到 `*:*:*` 和角色 `superadmin`。
- 菜单的增、改、删还额外要求超级管理员角色（`@SaCheckRole(SystemConstants.SUPER_ADMIN_ROLE_KEY)`）。

### 4. 参数绑定与校验

- GET 查询：BO 加 `PageQuery`（`pageNum/pageSize/orderByColumn/isAsc`）绑定查询参数。`pageSize` 缺省时是 `Integer.MAX_VALUE`，也就是查全部。
- 写接口：`@Validated(AddGroup.class 或 EditGroup.class) @RequestBody Bo`。
- 路径变量上的 `@NotNull`、`@NotEmpty` 生效，依赖控制器类上有 `@Validated`。
- 不在控制器里时，用 `ValidatorUtils.validate(obj, groups...)`。

### 5. 切面

- `@RepeatSubmit`：由 `RepeatSubmitAspect` 处理，Redis 键由 URL、token 和参数组成，默认间隔 5000ms。
- `@RateLimiter`：由 `RateLimiterAspect` 处理。
- `@Log(title, businessType)`：`LogAspect` 发布 `OperLogEvent`，再由 `SysOperLogServiceImpl` 异步入库，可在 `/monitor/operlog` 查询。

### 6. 业务层

- 可读的业务失败：`throw new ServiceException(msg)`。
- 事务：`@Transactional(rollbackFor = Exception.class)`。

### 7. 响应

- 统一返回 `R<T>`，字段为 `code`、`msg`、`data`。`R.ok` 的 code 是 200，`R.fail` 是 500，`R.warn` 是 601。
- `ResponseEnhancementAdvice` 配合 `JsonFieldProcessor` 管线，处理 `@Translation`、`@Sensitive` 等字段增强。
- `BigNumberSerializer` 把超出 JS 安全整数范围的 Long 序列化为字符串，所以前端的 ID 类型写成 `string | number`。

### 8. 异常映射

除特别说明外，HTTP 状态恒为 200，用 `code` 表示结果。

| 来源 | 处理器 | code |
|---|---|---|
| 未登录、token 失效、`clientid` 不匹配 | `SaTokenExceptionHandler.handleNotLoginException` | 401 |
| 缺少权限或角色 | `SaTokenExceptionHandler.handleNotAccessException` | 403 |
| `ServiceException` | `GlobalExceptionHandler.handleServiceException` | 500，或异常自带的 code |
| 校验失败：`BindException`、`MethodArgumentNotValidException`、`ConstraintViolationException`、`HandlerMethodValidationException` | `GlobalExceptionHandler` | 500，msg 为校验消息 |
| JSON 或请求体格式错误 | `handleJsonParseException`、`handleHttpMessageNotReadableException` | 400 |
| 路由不存在 | `handleNoHandlerFoundException` | 404 |
| 请求方法不支持 | `handleHttpRequestMethodNotSupported` | 405 |
| 唯一键冲突 `DuplicateKeyException` | `MybatisExceptionHandler` | 409 |
| 获取锁失败 `LockFailureException` | `RedisExceptionHandler` | 503 |
| 其他 `RuntimeException` 或 `Exception` | `GlobalExceptionHandler` | 500，msg 里带错误编号 |

## 认证流程

1. `POST /auth/login`：类上 `@SaIgnore`，方法上 `@ApiEncrypt`。请求体解析为 `LoginBody`（含 `clientId`、`grantType`）。
2. `ISysClientService.queryByClientId` 校验客户端存在、支持该 grantType、状态正常。
3. `IAuthStrategy.login` 找到 `<grantType>AuthStrategy`。以密码策略为例：
   1. 如果打开了验证码（`captcha.enable`），先校验验证码。
   2. 按用户名查询用户，检查是否停用。
   3. `SysLoginService.checkLogin` 处理错误次数和锁定，缓存键前缀为 `CacheNames.PWD_ERR_CNT_KEY`。
   4. `buildLoginUser` 构建 `LoginUser`。
   5. `LoginHelper.login` 生成 token，并在 token 扩展里写入 userId、userName、deptId、clientid、客户端访问规则等。
4. 返回 `LoginVo`，包含 `access_token`、`expire_in`、`client_id`。
5. 登录后，`GET /system/user/getInfo` 返回用户、角色和权限；`GET /system/menu/getRouters` 返回动态路由。

## 数据访问

- **实体与自动填充**：实体继承 `BaseEntity`。insert 和 update 时，`InjectionMetaObjectHandler` 用 `LoginHelper` 自动填充 `createDept/createBy/createTime/updateBy/updateTime`。
- **主键**：全局 `idType=ASSIGN_ID`，即雪花 Long。实体上写 `@TableId(value = "x_id")`。冒烟日志里偶尔出现 `Clock moved backwards`，是 WSL 下的环境时钟抖动。
- **逻辑删除**：`mybatis-plus.enableLogicDelete` 全局打开，实体字段写 `@TableLogic private String delFlag`。`deleteByIds` 实际执行 update，查询、`exists`、`selectCount` 自动追加未删除条件。手写 XML 不追加，例如 `BizPurchaseOrderMapper.selectMaxOrderNoByPrefix` 有意不过滤。
- **`BaseMapperPlus<T, V>`**：提供 `selectVoById`、`selectVoByIds`、`selectVoList`、`selectVoPage`、`selectVoOne`、`insertBatch`、`updateBatchById`、`insertOrUpdateBatch`、`lambda()`（`LambdaCrudChainWrapper`，可链式调用 `.eq(...).voOne()`）、`lambdaUpdate()`。VO 转换由 MapStruct-Plus（`@AutoMapper`）完成。
- **MyBatis-Plus 插件**（`MybatisPlusConfig`）按顺序为：
  1. 数据权限 `PlusDataPermissionInterceptor`，只对标注了 `@DataPermission` 的 Mapper 方法生效；
  2. 分页 `PaginationInnerInterceptor`；
  3. 乐观锁 `OptimisticLockerInnerInterceptor`。
  
  另有 `SqlLogInterceptor`，按 `mybatis-plus.sql-log.*` 打印 SQL。
- **多表**：可以用 `mybatis-plus-join` 的 `MPJLambdaWrapper`。当前业务只用 `LambdaQueryWrapper` 加冗余字段（例如 `biz_purchase_order.supplier_name`）。
- **数据权限**：`@DataPermission({@DataColumn(key = "deptName", value = "dept_id"), ...})` 标注在 Mapper 方法上，示例见 `TestDemoMapper`。两个业务规格都明确不做数据权限隔离。
- **数据源**：dynamic-datasource 严格模式，只配置了 `master`，需要切换时用 `@DS`。

## 缓存

- **实现**：Spring Cache 由 `PlusSpringCacheManager` 实现，Redisson 作存储，前面加一层 Caffeine 本地缓存（`CaffeineCacheDecorator`）。
- **缓存名语法**：可写成 `name#ttl#maxIdleTime#maxSize` 来带参数，示例是 `CacheNames.DEMO_CACHE`。
- **已有缓存名**（`CacheNames`）：`sys_config`、`sys_dict`、`sys_dict_type`、`sys_client`、`sys_user_name`、`sys_nickname`、`sys_dept`、`sys_oss`、`sys_role_custom`、`sys_dept_and_child`、`sys_oss_config`；另有键前缀 `online_tokens:`、`pwd_err_cnt:`。
- **字典缓存与失效**：`SysDictTypeServiceImpl` 的字典查询带 `@Cacheable(SYS_DICT)`。字典数据增删改时，通过 `@CachePut` 或 `CacheUtils.evict` 同步，所以 `DictService.getAllDictByDictType` 在字典管理修改后立即拿到新值。供应商分类的有效性校验依赖这一点。
- **会话存储**：Sa-Token 会话存在 Redis（`PlusSaTokenDao`）。冒烟使用独立的 Redis 库索引。
- **手工缓存**：`RedisUtils` 支持对象、列表、集合、Map、原子数、发布订阅、限流；`CacheUtils` 按缓存名读写、失效、清空。

## 调度与异步

- **定时任务**：走 SnailJob（`ruoyi-common-job` 的 `SnailJobConfig`，示例执行器在 `ruoyi-job`）。`snail-job.enabled` 在 dev 和 smoke 中都关闭，底座里也没有任何 `@Scheduled` 任务。要做定时业务，需要启用 SnailJob 客户端和 `ruoyi-snailjob-server`，这是底座议题。
- **线程池**：`spring.task.execution` 启用 Spring 管理的线程池（线程名前缀 `async-`）；`ThreadPoolConfig` 提供 `ScheduledExecutorService`。例如 `AuthController` 在登录 5 秒后推送欢迎消息。
- **事件**：操作日志、登录日志用 Spring 事件异步处理。
- **消息推送**：由 `message.enabled/transport/path` 控制，支持 SSE 和 WebSocket；smoke 运行档关闭。业务里发消息用 `MessageService`（ruoyi-api）。
- **分布式锁**：lock4j 的 `@Lock4j`，或 `RedisUtils.getClient()` 取 Redisson 锁。

## 前端运行时

- **应用装配**：`main.ts` 装配 Pinia、router、Element Plus、i18n、指令（`directive/index.ts`）、插件（`plugins/index.ts`）和 svg 图标。
- **路由守卫**（`permission.ts`）：
  - 没有 token：白名单路径（`/login`、`/register`、`/social-callback`）直接放行，其余跳转 `/login?redirect=...`。
  - 有 token 但角色为空：先 `useUserStore().getInfo()`，再 `usePermissionStore().generateRoutes()`（调用 `getRouters`），最后 `router.addRoute` 动态添加路由。
- **动态路由的组件解析**：
  - `store/modules/permission.ts` 用 `import.meta.glob('./../../views/**/*.vue')` 建一张查找表，键是相对 `views` 的路径。
  - `sys_menu.component='biz/supplier/index'` 对应文件 `src/views/biz/supplier/index.vue`。
  - 访问路径由父目录 path 和菜单 path 拼成，例如 `/biz/supplier`。
  - 路由名是 `SysMenu.getRouteName()`（path 首字母大写）加 menuId；`loadView` 用 `createCustomNameComponent` 包装组件，以支持 keep-alive。
- **请求封装**（`utils/request.ts`）：
  - axios 实例的 `baseURL` 是 `VITE_APP_BASE_API`，超时 50 秒。
  - 请求拦截器加上 `Authorization` 和 `Content-Language`。GET 参数用 `tansParams` 展开，支持 `params[beginX]` 这类嵌套参数。
  - 500ms 内对同一 URL、同一 body 的 POST/PUT 视为重复提交，前端直接拒绝。
  - 请求头带 `isEncrypt` 且 `VITE_APP_ENCRYPT` 打开时，请求体用 AES 加密，AES 密钥再用 RSA 加密。
  - 响应拦截器：401 弹出重新登录框；500 用 `ElMessage.error` 提示；601 用 warning 提示；其他非 200 用 `ElNotification`，并 reject。成功时返回整个 `R` 对象，所以页面里读 `res.data.rows` 和 `res.data.total`。
  - `download(url, params, fileName)` 以 `x-www-form-urlencoded` 格式 POST，响应作为 blob 保存成文件。
- **权限控制**：`v-hasPermi` 和 `utils/permission.ts` 的 `checkPermi` 读取 `useUserStore().permissions`，其中 `*:*:*` 表示全部权限。
