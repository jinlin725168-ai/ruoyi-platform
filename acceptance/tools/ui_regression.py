"""StoryLoop `ui_regression` generator for ruoyi-platform: Playwright Test Agents over the smoke stack.

Configured in .storyloop/config.json:
    "ui_regression": {"command": ["{python}", "acceptance/tools/ui_regression.py"], "timeout_seconds": 3600}

stdin  : storyloop.ui-regression.v1 request (change_id, capability, suite_root, goal, stories)
stdout : {"files": [{"path": "plan.md", ...}, {"path": "<scenario>.spec.ts", ...}]}

Flow: build + boot the throwaway stack (Stack from ruoyi_smoke.py) -> planner explores the live
app and saves plan.md (skipped when acceptance/ui/<capability>/plan.md already exists) ->
generator writes one spec per planned scenario (bounded by --max-scenarios) against the live
app -> healer verifies and repairs those generated specs only -> specs that pass are returned.
Nothing here touches the project workspace; StoryLoop places the returned files.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ruoyi_smoke import Stack  # noqa: E402

AGENTS = Path(__file__).resolve().parent / "playwright-agents"
LOGIN = "登录页 /login，账号 admin，密码 admin123，验证码已关闭（登录表单没有验证码框）。"
RELATIVE_URLS = ("测试里所有 page.goto 必须用相对路径（例如 page.goto('/login')），baseURL 由配置提供，"
                 "不要写死主机和端口。每个测试自己登录并自己准备数据，编码和名称加时间戳后缀。")
SCENARIO = re.compile(r"^#### (\d+\.\d+)\. (.+?)\s*$", re.M)
FILE = re.compile(r"\*\*File:\*\* `([^`]+)`")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-scenarios", type=int, default=3, help="generator runs per change")
    parser.add_argument("--segment-turns", type=int, default=80)
    args = parser.parse_args()
    request = json.load(sys.stdin)
    payload = request["payload"]
    root = Path(request["project"]).resolve()
    capability = payload["capability"]
    existing = root / "acceptance" / "ui" / capability
    for tool in ("claude", "npx", "pnpm", "mvn", "java", "docker"):
        if not shutil.which(tool):
            return _fail(f"{tool} is not on PATH")

    stack = Stack(root, scratch_name="ruoyi-ui-regression")
    try:
        code = stack.build() or stack.start_backend() or stack.start_frontend()
        if code:
            return code
        workspace = _agent_workspace(stack.scratch / "frontend", existing)
        base_url = f"http://127.0.0.1:{stack.ui_port}"
        plan_path = workspace / "specs" / "plan.md"
        if not plan_path.is_file():
            outcome = _planner(workspace, base_url, payload, args)
            if outcome:
                return outcome
        plan = plan_path.read_text(encoding="utf-8")
        scenarios = _scenarios(plan)
        done = {p.name for p in existing.glob("*.spec.ts")} if existing.is_dir() else set()
        todo = [s for s in scenarios if Path(s["file"]).name not in done][: args.max_scenarios]
        print(f"ui_regression: {len(scenarios)} planned, {len(done)} existing, generating {len(todo)}",
              file=sys.stderr)
        for scenario in todo:
            _generator(workspace, plan, scenario, base_url, args)
        generated = sorted((workspace / "tests").rglob("*.spec.ts"))
        generated = [p for p in generated if p.name != "seed.spec.ts"]
        if generated:
            _healer(workspace, base_url, args)
        passing = _passing(workspace, generated, base_url)
        files = [{"path": "plan.md", "content": plan}]
        files += [{"path": p.name, "content": p.read_text(encoding="utf-8")} for p in passing]
        skipped = [p.name for p in generated if p not in passing]
        if skipped:
            print(f"ui_regression: not returned (still failing): {', '.join(skipped)}", file=sys.stderr)
        print(json.dumps({"files": files}, ensure_ascii=False))
        return 0
    finally:
        stack.stop()


def _agent_workspace(frontend: Path, existing: Path) -> Path:
    """Prepare the scratch frontend as a Playwright agents workspace (config, MCP, seed, prior assets)."""
    (frontend / "playwright.config.ts").write_text(
        "import { defineConfig } from '@playwright/test';\n"
        "export default defineConfig({ testDir: '.', testMatch: ['tests/**/*.spec.ts'], outputDir: 'test-results',\n"
        "  use: { baseURL: process.env.PW_BASE_URL, headless: true }, timeout: 60_000, workers: 1,\n"
        "  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }] });\n", encoding="utf-8")
    shutil.copyfile(AGENTS / "mcp.json", frontend / ".mcp.json")
    (frontend / "tests").mkdir(exist_ok=True)
    (frontend / "specs").mkdir(exist_ok=True)
    for stale in (frontend / "tests").rglob("*.spec.ts"):
        stale.unlink()
    for stale in (frontend / "specs").glob("*.md"):
        stale.unlink()
    (frontend / "tests" / "seed.spec.ts").write_text(
        "import { test, expect } from '@playwright/test';\n\ntest.describe('Test group', () => {\n"
        "  test('seed', async ({ page }) => {\n    // generate code here.\n  });\n});\n", encoding="utf-8")
    if existing.is_dir():
        if (existing / "plan.md").is_file():
            shutil.copyfile(existing / "plan.md", frontend / "specs" / "plan.md")
    return frontend


def _claude(workspace: Path, agent: str, prompt: str, base_url: str, args, write: bool = False) -> dict:
    tools = (AGENTS / f"{agent}.tools").read_text(encoding="utf-8").strip().split(",")
    builtin = ["Read", "Grep", "Glob"] + (["Edit", "Write", "MultiEdit"] if write else [])
    command = ["claude", "-p", "--restricted", "--output-format", "json", "--permission-prompts", "none",
               "--max-turns", str(args.segment_turns), "--mcp-config", ".mcp.json", "--strict-mcp-config",
               "--append-system-prompt-file", str(AGENTS / f"{agent}.md"),
               "--tools", ",".join(builtin), "--allowedTools", *builtin, *[t for t in tools if t.startswith("mcp__")]]
    if write:
        command += ["--permission-mode", "acceptEdits"]
    env = dict(os.environ)
    env["PW_BASE_URL"] = base_url
    completed = subprocess.run(command, input=prompt, capture_output=True, text=True, cwd=workspace, env=env)
    try:
        envelope = json.loads(completed.stdout)
    except ValueError:
        envelope = {"subtype": "no-envelope", "result": completed.stderr[-1000:]}
    print(f"ui_regression/{agent}: {envelope.get('subtype')} turns={envelope.get('num_turns')} "
          f"cost={envelope.get('total_cost_usd', 0):.2f}", file=sys.stderr)
    return envelope


def _planner(workspace: Path, base_url: str, payload: dict, args) -> int:
    stories = "\n".join(f"- {s['id']} [{s.get('priority', '-')}] {s['title']}" for s in payload["stories"])
    prompt = (f"被测应用：RuoYi 后台，地址 {base_url} 。{LOGIN}\n"
              f"本次变更目标：{payload['goal']}\n用户故事：\n{stories}\n"
              "请为这些故事涉及的页面做测试规划，覆盖主路径、失败校验和取消操作。每个场景假设全新状态并自行准备数据。"
              "用 planner_save_plan 把计划保存为 specs/plan.md，用中文写，每个场景给出 **File:** `tests/<name>.spec.ts`。")
    envelope = _claude(workspace, "planner", prompt, base_url, args)
    if not (workspace / "specs" / "plan.md").is_file():
        return _fail(f"planner did not save specs/plan.md: {str(envelope.get('result'))[:300]}")
    return 0


def _scenarios(plan: str) -> list[dict]:
    result = []
    matches = list(SCENARIO.finditer(plan))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(plan)
        body = plan[match.start():end]
        file_match = FILE.search(body)
        result.append({"number": match.group(1), "title": match.group(2), "body": body,
                       "file": file_match.group(1) if file_match else f"tests/scenario-{match.group(1)}.spec.ts"})
    return result


def _generator(workspace: Path, plan: str, scenario: dict, base_url: str, args) -> None:
    head = plan[:plan.index("## Test Scenarios")] if "## Test Scenarios" in plan else ""
    group = re.search(r"^### (\d+)\. (.+?)\s*$", plan[:plan.index(scenario["body"])], re.M | re.S)
    group_line = f"### {group.group(1)}. {group.group(2)}\n\n**Seed:** `tests/seed.spec.ts`\n\n" if group else ""
    prompt = (f"请为下面这个测试计划条目生成 Playwright 测试，用 generator_write_test 写到 `{scenario['file']}`。"
              f"{RELATIVE_URLS}\n\n{head}\n## Test Scenarios\n\n{group_line}{scenario['body']}")
    _claude(workspace, "generator", prompt, base_url, args)


def _healer(workspace: Path, base_url: str, args) -> None:
    prompt = ("请用 test_run 运行 tests/ 下的所有测试，修复失败的测试。只能改 tests/ 下的测试文件，不能改应用；"
              "不要放宽断言去迁就错误行为，只修定位器、时序和数据准备。" + RELATIVE_URLS)
    _claude(workspace, "healer", prompt, base_url, args, write=True)


def _passing(workspace: Path, generated: list[Path], base_url: str) -> list[Path]:
    passing = []
    for spec in generated:
        result = subprocess.run([str(workspace / "node_modules/.bin/playwright"), "test", str(spec.relative_to(workspace)),
                                 "--reporter=line"], cwd=workspace, capture_output=True, text=True,
                                env={**os.environ, "PW_BASE_URL": base_url})
        (passing if result.returncode == 0 else []).append(spec)
    return passing


def _fail(message: str) -> int:
    print(f"ui_regression: {message}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
