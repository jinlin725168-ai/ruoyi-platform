# 架构与运行机制

对应底座版本：1.0.19，生成日期：2026-09-28

## 一、技术栈与版本

后端（`backend/pom.xml` 的 `<properties>`）：

| 项 | 版本 |
|---|---|
| JDK | 21（`java.version`；compiler release 21，编译参数带 `-parameters`） |
| Spring Boot | 4.1.0；Spring AI 2.0.0；springdoc 3.0.3 |
| MyBatis / MyBatis-Plus / mybatis-plus-join | 3.5.19 / 3.5.17 / 1.5.9；dynamic-datasource 4.5.0 |
| Sa-Token | 1.45.0 |
| Redisson / lock4j | 4.6.1 / 2.2.7 |
| hutool / MapStruct-Plus / lombok | 5.8.47 / 1.5.1 / 1.18.46 |
| Fesod（Excel） | 2.0.2-incubating |
| Warm-Flow / LiteFlow | 1.8.9 / 2.16.1.2 |
| SnailJob / Snail AI | 2.0.2 / 1.1.1 |
| 安全版本覆盖（BASE-20260924-004） | netty、tomcat、httpcore5、postgresql、commons-beanutils、bouncycastle 在 `dependencyManagement` 开头显式钉版本，优先于 Spring Boot BOM 传递来的旧版本；上游升级 Spring Boot 后可以逐条删除 |
| 构建插件 | maven-compiler 3.15.0；surefire 3.5.5（父 pom）；failsafe 3.5.6、spotless 3.10.2、checkstyle 插件 3.6.0 加 checkstyle 10.18.2（`ruoyi-modules/pom.xml`）；flatten 1.7.3 |

注解处理器依次为 therapi-javadoc、lombok、spring-boot-configuration-processor、mapstruct-plus-processor、lombok-mapstruct-binding（`backend/pom.xml` 的 `maven-compiler-plugin`）。

前端（`frontend/package.json`）：vue 3.5.42、vue-router 5.3.1、pinia 4.0.3、element-plus 2.14.5、axios 1.20.0、vxe-table 4.21.9、echarts 6.1.0；开发依赖有 vite ^8.2.2、typescript ^6.0.3、vue-tsc ^3.3.11、vitest 4.1.11、@playwright/test ^1.63.0、oxlint、oxfmt、unocss、unplugin-auto-import、unplugin-vue-components。`packageManager` 为 pnpm@10.34.5，`engines.node` 要求 >=20.19.0。

## 二、启动

1. 入口 `org.dromara.DromaraApplication.main`（`backend/ruoyi-admin`），带 `BufferingApplicationStartup`；war 部署用 `DromaraServletInitializer`。
2. 构建时，Maven 资源过滤把 `@profiles.active@`、`@logging.level@`、`@monitor.*@` 写进 `application*`、`bootstrap*`、`banner*`。Maven profile 有 `local`、`dev`（默认激活）、`prod`。运行时可以用 `--spring.profiles.active` 覆盖，冒烟用的是 `dev,smoke`。
3. 各 `ruoyi-common-*` 的 `@AutoConfiguration` 按顺序装配：Jackson、Redisson 与缓存、MyBatis-Plus 插件、Sa-Token、`SecurityConfig`、过滤器、springdoc、push、encrypt、translation、sensitive 等。带 `enabled` 开关的模块按配置跳过。
4. MyBatis 按 `application.yml` 的 `mybatis-plus.mapperPackage`、`mapperLocations`、`typeAliasesPackage` 扫描 Mapper 接口、XML 和别名。新 Mapper 放在 `org.dromara.biz.<feature>.mapper`，XML 放在 `ruoyi-biz/src/main/resources/mapper/biz/`，不需要额外注册。
5. `SystemApplicationRunner.run` 调用 `ossConfigService.init()` 初始化 OSS 配置。
6. LiteFlow 加载 `classpath:liteflow/*.el.xml`，开关跟随 `warm-flow.enabled`。

## 三、请求链路

一个新接口从进入到返回，依次经过：

1. **Servlet 过滤器**
   - `SaTokenContextFilterForJakartaServlet`：`SecurityConfig` 注册，优先级最高。
   - `CryptoFilter`：`ApiDecryptAutoConfiguration` 注册，只在 `api-decrypt.enabled` 打开时生效，对 `@ApiEncrypt` 接口解密请求、加密响应。
   - `RepeatableFilter`（请求体可重复读）和 `XssFilter`（受 `xss.enabled` 控制）：由 `FilterConfig` 注册。
   - `/actuator/**` 走 Basic Auth（`SecurityConfig.getSaServletFilter`）。
