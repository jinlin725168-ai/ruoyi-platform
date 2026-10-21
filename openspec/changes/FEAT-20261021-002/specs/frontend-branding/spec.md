# frontend-branding — delta for FEAT-20261021-002

## ADDED Requirements

### Requirement: 红魔品牌统一展示

_Story S1, priority P1, from FEAT-20261021-002_

As 使用业务工作台的员工, 在登录页、注册页、侧栏和浏览器标签上都看到一致的“红魔业务工作台”/“红魔”品牌, so that 我能确认正在使用的是本单位的红魔业务工作台.

THE SYSTEM SHALL 在一个前端品牌模块里集中维护品牌全称“红魔业务工作台”和短名“红魔”
THE SYSTEM SHALL 让登录页、注册页、侧栏标识和浏览器标题的品牌文字都取自品牌模块，不再读取 VITE_APP_TITLE 或 VITE_APP_LOGO_TITLE
WHEN 动态标题开关开启且当前页面有页面标题 THE SYSTEM SHALL 把浏览器标题设为“<页面标题> - 红魔业务工作台”
WHEN 动态标题开关关闭或当前页面没有页面标题 THE SYSTEM SHALL 把浏览器标题设为“红魔业务工作台”
WHEN 侧栏展开 THE SYSTEM SHALL 在品牌标识里显示包含“红魔”的文字
WHEN 侧栏折叠 THE SYSTEM SHALL 仍显示可识别的红魔标识，并给它包含“红魔”的可访问名称
THE SYSTEM SHALL 在登录页和注册页的品牌展示区移除“Plus UI Workspace”“企业级后台管理系统”等上游推广文案，沿用现有布局和主题样式
THE SYSTEM SHALL 用 Vue 文本插值渲染品牌文案，不使用 v-html

#### Scenario: A1
- **GIVEN** 登录页或已登录后的侧栏可见
- **WHEN** 查看用户可见的品牌名称
- **THEN** 登录页展示“红魔业务工作台”，侧栏展示“红魔”

#### Scenario: A2
- **GIVEN** 浏览器可以访问登录、注册与首页路由
- **WHEN** 在这三个路由之间切换并读取浏览器标题
- **THEN** 登录与注册页标题为“红魔业务工作台”，首页为“首页 - 红魔业务工作台”

#### Scenario: A3
- **GIVEN** 登录、注册、侧栏与首页已呈现
- **WHEN** 逐一查看这些入口的品牌文字
- **THEN** 各入口使用一致的红魔名称，不再显示“Plus UI Workspace”等旧品牌推广文案

#### Scenario: A4
- **GIVEN** 浏览器没有登录状态，也没有记住的账号
- **WHEN** 访问登录页
- **THEN** 登录表单主标题和浏览器标题都是“红魔业务工作台”，页面不出现“企业级后台管理系统”

#### Scenario: A5
- **GIVEN** 测试用户已登录并进入首页
- **WHEN** 把侧栏从展开切换为折叠
- **THEN** 展开时品牌标识文字包含“红魔”，折叠后标识仍然可见，且可访问名称包含“红魔”

#### Scenario: A6
- **GIVEN** 浏览器没有登录状态
- **WHEN** 访问注册页
- **THEN** 注册表单主标题和浏览器标题都是“红魔业务工作台”


### Requirement: 登录表单不预填口令且既有登录行为保留

_Story S2, priority P1, from FEAT-20261021-002_

As 使用业务工作台的员工, 登录表单不再预填任何账号和口令，同时登录相关功能照常可用, so that 默认口令不会暴露在界面上，日常登录也不受品牌替换影响.

