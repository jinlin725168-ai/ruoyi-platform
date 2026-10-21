# Decisions for FEAT-20261021-002

## Idea

将现有 RuoYi 前端替换为“红魔”品牌。用户已批准如下范围：品牌全称“红魔业务工作台”、短名“红魔”，统一现有登录页、注册页标题、侧栏折叠/展开标识和浏览器标题；替换现有首页的上游推广内容，介绍真实已有的供应商及采购单管理等能力，不展示编造统计或品牌厂商宣传数据；登录表单初始账号与口令均为空，不复制任何口令到新代码、规格或测试。沿用现有布局和主题，保留上游署名及许可证，保留当前登录/验证码/第三方登录/动态权限菜单/退出等既有行为。仅改已有前端可变区，品牌文案集中维护，拆出登录展示部分使所有本次修改文件不超过500行、函数不超过50行，不改 .env、后端、数据库 schema、API 签名、构建清单、核心依赖或受保护验收工具。对需修改的既有代码先做特征化，验收独立验证品牌一致、首页替换、空口令预填及登录回归，实际证明 RED 后再实现并验证 GREEN、静态检查和系统冒烟。新代码使用现有依赖与安全 Vue 插值。通过 StoryLoop 完整闭环积累一个真实已有目录修改样本，并保留所有停点、修复与实际验证边界。品牌及上述范围均已获得用户明确批准，不再就品牌提问。

## Revision of FEAT-20261021-001

- Problem: -
- Requested change: 协调者修正合同测试命令与真实清单一致，并明确保留既有动态标题开关语义；业务范围与用户选择不变。
- Why it is a contract defect: 一致性审查已指出不存在的 .py 验收路径、spec归属和标题开关例外未写清；首轮锁定特征化测试又导致lint失败且无已锁定测试修复通道。保留首轮失败与原实现，重新从未实现源码经过完整门禁，不放宽测试或修改锁。

## Product revisions

- none

## Clarifications

- none

## Answers to agent questions

- none

## Manual acceptance

- none

## Resets

- none

## Smoke suite repairs

- 2026-10-21T10:22:39+00:00 (a7a149608): 协调者独立核对旧源码上的两处测试缺陷：A12 只匹配百分号编码 /login?redirect=%2Findex，实际 Vue Router 返回语义相同的 /login?redirect=/index，应解析URL并核对pathname和searchParams.get(redirect)==/index；A13 把 /auth/code 读取成 code.data.captchaEnabled，现有响应和登录页取 captchaEnabled 顶层，应按真实响应验证且保留验证码框不存在的 UI 断言。其余品牌和回归判据保持，不改业务源码，重新从合同提交证明品牌9项RED且回归8项GREEN。
- 2026-10-21T10:28:53+00:00 (cddacee5b): 第1次修复后旧源码回归7/8，A12已通过，A13仍undefined。协调者先前顶层字段假设错误：已核实公开 CaptchaController.java:130-133 返回 R.ok(new CaptchaVo(false,null,null))，R的数据位于data；现有 login.vue:213-216 解构res.data，第一轮001无双导航helper的 code.data.captchaEnabled 曾通过。请恢复A13对code.data.captchaEnabled的精确false断言，并排查 redmagic_support.ts openAuthPage：clearStorage先goto触发第一轮验证码请求，随后立即reload，而waitForResponse可能捕获旧请求；response.json().catch(()=>({}))又吞掉解析失败。应确保旧请求已完成后才清存储并监听新reload，精确匹配GET验证码接口，等待新响应完成并检查成功状态和包裹结构，不吞异常，不输出响应全文、uuid、img或任何凭证。可使用现有Playwright在scratch复现，仅修验收helper/断言，保留品牌9项和回归8项，重新证明品牌RED且全部回归GREEN。
- 2026-10-21T10:34:01+00:00 (d0b8abc6e): 第2次修复已使A13通过，但旧代码回归A10在logout后再次openAuthPage时报 response.json: Protocol error (Network.getResponseBody): No resource with given identifier found；原生7通过/1失败。位置redmagic_login_regression.spec.ts:35，即logout之后立即再次goto/login；logout helper只等URL，旧登录页已触发验证码请求但未消费，新navigateAuthPage监听到了旧请求，页面跳转后响应体失效。需要在每一次安装新导航响应监听前先消费/排空上次页面请求，适合此smoke档（消息推送已关闭）的最小修复是在navigateAuthPage开始处 await page.waitForLoadState(networkidle,timeout30000)，确保logout后既有请求结束，再开始waitForResponse+navigate。也可采用可证明绑定新文档的请求机制，但不要固定sleep/重试吞ProtocolError/删除data断言。保留全部品牌9项、回归8项、记住用户名且密码为空、HTTP业务结构校验，重新从合同提交验证品牌RED和回归全GREEN。
- 2026-10-21T10:39:12+00:00 (61a81859f): 第3次修复后A10仍同样的 Network.getResponseBody No resource with given identifier found；A13保持通过。已用无凭证本地最小页面实测：SPA触发400ms旧请求后 waitForLoadState(networkidle)等待0ms，旧生命周期使该等待不可靠。进一步最小复现先 goto(about:blank) 完成旧文档销毁，再注册精确GET验证码waitForResponse并goto目标登录页；连续10轮均只捕获fresh请求，stale_response_matches=0。请据此替换navigateAuthPage里无效的networkidle等待为显式新文档隔离：监听前 await page.goto(about:blank)。注意openAuthPage清存储分支原callback是page.reload()，隔离后会刷新blank而超时，必须改成page.goto(route)，使每次都是明确目标路由导航；保留原helper对外签名。该过程保留同一浏览器context的localStorage，clearStorage=false绝不清除记住的账号，true仍在已有登录页origin明确清除存储。保留响应完成/HTTP/业务码/data布尔校验以及所有9品牌/8回归断言，不吞异常/不重试/不固定sleep/不修改业务源码。重新从合同提交验证品牌RED、回归全GREEN。

## Overruled attributions

- none