2. **登录拦截**：`SecurityConfig.addInterceptors` 注册 `SaInterceptor`，覆盖 `AllUrlHandler` 收集到的所有路由，排除 `security.excludes`，`@SaIgnore` 由 Sa-Token 自行跳过。对其余请求：
   - `StpUtil.checkLogin()`；
   - 请求头或参数里的 `clientid` 必须与 token 扩展里的一致，否则按 401 处理；
   - 按 `sys_client` 的访问路径和 IP 白名单校验，不满足时报 403。
   
   另有 `PlusWebInvokeTimeInterceptor` 记录接口耗时。
3. **注解鉴权**：`@SaCheckPermission("biz:x:list")`、`@SaCheckRole`。权限来自 `SaPermissionImpl` 读取的 `LoginUser.menuPermission` 和 `rolePermission`，登录时由 `SysPermissionServiceImpl` 计算。超级管理员得到 `*:*:*`。菜单的增、改、删还要求超级管理员角色。
4. **参数绑定与校验**：
   - GET 查询：BO 加 `PageQuery`（`pageNum/pageSize/orderByColumn/isAsc`）。`pageSize` 缺省时为 `Integer.MAX_VALUE`。
   - 写接口：`@Validated(AddGroup.class 或 EditGroup.class) @RequestBody Bo`。
   - 路径变量上的 `@NotNull`、`@NotEmpty` 依赖控制器类上的 `@Validated`。
5. **切面**：
   - `@RepeatSubmit`：`RepeatSubmitAspect`，Redis 键由 URL、token 和参数组成。
   - `@RateLimiter`：`RateLimiterAspect`。
   - `@Log`：`LogAspect` 发布 `OperLogEvent`，再由 `SysOperLogServiceImpl` 异步入库。
6. **业务层**：Service 抛 `ServiceException(msg)` 表示可读的业务失败；多表写操作加 `@Transactional(rollbackFor = Exception.class)`。
7. **统一返回**：`R<T>`，即 `{code,msg,data}`。`R.ok` 为 200，`R.fail` 为 500，`R.warn` 为 601。`ResponseEnhancementAdvice` 配合 `JsonFieldProcessor` 处理 `@Translation`、`@Sensitive`；`BigNumberSerializer` 把超出 JS 安全整数范围的 Long 序列化为字符串。
8. **异常映射**（HTTP 状态恒为 200，用 `code` 区分）：

| 来源 | 处理器 | code |
|---|---|---|
| 未登录、token 失效、clientid 不匹配 | `SaTokenExceptionHandler` | 401 |
| 缺少权限或角色 | `SaTokenExceptionHandler` | 403 |
| `ServiceException` | `GlobalExceptionHandler.handleServiceException` | 500，或异常自带的 code |
| 校验失败（`BindException`、`MethodArgumentNotValidException`、`ConstraintViolationException`、`HandlerMethodValidationException`） | `GlobalExceptionHandler` | 500，msg 为校验消息 |
| JSON 或请求体格式错误 | `GlobalExceptionHandler` | 400 |
| 路由不存在 / 请求方法不支持 | `GlobalExceptionHandler` | 404 / 405 |
| `DuplicateKeyException` | `MybatisExceptionHandler` | 409 |
| 获取锁失败 `LockFailureException` | `RedisExceptionHandler` | 503 |
| 其他异常 | `GlobalExceptionHandler` | 500 |

**认证流程**：

1. `POST /auth/login`（类上 `@SaIgnore`，方法上 `@ApiEncrypt`）。
2. `ISysClientService.queryByClientId` 校验客户端。
3. 找到 `<grantType>AuthStrategy` 并执行：验证码（`captcha.enable` 打开时）、错误次数锁定（`SysLoginService.checkLogin`）、`buildLoginUser`、`LoginHelper.login` 写入 token 扩展。
4. 返回 `access_token`、`expire_in`、`client_id`。
5. 登录后调用 `GET /system/user/getInfo` 和 `GET /system/menu/getRouters`。

## 四、数据访问