WHEN 浏览器里没有记住的账号 THE SYSTEM SHALL 让登录表单的账号和口令初始都为空
THE SYSTEM SHALL 不在前端源码、规格和测试里写入任何默认口令
WHEN 用户勾选记住密码并登录成功 THE SYSTEM SHALL 下次打开登录页时只回填账号，口令保持为空
WHEN 用户提交正确的账号和口令 THE SYSTEM SHALL 跳转到登录前的目标页（默认首页），并按权限加载动态菜单
WHEN 登录被后端拒绝 THE SYSTEM SHALL 停留在登录页并显示错误提示，验证码开启时刷新验证码
WHEN 后端报告验证码关闭 THE SYSTEM SHALL 不显示验证码输入框
THE SYSTEM SHALL 保留微信、MaxKey、TopIAM、Gitee、GitHub 五个第三方登录入口
WHEN 用户退出登录 THE SYSTEM SHALL 回到登录页，访问受保护页面时重定向到登录页
THE SYSTEM SHALL 保留登录页和注册页页脚的上游版权署名
THE SYSTEM SHALL 把登录页的品牌展示区拆成独立组件，使本次新增或修改的文件不超过 500 行、函数不超过 50 行

#### Scenario: A7
- **GIVEN** 浏览器没有登录状态，也没有记住的账号
- **WHEN** 访问登录页
- **THEN** 账号输入框和口令输入框的值都是空串

#### Scenario: A8
- **GIVEN** 临时库里有测试夹具账号
- **WHEN** 用户在登录页填入该账号和口令后提交
- **THEN** 进入首页，并能从动态菜单打开采购单页面

#### Scenario: A9
- **GIVEN** 临时库里有测试夹具账号
- **WHEN** 用户提交该账号和一个错误口令
- **THEN** 仍停留在登录页，并显示后端返回的错误提示

#### Scenario: A10
- **GIVEN** 用户曾勾选记住密码并用测试账号登录成功，之后退出登录
- **WHEN** 再次打开登录页
- **THEN** 账号输入框回填该账号，口令输入框为空，记住密码保持勾选

#### Scenario: A11
- **GIVEN** 浏览器没有登录状态
- **WHEN** 访问登录页
- **THEN** 微信、MaxKey、TopIAM、Gitee、GitHub 五个第三方登录入口都可见

#### Scenario: A12
- **GIVEN** 测试用户已登录并位于首页
- **WHEN** 用户退出登录
- **THEN** 回到登录页，再访问首页会被重定向到登录页

#### Scenario: A13
- **GIVEN** 后端以 smoke 运行档启动，验证码已关闭
- **WHEN** 访问登录页
- **THEN** 登录表单不显示验证码输入框

#### Scenario: A14
- **GIVEN** 浏览器没有登录状态
- **WHEN** 分别访问登录页和注册页
- **THEN** 两个页面的页脚都包含“Copyright © 2018-<当前年份> 疯狂的狮子Li All Rights Reserved.”


### Requirement: 首页介绍红魔业务工作台的已有能力

_Story S3, priority P2, from FEAT-20261021-002_

As 登录后的员工, 首页介绍红魔业务工作台里实际可用的供应商管理和采购单管理能力, so that 我能直接了解系统能做什么，而不是看到上游项目的推广.

THE SYSTEM SHALL 在首页主标题中显示品牌全称“红魔业务工作台”
THE SYSTEM SHALL 在首页介绍现有的供应商管理和采购单管理能力，只描述系统里已有的功能
THE SYSTEM SHALL 从首页移除上游项目矩阵、源码和更新日志等推广入口
THE SYSTEM SHALL 不在首页展示编造的业务统计、收益数据，也不展示红魔厂商的产品参数或商业背书
THE SYSTEM SHALL 沿用首页现有的卡片布局和主题样式

#### Scenario: B1
- **GIVEN** 测试用户已登录
- **WHEN** 打开首页
- **THEN** 首页主标题包含“红魔业务工作台”，正文同时介绍“供应商管理”和“采购单管理”

#### Scenario: B2
- **GIVEN** 测试用户已登录
- **WHEN** 打开首页
- **THEN** 首页主内容区不出现“RuoYi-Cloud-Plus”“项目矩阵”“查看源码”“更新日志”，也没有指向 gitee.com/dromara、github.com/dromara 或 plus-doc.dromara.org 的入口

#### Scenario: B3
- **GIVEN** 测试用户已登录
- **WHEN** 打开首页
- **THEN** 首页主内容区不出现“收益”“营收”“利润”“销售额”“成交额”“官方授权”“背书”等统计或宣传字样
