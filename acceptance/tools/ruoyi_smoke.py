"""StoryLoop smoke executor for ruoyi-platform: build, boot a throwaway backend, run cases.

Invoked from the repository root (a StoryLoop candidate copy or a developer checkout):

    python3 acceptance/tools/ruoyi_smoke.py acceptance/smoke/<change-id>/test_*.py [x.spec.ts ...]

Generic mechanics (scratch sync, case runner, readiness polling, process cleanup, exit codes)
come from smoke_harness.py, a vendored copy of storyloop/examples/tools/smoke_harness.py.
RuoYi-specific steps:
 1. `mvn -o package` the backend in the scratch copy.
 2. Create a temporary MySQL database in the local docker container; import the base scripts
    from backend/script/sql, then every sql/biz/*.sql in name order.
 3. Start ruoyi-admin.jar with profiles dev,smoke on a free port against that database and a
    dedicated Redis database index.
 4. Run *.py cases with unittest; for *.spec.ts cases start vite (proxy -> throwaway backend)
    and run Playwright.
 5. Stop everything and drop the database.

Exit codes follow the StoryLoop contract: 0 pass, 1 behavioural failure, 2 environment error.
Only PATH and TMP are guaranteed in the environment; mvn, java, docker (and pnpm, node for UI
cases) must be on PATH.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True  # never leave __pycache__ in a candidate copy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_harness import (  # noqa: E402
    env_error, free_port, run_python_cases, split_cases, stop, sync_scratch, wait_http,
)

BASE_SQL = ["ry_vue.sql", "ry_workflow.sql"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", nargs="+", help="case files relative to the repo root")
    parser.add_argument("--mysql-container", default="ruoyi-mysql")
    parser.add_argument("--mysql-user", default="root")
    parser.add_argument("--mysql-password", default="root")
    parser.add_argument("--mysql-host-port", type=int, default=3307)
    parser.add_argument("--redis-db", type=int, default=15)
    parser.add_argument("--boot-timeout", type=int, default=180)
    parser.add_argument("--scratch", default="ruoyi-smoke", help="persistent scratch dir name")
    args = parser.parse_args()

    root = Path.cwd()
    if not (root / "backend/pom.xml").is_file():
        return env_error("run from the repository root (backend/pom.xml not found)")
    try:
        groups = split_cases(args.cases, root, (".py", ".spec.ts"))
    except ValueError as exc:
        return env_error(str(exc))
    py_cases, specs = groups[".py"], groups[".spec.ts"]
    for tool in ("mvn", "java", "docker") + (("pnpm", "node") if specs else ()):
        if not shutil.which(tool):
            return env_error(f"{tool} is not on PATH")

    try:
        scratch = sync_scratch(root, args.scratch)
    except (OSError, subprocess.CalledProcessError) as exc:
        return env_error(f"scratch sync failed: {exc}")
    log = scratch / "smoke-build.log"
    with log.open("w", encoding="utf-8") as handle:
        build = subprocess.run(
            ["mvn", "-q", "-o", "-f", "backend/pom.xml", "-DskipTests", "-pl", "ruoyi-admin",
             "-am", "package"], cwd=scratch, stdout=handle, stderr=subprocess.STDOUT)
    if build.returncode != 0:
        return env_error("backend build failed", log)
    jar = scratch / "backend/ruoyi-admin/target/ruoyi-admin.jar"
    if not jar.is_file():
        return env_error("ruoyi-admin.jar not produced", log)

    database = f"ry_smoke_{os.getpid()}"
    mysql = _Mysql(args.mysql_container, args.mysql_user, args.mysql_password)
    try:
        mysql.run(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        for name in BASE_SQL:
            mysql.import_file(database, root / "backend/script/sql" / name)
        for path in sorted((root / "sql/biz").glob("*.sql")):
            mysql.import_file(database, path)
    except subprocess.CalledProcessError as exc:
        mysql.drop(database)
        return env_error(f"database setup failed: {exc.stderr.decode('utf-8', 'replace')[-2000:]}")

    port = free_port()
    url = (f"jdbc:mysql://localhost:{args.mysql_host_port}/{database}?useUnicode=true&characterEncoding=utf8"
           "&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&autoReconnect=true"
           "&rewriteBatchedStatements=true&allowPublicKeyRetrieval=true&nullCatalogMeansCurrent=true")
    server_log = scratch / "smoke-server.log"
    server = subprocess.Popen(
        ["java", "-jar", str(jar), "--spring.profiles.active=dev,smoke", f"--server.port={port}",
         f"--spring.datasource.dynamic.datasource.master.url={url}",
         f"--spring.data.redis.database={args.redis_db}"],
        cwd=scratch, stdout=server_log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
        start_new_session=True)
    try:
        if not wait_http(server, f"http://127.0.0.1:{port}/auth/tenant/list", args.boot_timeout):
            return env_error("backend did not become ready", server_log)
        env = {"SMOKE_BASE_URL": f"http://127.0.0.1:{port}",
               "PYTHONPATH": str(root / "acceptance/tools"), "CI": "1"}
        failed = False
        if py_cases:
            failed = run_python_cases(py_cases, cwd=root, env=env) != 0
        if specs:
            outcome = _run_ui(scratch, specs, port, env, args.boot_timeout)
            if outcome == 2:
                return 2
            failed = failed or outcome != 0
        return 1 if failed else 0
    finally:
        stop(server)
        mysql.drop(database)


def _run_ui(scratch: Path, specs: list[str], backend_port: int, env: dict, timeout: int) -> int:
    """Serve the scratch frontend with vite and run the Playwright specs against it."""
    frontend = scratch / "frontend"
    full_env = dict(os.environ)
    full_env.update(env)
    log = scratch / "smoke-frontend.log"
    with log.open("w", encoding="utf-8") as handle:
        install = subprocess.run(["pnpm", "install", "--offline", "--frozen-lockfile"], cwd=frontend,
                                 stdout=handle, stderr=subprocess.STDOUT, env=full_env)
    if install.returncode != 0:
        return env_error("frontend dependency install failed", log)
    link = scratch / "node_modules"
    if not link.exists():
        link.symlink_to(frontend / "node_modules", target_is_directory=True)
    ui_port = free_port()
    ui_env = dict(full_env)
    ui_env.update({"VITE_PROXY_TARGET": f"http://127.0.0.1:{backend_port}", "VITE_APP_ENCRYPT": "false",
                   "VITE_APP_MESSAGE_ENABLED": "false"})
    vite_log = scratch / "smoke-vite.log"
    vite = subprocess.Popen(
        [str(frontend / "node_modules/.bin/vite"), "--mode", "development", "--host", "127.0.0.1",
         "--port", str(ui_port), "--strictPort"],
        cwd=frontend, stdout=vite_log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
        env=ui_env, start_new_session=True)
    try:
        if not wait_http(vite, f"http://127.0.0.1:{ui_port}/", timeout):
            return env_error("vite dev server did not become ready", vite_log)
        output = scratch / "smoke-ui-output"
        shutil.rmtree(output, ignore_errors=True)
        pw_env = dict(ui_env)
        pw_env.update({"SMOKE_UI_URL": f"http://127.0.0.1:{ui_port}", "SMOKE_OUTPUT_DIR": str(output)})
        result = subprocess.run(
            [str(frontend / "node_modules/.bin/playwright"), "test", "-c",
             "acceptance/tools/playwright.config.ts", *specs], cwd=scratch, env=pw_env)
        return 0 if result.returncode == 0 else 1
    finally:
        stop(vite)


class _Mysql:
    def __init__(self, container: str, user: str, password: str):
        self.base = ["docker", "exec", "-i", container, "mysql", "--default-character-set=utf8mb4",
                     f"-u{user}", f"-p{password}"]

    def run(self, statement: str, database: str | None = None) -> None:
        command = self.base + ([database] if database else []) + ["-e", statement]
        subprocess.run(command, check=True, capture_output=True)

    def import_file(self, database: str, path: Path) -> None:
        with path.open("rb") as handle:
            subprocess.run(self.base + [database], stdin=handle, check=True, capture_output=True)

    def drop(self, database: str) -> None:
        try:
            self.run(f"DROP DATABASE IF EXISTS `{database}`")
        except subprocess.CalledProcessError:
            print(f"warning: could not drop {database}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
