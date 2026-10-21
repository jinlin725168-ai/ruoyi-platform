## Context
本轮提供的事实记录为空。已读取相关底座文档和计划修改的前端源码。登录页579行，注册页523行，重复包含品牌展示和样式；品牌分别来自环境标题与侧栏标题。浏览器标题更新目前位于有 token 的分支，不能覆盖未登录登录/注册路由。合同已批准品牌与范围；本设计不执行实现或验证，也不把先前运行的 GREEN 当成本轮证据。

## Goals
统一应用加载后的红魔品牌，清空登录默认账号和口令，用真实已有能力替换首页推广；保持认证、权限、动态菜单、主题、布局和上游归属。

## Decisions
### 集中品牌及标题计算
- Choice：新增无副作用的品牌模块，导出全称、短名和标题格式化函数。
- Rationale：让全部入口共享同一来源，并能直接用现有 Vitest 验证开关及空标题分支。
- Alternatives considered：分别硬编码会重复维护；修改环境变量或静态 HTML 超出范围。

### 共用认证页品牌展示
- Choice：抽取 AuthBrandPanel，同时迁移两页重复品牌区模板、静态介绍和专属 SCSS，包括移动端断点。表单、页脚和认证逻辑留在页面。
- Rationale：两页都已超过500行，共用展示组件可以在保留布局的同时满足文件限制。展示内容只介绍供应商、采购单、动态菜单和主题等已有能力。
- Alternatives considered：只抽登录页仍会留下超限注册页；抽认证表单会扩大行为变更风险。

### 标题更新与权限守卫
- Choice：useDynamicTitle 委托纯函数；路由守卫在认证分支前通过现有 settingsStore.setTitle 更新当前页面名，缺失时传空串。保留设置开关现有调用链。
- Rationale：登录、注册及无标题页面都需要刷新标题，且不能沿用上一页标题。只移动标题处理，不改变访问权限。
- Alternatives considered：在各页面分别写 document.title 容易遗漏路由和开关语义。守卫回调若超过50行，在同文件抽取原有用户信息及动态路由初始化流程，保持错误、返回值、执行顺序和重定向参数不变，不新增业务模块。

### 侧栏文字标识和真实能力首页
- Choice：侧栏使用短名文字徽标及包含品牌的 aria-label，折叠后仍可识别；首页保留卡片布局，以静态业务能力条目替换产品矩阵与推广操作。
- Rationale：无需新图片、接口、权限或依赖；不引入未经授权的厂商标志或无权限快捷入口。
- Alternatives considered：保留旧图标不能满足名称一致性；新增数据看板或业务快捷入口会扩大范围。

## Files
| 文件 | 操作与职责 |
|---|---|
| frontend/src/constants/brand.ts | 新增品牌常量及纯标题函数，公共导出附文档注释 |
| frontend/src/constants/brand.test.ts | 新增纯逻辑 Vitest，用实际函数返回值验证标题规则 |
| frontend/src/components/AuthBrandPanel/index.vue | 新增共用品牌展示及专属响应式样式，无认证状态 |
| frontend/src/views/login.vue | 接入组件和品牌常量，移走展示样式，清空初始值及回填默认值，保留认证流程和署名 |
| frontend/src/views/register.vue | 接入组件和品牌常量，移走重复展示样式，保留表单及署名 |
| frontend/src/views/index.vue | 替换 products、capabilityGroups 和相关模板，移除 goTarget 推广操作及失效样式 |
| frontend/src/layout/components/Sidebar/Logo.vue | 改为品牌文字标识，补充折叠/展开可访问名称，保留路由目标和主题 |
| frontend/src/settings.ts | 默认网页标题引用品牌全称，其他设置保持原语义 |
| frontend/src/utils/dynamicTitle.ts | 按现有 settings 状态调用纯标题函数 |
| frontend/src/permission.ts | 覆盖全部路由的标题刷新；必要时同文件拆分守卫函数以满足长度限制 |

特征化测试由特征化角色规划并写入允许测试路径；受保护验收由验收角色生成。实现只能修改已锁定 characterization.touched 中的既有文件及本方案新增文件。dependencies 为空表示不新增、不替换依赖，继续使用仓库已有版本。

## Data And Interfaces
| 项目 | 约定 |
|---|---|
| BRAND_FULL_NAME | 红魔业务工作台 |
| BRAND_SHORT_NAME | 红魔 |
| formatBrandTitle | 动态标题开启且页面名非空：页面名 + 空格连字符空格 + 全称；其余情况仅全称 |
| AuthBrandPanel | 内部只读展示组件，不接收账号、口令、token 或用户信息 |
| 登录数据 | 保留 LoginData 形状、现有提交接口、验证码及第三方登录参数；仅改变默认值 |
| 本地状态 | 保留 username、rememberMe 的现有处理，继续移除历史 password 键，不迁移格式 |
| 数据表、列、HTTP端点、权限串 | 无新增、无修改；不修改菜单或路由定义 |

