"""StoryLoop smoke executor for ruoyi-platform: build, boot a throwaway backend, run cases.

Invoked from the repository root (a StoryLoop candidate copy or a developer checkout):

    python3 acceptance/tools/ruoyi_smoke.py acceptance/smoke/<change-id>/test_*.py

Steps
 1. Sync Git-visible files into a persistent scratch directory (never builds in place, because
    StoryLoop forbids ignored files such as target/ from appearing in the candidate).
 2. `mvn -o package` the backend there (incremental after the first run).
 3. Create a temporary MySQL database in the local docker container, import the base scripts from
    backend/script/sql and then every sql/biz/*.sql in name order.
 4. Start ruoyi-admin.jar with profiles dev,smoke on a free port against that database and a
    dedicated Redis database index, wait until /auth/login answers.
 5. Run *.py case files with unittest (PYTHONPATH includes acceptance/tools, SMOKE_BASE_URL set).
 6. If *.spec.ts files are given: `pnpm install --offline` in the scratch frontend, start `vite`
    with the proxy pointed at the throwaway backend, run Playwright with SMOKE_UI_URL set.
 7. Stop everything and drop the database.

Exit codes follow the StoryLoop contract: 0 pass, 1 behavioural failure, 2 environment error.
Only PATH and TMP are guaranteed in the environment; mvn, java and docker must be on PATH.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BASE_SQL = ["ry_vue.sql", "ry_workflow.sql"]
BUILD_OUTPUT = {"target", "node_modules", "dist", "logs"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", nargs="+", help="unittest case files relative to the repo root")
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
        return _env_error("run from the repository root (backend/pom.xml not found)")
    for case in args.cases:
        if not (root / case).is_file():
            return _env_error(f"case file not found: {case}")
    specs = [case for case in args.cases if case.endswith(".spec.ts")]
    py_cases = [case for case in args.cases if case.endswith(".py")]
    if len(specs) + len(py_cases) != len(args.cases):
        return _env_error("cases must be *.py (unittest) or *.spec.ts (Playwright)")
    for tool in ("mvn", "java", "docker") + (("pnpm", "node") if specs else ()):
        if not shutil.which(tool):
            return _env_error(f"{tool} is not on PATH")

    scratch = Path(tempfile.gettempdir()) / f"storyloop-{args.scratch}"
    try:
        _sync(root, scratch)
    except (OSError, subprocess.CalledProcessError) as exc:
        return _env_error(f"scratch sync failed: {exc}")
    log = scratch / "smoke-build.log"
    with log.open("w", encoding="utf-8") as handle:
        build = subprocess.run(
            ["mvn", "-q", "-o", "-f", "backend/pom.xml", "-DskipTests", "-pl", "ruoyi-admin",
             "-am", "package"], cwd=scratch, stdout=handle, stderr=subprocess.STDOUT)
    if build.returncode != 0:
        return _env_error("backend build failed", log)
    jar = scratch / "backend/ruoyi-admin/target/ruoyi-admin.jar"
    if not jar.is_file():
        return _env_error("ruoyi-admin.jar not produced", log)

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
        return _env_error(f"database setup failed: {exc.stderr.decode('utf-8', 'replace')[-2000:]}")

    port = _free_port()
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
        if not _wait_ready(server, port, args.boot_timeout):
            return _env_error("backend did not become ready", server_log)
        env = dict(os.environ)
        env.update({"SMOKE_BASE_URL": f"http://127.0.0.1:{port}", "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(root / "acceptance/tools"), "CI": "1"})
        failed = False
        if py_cases:
            result = subprocess.run([sys.executable, "-B", "-c", RUNNER, *py_cases], cwd=root, env=env)
            failed = failed or result.returncode != 0
        if specs:
            outcome = _run_ui(scratch, specs, port, env, args.boot_timeout)
            if outcome == 2:
                return 2
            failed = failed or outcome != 0
        return 1 if failed else 0
    finally:
        _stop(server)
        mysql.drop(database)


def _run_ui(scratch: Path, specs: list[str], backend_port: int, env: dict, timeout: int) -> int:
    """Serve the scratch frontend with vite and run the Playwright specs against it."""
    frontend = scratch / "frontend"
    log = scratch / "smoke-frontend.log"
    with log.open("w", encoding="utf-8") as handle:
        install = subprocess.run(["pnpm", "install", "--offline", "--frozen-lockfile"], cwd=frontend,
                                 stdout=handle, stderr=subprocess.STDOUT, env=env)
    if install.returncode != 0:
        return _env_error("frontend dependency install failed", log)
    link = scratch / "node_modules"
    if not link.exists():
        link.symlink_to(frontend / "node_modules", target_is_directory=True)
    ui_port = _free_port()
    ui_env = dict(env)
    ui_env.update({"VITE_PROXY_TARGET": f"http://127.0.0.1:{backend_port}", "VITE_APP_ENCRYPT": "false",
                   "VITE_APP_MESSAGE_ENABLED": "false"})
    vite_log = scratch / "smoke-vite.log"
    vite = subprocess.Popen(
        [str(frontend / "node_modules/.bin/vite"), "--mode", "development", "--host", "127.0.0.1",
         "--port", str(ui_port), "--strictPort"],
        cwd=frontend, stdout=vite_log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
        env=ui_env, start_new_session=True)
    try:
        if not _wait_http(vite, f"http://127.0.0.1:{ui_port}/", timeout):
            return _env_error("vite dev server did not become ready", vite_log)
        output = scratch / "smoke-ui-output"
        shutil.rmtree(output, ignore_errors=True)
        pw_env = dict(ui_env)
        pw_env.update({"SMOKE_UI_URL": f"http://127.0.0.1:{ui_port}", "SMOKE_OUTPUT_DIR": str(output)})
        result = subprocess.run(
            [str(frontend / "node_modules/.bin/playwright"), "test", "-c",
             "acceptance/tools/playwright.config.ts", *specs], cwd=scratch, env=pw_env)
        return 0 if result.returncode == 0 else 1
    finally:
        _stop(vite)


# Case files live under acceptance/smoke/<change-id>/ whose name contains hyphens, so they are
# loaded by path instead of by dotted module name.
RUNNER = """
import importlib.util, sys, unittest
suite = unittest.TestSuite()
for path in sys.argv[1:]:
    spec = importlib.util.spec_from_file_location(path.replace('/', '_').replace('-', '_')[:-3], path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() and result.testsRun > 0 else 1)