- **审计字段**：实体继承 `BaseEntity`（`createDept/createBy/createTime/updateBy/updateTime`，没有 `params`）。`InjectionMetaObjectHandler` 在 insert 和 update 时通过 `LoginHelper` 自动填充。
- **主键**：全局 `idType` 为 ASSIGN_ID，即雪花 Long。实体上写 `@TableId(value = "x_id")`。
- **逻辑删除**：由 `mybatis-plus.enableLogicDelete` 全局打开，配合实体上的 `@TableLogic private String delFlag`。`deleteByIds` 实际执行 update；`select*`、`exists`、`selectCount` 自动追加未删除条件；Mapper XML 里的手写 SQL 不追加（`BizSupplierMapper.selectCategoriesIgnoreDeleted`、`BizPurchaseOrderMapper.selectMaxOrderNoByPrefix` 有意利用这一点）。
- **`updateById` 跳过 null 字段**：要清空字段，必须显式写空串（见 `BizPurchaseOrderServiceImpl.updateByBo` 对 remark 的处理）。
- **分页**：控制器接收 `PageQuery`，调用 `pageQuery.build()` 生成 `Page`（排序字段做驼峰转下划线和防注入），再 `mapper.selectVoPage(page, wrapper)`，最后 `PageResult.build(records, total)`。
- **MyBatis-Plus 插件**（`MybatisPlusConfig`）按顺序为：数据权限 `PlusDataPermissionInterceptor`（只对 `@DataPermission` 标注的 Mapper 方法生效）、分页 `PaginationInnerInterceptor`、乐观锁 `OptimisticLockerInnerInterceptor`。另有按 `mybatis-plus.sql-log.*` 打印 SQL 的拦截器。
- **多租户**：不存在，底座没有 `ruoyi-common-tenant`。
- **`BaseMapperPlus<T,V>`**：提供 `selectVo*`、`insertBatch`、`updateBatchById`、`lambda()` 链式查询；VO 转换由 MapStruct-Plus 的 `@AutoMapper` 完成。
- **忽略大小写的模糊查询**：业务里写成 `lqw.apply("LOWER(col) LIKE {0}", "%" + v.toLowerCase(Locale.ROOT) + "%")`，参数化以防注入（`BizSupplierServiceImpl.buildQueryWrapper`）。
- **数据源**：dynamic-datasource 严格模式，只配置了 `master`。
- **事务**：`@Transactional(rollbackFor = Exception.class)`，写在 ServiceImpl 的方法上。

## 五、横切能力

- **缓存**：
  - Spring Cache 由 `PlusSpringCacheManager` 实现，Redisson 作存储，外加 Caffeine 本地缓存（`CaffeineCacheDecorator`）。缓存名可写成 `name#ttl#maxIdleTime#maxSize`。
  - 缓存名常量在 `CacheNames`。字典查询带 `@Cacheable(SYS_DICT)`，字典增删改时同步刷新，所以 `DictService.getAllDictByDictType` 在字典修改后立即拿到新值。
- **会话**：Sa-Token 会话存在 Redis（`PlusSaTokenDao`）。
- **分布式锁、限流、防重**：`@Lock4j` 或 Redisson 锁；`@RateLimiter`；`@RepeatSubmit`。
- **流水号**：`SequenceUtils` 基于 Redis。采购单号没有用它，用的是库内最大值加一，再靠唯一索引冲突重试。
- **定时任务**：只有 SnailJob（`ruoyi-common-job`，示例在 `ruoyi-job`）。`snail-job.enabled` 在 dev 和 smoke 都关闭，底座里也没有 `@Scheduled`。
- **异步与事件**：`spring.task.execution` 线程池；`ThreadPoolConfig` 提供 `ScheduledExecutorService`；操作日志和登录日志走 Spring 事件。
- **消息推送**：由 `message.enabled/transport/path` 控制（SSE 或 WebSocket），业务里用 `ruoyi-api` 的 `MessageService`。smoke 运行档关闭。
- **文件存储**：`ruoyi-common-oss`（S3 兼容），配置存在 `sys_oss_config`，跨模块用 `OssService`。
- **加解密**：接口加密用 `@ApiEncrypt` 加 `api-decrypt.*`；字段加密用 `@EncryptField` 加 `mybatis-encryptor.*`（默认关闭）。
- **日志**：`@Log` 写入操作日志，结果在 `/monitor/operlog` 查询；`logback-plus.xml`。
- **国际化**：`i18n/messages*.properties`，`MessageUtils.message`。

## 六、前端运行机制

