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


class Stack:
    """Build the candidate in scratch, boot a throwaway backend (and optionally vite); reusable."""

    def __init__(self, root: Path, scratch_name: str = "ruoyi-smoke", mysql_container: str = "ruoyi-mysql",
                 mysql_user: str = "root", mysql_password: str = "root", mysql_host_port: int = 3307,
                 redis_db: int = 15, boot_timeout: int = 180):
        self.root, self.scratch_name, self.boot_timeout = root, scratch_name, boot_timeout
        self.mysql = _Mysql(mysql_container, mysql_user, mysql_password)
        self.mysql_host_port, self.redis_db = mysql_host_port, redis_db
        self.scratch: Path | None = None
        self.database: str | None = None
        self.server = self.vite = None
        self.port = self.ui_port = None

    def build(self) -> int | None:
        """Sync + package; returns an exit code on environment failure, else None."""
        try:
            self.scratch = sync_scratch(self.root, self.scratch_name)
        except (OSError, subprocess.CalledProcessError) as exc:
            return env_error(f"scratch sync failed: {exc}")
        log = self.scratch / "smoke-build.log"
        with log.open("w", encoding="utf-8") as handle:
            build = subprocess.run(
                ["mvn", "-q", "-o", "-f", "backend/pom.xml", "-DskipTests", "-pl", "ruoyi-admin",
                 "-am", "package"], cwd=self.scratch, stdout=handle, stderr=subprocess.STDOUT)
        if build.returncode != 0:
            return env_error("backend build failed", log)
        if not (self.scratch / "backend/ruoyi-admin/target/ruoyi-admin.jar").is_file():
            return env_error("ruoyi-admin.jar not produced", log)
        return None

    def start_backend(self) -> int | None:
        self.database = f"ry_smoke_{os.getpid()}"
        try:
            self.mysql.run(f"CREATE DATABASE `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
            for name in BASE_SQL:
                self.mysql.import_file(self.database, self.root / "backend/script/sql" / name)
            for path in sorted((self.root / "sql/biz").glob("*.sql")):
                self.mysql.import_file(self.database, path)
        except subprocess.CalledProcessError as exc:
            self.mysql.drop(self.database)
            return env_error(f"database setup failed: {exc.stderr.decode('utf-8', 'replace')[-2000:]}")
        self.port = free_port()
        url = (f"jdbc:mysql://localhost:{self.mysql_host_port}/{self.database}?useUnicode=true&characterEncoding=utf8"
               "&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&autoReconnect=true"
               "&rewriteBatchedStatements=true&allowPublicKeyRetrieval=true&nullCatalogMeansCurrent=true")
        log = self.scratch / "smoke-server.log"
        self.server = subprocess.Popen(
            ["java", "-jar", str(self.scratch / "backend/ruoyi-admin/target/ruoyi-admin.jar"),
             "--spring.profiles.active=dev,smoke", f"--server.port={self.port}",
             f"--spring.datasource.dynamic.datasource.master.url={url}",
             f"--spring.data.redis.database={self.redis_db}"],
            cwd=self.scratch, stdout=log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
            start_new_session=True)
        if not wait_http(self.server, f"http://127.0.0.1:{self.port}/auth/tenant/list", self.boot_timeout):
            return env_error("backend did not become ready", log)
        return None

    def start_frontend(self) -> int | None:
        frontend = self.scratch / "frontend"
        env = dict(os.environ)
        env["CI"] = "1"
        log = self.scratch / "smoke-frontend.log"
        with log.open("w", encoding="utf-8") as handle:
            install = subprocess.run(["pnpm", "install", "--offline", "--frozen-lockfile"], cwd=frontend,
                                     stdout=handle, stderr=subprocess.STDOUT, env=env)
        if install.returncode != 0:
            return env_error("frontend dependency install failed", log)
        link = self.scratch / "node_modules"
        if not link.exists():
            link.symlink_to(frontend / "node_modules", target_is_directory=True)
        self.ui_port = free_port()
        env.update({"VITE_PROXY_TARGET": f"http://127.0.0.1:{self.port}", "VITE_APP_ENCRYPT": "false",
                    "VITE_APP_MESSAGE_ENABLED": "false"})
        vite_log = self.scratch / "smoke-vite.log"
        self.vite = subprocess.Popen(
            [str(frontend / "node_modules/.bin/vite"), "--mode", "development", "--host", "127.0.0.1",
             "--port", str(self.ui_port), "--strictPort"],
            cwd=frontend, stdout=vite_log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
            env=env, start_new_session=True)
        if not wait_http(self.vite, f"http://127.0.0.1:{self.ui_port}/", self.boot_timeout):
            return env_error("vite dev server did not become ready", vite_log)
        # unplugin writes the auto-import declarations on start; keep a copy that survives the
        # scratch sync (smoke-* is treated as build output) so frontend_check.py can type-check.
        keep = self.scratch / "smoke-dts"
        keep.mkdir(exist_ok=True)
        for declaration in (frontend / "src/types").glob("*.d.ts"):
            shutil.copy2(declaration, keep / declaration.name)
        return None

    def stop(self) -> None:
        for process in (self.vite, self.server):
            if process is not None:
                stop(process)
        if self.database:
            self.mysql.drop(self.database)


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

    stack = Stack(root, args.scratch, args.mysql_container, args.mysql_user, args.mysql_password,
                  args.mysql_host_port, args.redis_db, args.boot_timeout)
    try:
        code = stack.build() or stack.start_backend()
        if code:
            return code
        env = {"SMOKE_BASE_URL": f"http://127.0.0.1:{stack.port}",
               "PYTHONPATH": str(root / "acceptance/tools"), "CI": "1"}
        failed = False
        if py_cases:
            failed = run_python_cases(py_cases, cwd=root, env=env) != 0
        if specs:
            code = stack.start_frontend()
            if code:
                return code
            # Only the change's own specs run here; acceptance/ui/** regression assets are
            # documentation and on-demand regression, never part of the smoke gate.
            outcome = run_playwright(stack, specs, env)
            failed = failed or outcome != 0
        return 1 if failed else 0
    finally:
        stack.stop()


def run_playwright(stack: Stack, specs: list[str], env: dict) -> int:
    """Run Playwright specs in the scratch copy against the stack's vite server."""
    output = stack.scratch / "smoke-ui-output"
    shutil.rmtree(output, ignore_errors=True)
    pw_env = dict(os.environ)
    pw_env.update(env)
    pw_env.update({"SMOKE_UI_URL": f"http://127.0.0.1:{stack.ui_port}", "SMOKE_OUTPUT_DIR": str(output)})
    result = subprocess.run(
        [str(stack.scratch / "frontend/node_modules/.bin/playwright"), "test", "-c",
         "acceptance/tools/playwright.config.ts", *specs], cwd=stack.scratch, env=pw_env)
    return 0 if result.returncode == 0 else 1


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