"""


def _sync(root: Path, target: Path) -> None:
    wanted = _visible_files(root)
    keep = set(wanted)
    if target.exists():
        for directory, names, files in os.walk(target):
            names[:] = [name for name in names
                        if name not in BUILD_OUTPUT and not Path(directory, name).is_symlink()]
            for name in files:
                relative = Path(directory, name).relative_to(target).as_posix()
                if relative not in keep and not _is_build_output(relative):
                    Path(directory, name).unlink()
    for relative in wanted:
        source, dest = root / relative, target / relative
        if dest.exists() and dest.stat().st_size == source.stat().st_size \
                and dest.stat().st_mtime >= source.stat().st_mtime:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def _visible_files(root: Path) -> list[str]:
    if (root / ".git").exists():
        output = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=root,
                                capture_output=True, check=True).stdout
        return sorted(set(filter(None, output.decode("utf-8").split("\0"))))
    files = []
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_file() and not relative.startswith(".storyloop/") and not _is_build_output(relative):
            files.append(relative)
    return sorted(files)


def _is_build_output(relative: str) -> bool:
    parts = relative.split("/")
    return any(part in BUILD_OUTPUT or part.endswith(".flattened-pom.xml") for part in parts) \
        or relative.startswith("smoke-")


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


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_ready(server: subprocess.Popen, port: int, timeout: int) -> bool:
    return _wait_http(server, f"http://127.0.0.1:{port}/auth/tenant/list", timeout)


def _wait_http(process: subprocess.Popen, url: str, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=3):
                return True
        except urllib.error.HTTPError:
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    return False


def _stop(server: subprocess.Popen) -> None:
    if server.poll() is None:
        try:
            os.killpg(server.pid, signal.SIGTERM)
            server.wait(timeout=30)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            os.killpg(server.pid, signal.SIGKILL)
            server.wait(timeout=10)


def _env_error(message: str, log: Path | None = None) -> int:
    print(f"ruoyi_smoke: {message}", file=sys.stderr)
    if log and log.is_file():
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
        print("\n".join(lines), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
