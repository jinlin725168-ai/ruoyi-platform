"""StoryLoop `check_commands` entry for ruoyi-platform: frontend lint and type check in the scratch copy.

    python3 acceptance/tools/frontend_check.py

StoryLoop runs check commands in an isolated candidate copy that has no node_modules, so the
check mirrors the candidate into the same persistent scratch the smoke stack uses (where
pnpm install has been run once) and runs `oxlint src` and `vue-tsc --noEmit` there (type errors count only in business files). Exit code: 0 clean,
1 type errors, 2 environment error (no node_modules, sync failure).
"""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_harness import env_error, sync_scratch  # noqa: E402

SCRATCH_NAME = "ruoyi-smoke"  # shared with ruoyi_smoke.py so the installed node_modules is reused


def main() -> int:
    root = Path.cwd().resolve()
    try:
        scratch = sync_scratch(root, SCRATCH_NAME)
    except Exception as exc:  # noqa: BLE001
        return env_error(f"scratch sync failed: {exc}")
    frontend = scratch / "frontend"
    binaries = frontend / "node_modules/.bin"
    for tool in ("oxlint", "vue-tsc"):
        if not (binaries / tool).is_file():
            return env_error(f"{binaries / tool} missing: run `pnpm install` in {frontend} once")
    failed = subprocess.run([str(binaries / "oxlint"), "src"], cwd=frontend).returncode != 0
    if _restore_declarations(scratch, frontend):
        failed = _type_check_business_files(binaries / "vue-tsc", frontend) or failed
    else:
        print("frontend_check: vue-tsc skipped, no auto-import declarations yet (they appear after the first "
              "smoke run starts vite)", file=sys.stderr)
    return 1 if failed else 0


BUSINESS = re.compile(r"^src/(views|api)/biz/|\.test\.ts\(")


def _type_check_business_files(vue_tsc: Path, frontend: Path) -> bool:
    """vue-tsc over the whole app, but only errors in business files fail: upstream plus-ui does not
    pass vue-tsc itself and is not ours to fix. Upstream errors are reported as a count."""
    result = subprocess.run([str(vue_tsc), "--noEmit", "--pretty", "false"], cwd=frontend,
                            capture_output=True, text=True)
    errors = [line for line in (result.stdout + result.stderr).splitlines() if "error TS" in line]
    ours = [line for line in errors if BUSINESS.match(line)]
    for line in ours:
        print(line, file=sys.stderr)
    upstream = len(errors) - len(ours)
    print(f"frontend_check: vue-tsc {len(ours)} error(s) in business files, {upstream} in upstream files (not a gate)",
          file=sys.stderr)
    return bool(ours)


def _restore_declarations(scratch: Path, frontend: Path) -> bool:
    """unplugin's *.d.ts are Git-ignored; the smoke stack keeps a copy under scratch/smoke-dts."""
    types = frontend / "src/types"
    if any(types.glob("auto-imports.d.ts")):
        return True
    kept = scratch / "smoke-dts"
    if not kept.is_dir():
        return False
    types.mkdir(parents=True, exist_ok=True)
    for declaration in kept.glob("*.d.ts"):
        shutil.copy2(declaration, types / declaration.name)
    return True


if __name__ == "__main__":
    sys.exit(main())