## Risks And Trade-Offs
风险集中在守卫控制流、标题残留、展示样式迁移及空默认值与记住账号的交互。通过特征化、纯函数测试和独立真实浏览器回归分别验证。现有 frontend_check.py 只拦部分路径类型错误，因此另核对所有修改路径的 vue-tsc 诊断。所有运行交给既有 scratch 执行器；环境故障保留原始错误，不改门禁。脚本加载前 HTML 静态标题保持合同明确的底座例外。没有配置原则 ID，因此 principle_checks 为空。

## Implementation record

## Context
依据已批准 shared-brand 方案及配置中的 module_roots、test_roots 实现。仅修改七个 touched 既有文件并新增三个批准文件，未修改锁定特征化、验收工具、底座或 Git 状态。

## Goals
集中维护红魔品牌，统一登录、注册、侧栏及应用加载后的浏览器标题；清空登录初始账号和口令；首页介绍真实已有业务能力，保留认证、权限、菜单、主题和上游署名。

## Tests First
新增 frontend/src/constants/brand.test.ts，覆盖品牌名称、有页面名、空串、缺省输入及关闭动态标题。
首次运行 frontend_unit.py 实际 RED：Cannot find module './brand'。其余 34 项测试通过。实现后最终运行结果为 7 个测试文件、38 项测试全部通过，锁定特征化保持不变。
frontend_check.py 最终退出 0，业务类型错误为 0；额外 vue-tsc 核对本次全部修改路径，无诊断。全部修改文件少于 500 行，函数不超过 50 行。
已调用独立品牌/登录验收及系统冒烟清单。串行重试仍在后端构建阶段退出 2，未进入浏览器行为断言，不能宣称验收 GREEN。本角色未取得本轮品牌浏览器 RED 证据。

## Decisions
### 品牌集中维护
Choice：品牌模块导出全称、短名和 formatBrandTitle。
Rationale：所有入口共享来源，标题开关分支可独立测试。
Alternatives considered：重复硬编码或编辑环境配置。

### 共用认证展示组件
Choice：迁移两页品牌模板、介绍及响应式样式到 AuthBrandPanel。
Rationale：保留表单行为并使登录页、注册页分别降至 467、411 行。
Alternatives considered：抽取认证表单会扩大行为风险。

### 标题及权限流程
Choice：认证判断前更新页面标题；同文件抽取既有动态路由初始化流程。
Rationale：覆盖匿名和无标题路由，并满足函数长度限制。
Alternatives considered：各页面直接设置标题容易遗漏路由。

### 侧栏及首页
Choice：展开、折叠均显示短名并提供品牌可访问名称；首页保留卡片布局，展示供应商档案及采购单功能。
Rationale：无需新增接口、菜单、依赖或虚构数据。
Alternatives considered：保留旧图标或新增统计看板。

## Risks And Trade-Offs
完整闭环受执行环境阻断。串行运行的变更验收和系统冒烟均报告：
`Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project ruoyi-system: Fatal error compiling: java.lang.ExceptionInInitializerError: java.io.FileNotFoundException: <local-runtime-path> (Read-only file system)`。
未修改该私有路径、后端或安全门。早期并行调用共用 scratch 产生过构建干扰，已串行重试并确认上述独立阻断。
自动导入声明生成也受 `Error: listen EPERM: operation not permitted 127.0.0.1:5177` 阻断；修改页面显式导入所用符号后，修改路径类型诊断为零，但声明生成要求仍未完成。验证码开启及外部第三方认证流程未覆盖。脚本执行前静态 HTML 标题维持合同例外。

## Files
- frontend/src/constants/brand.ts：集中品牌及标题纯函数。
- frontend/src/constants/brand.test.ts：标题规则 Vitest。
- frontend/src/components/AuthBrandPanel/index.vue：共用品牌展示及响应式样式。
- frontend/src/views/login.vue：接入品牌组件，空账号和口令，保留账号回填及认证处理。
- frontend/src/views/register.vue：接入品牌组件，保留注册行为和署名。
- frontend/src/views/index.vue：以真实业务能力替换推广内容。
- frontend/src/layout/components/Sidebar/Logo.vue：短名文字标识及可访问名称。
- frontend/src/settings.ts：默认标题引用品牌。
- frontend/src/utils/dynamicTitle.ts：委托标题纯函数。
- frontend/src/permission.ts：全路由标题刷新及既有初始化流程拆分。