- **装配**：`main.ts` 装配 Pinia、router、Element Plus、i18n、指令（`directive/index.ts`）、插件（`plugins/index.ts`）、svg 图标。
- **请求封装**（`utils/request.ts`）：
  - axios 的 `baseURL` 取 `VITE_APP_BASE_API`。请求拦截器加上 `Authorization`、`clientid`、`Content-Language`；GET 参数用 `tansParams` 展开，支持 `params[beginX]`。
  - 短时间内对同一 URL、同一 body 的 POST/PUT 视为重复提交，直接拒绝。
  - 请求头带 `isEncrypt` 且 `VITE_APP_ENCRYPT` 打开时，请求体加密。
  - 响应拦截器：401 弹出重新登录框，500 用 `ElMessage.error`，601 用 warning，其他非 200 用 `ElNotification`，并 reject。成功时返回整个 `R`，页面里读 `res.data.rows`、`res.data.total`。
- **路由守卫**（`permission.ts`）：
  - 没有 token：白名单（`/login`、`/register`、`/social-callback`）直接放行，其余跳转 `/login?redirect=`。
  - 有 token 但角色为空：依次调用 `useUserStore().getInfo()`、`usePermissionStore().generateRoutes()`（请求 `getRouters`），再 `router.addRoute`。
- **动态路由**：`store/modules/permission.ts` 用 `import.meta.glob('./../../views/**/*.vue')` 建查找表。`sys_menu.component='biz/supplier/index'` 对应 `src/views/biz/supplier/index.vue`，访问路径由父目录 path 和菜单 path 拼成 `/biz/supplier`。
- **权限**：`v-hasPermi` 和 `utils/permission.ts` 的 `checkPermi` 读取 `useUserStore().permissions`。
- **字典**：`utils/dict.ts` 的 `useDict(...types)` 调用 `/system/dict/data/type/{type}`，结果缓存在 `store/modules/dict`。
- **状态管理**：Pinia 仓库在 `store/modules/*`。
- **自动导入**：unplugin-auto-import 和 unplugin-vue-components 在 vite 启动时生成 `src/types/auto-imports.d.ts` 和 `components.d.ts`。这两个文件被 git 忽略，已声明为 scratch。

## 七、环境与运行方式

- **本地中间件**：`infra/docker-compose.yml` 起容器 `ruoyi-mysql` 和 `ruoyi-redis`，端口约定见仓库根目录 `README.md`。本文不抄录端口和口令。
- **后端配置位置**（只列键）：
  - `ruoyi-admin/src/main/resources/application.yml`：`server.port`、`captcha.*`、`user.password.*`、`sa-token.*`、`security.excludes`、`mybatis-plus.*`、`api-decrypt.*`、`xss.*`、`springdoc.*`（`group-configs` 不含 `org.dromara.biz`）、`lock4j.*`、`message.*`、`warm-flow.*`、`liteflow.*`。
  - `application-dev.yml`：`spring.datasource.dynamic.*`、`spring.data.redis.*`、`redisson.*`、`snail-job.*`、`spring.boot.admin.client.*`、`mail.*`、`sms.*`、`justauth.*`，文件末尾覆盖了 `server.port`。
  - `application-prod.yml`：上游的生产模板。
  - `application-smoke.yml`（本仓库新增，与 dev 叠加）：关闭 `captcha.enable`、`api-decrypt.enabled`、`spring.boot.admin.client.enabled`、`snail-job.enabled`、`message.enabled`、`springdoc.api-docs.enabled`，并降低日志级别。端口、数据源 url、Redis 库索引由 `ruoyi_smoke.py` 通过命令行注入。
- **profile 的含义**：Maven 的 `dev` profile 决定资源过滤值，以及 surefire 和 failsafe 的 `groups`；Spring 的 `dev` 运行档连本地 infra；`smoke` 运行档是冒烟专用的开关集合。
- **前端配置位置**：
  - `frontend/.env.development` 和 `.env.production`：`VITE_APP_BASE_API`、`VITE_APP_PORT`、`VITE_APP_ENCRYPT`、`VITE_APP_RSA_*`、`VITE_APP_CLIENT_ID`、`VITE_APP_MESSAGE_*` 等。
  - `frontend/vite.config.ts`：代理目标取环境变量 `VITE_PROXY_TARGET`，未设置时用文件里的默认值；`resolve.tsconfigPaths` 打开；`CI` 环境变量存在时不自动打开浏览器。
- **编译**：`mvn -q -o -f backend/pom.xml -pl ruoyi-admin -am compile`（离线，依赖只能来自本地 Maven 仓库）。前端类型检查：`pnpm --dir frontend exec vue-tsc --noEmit`。
