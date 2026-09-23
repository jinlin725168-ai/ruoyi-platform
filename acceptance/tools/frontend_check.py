"""StoryLoop `check_commands` entry for ruoyi-platform: frontend lint and type check in the scratch copy.

    python3 acceptance/tools/frontend_check.py

StoryLoop runs check commands in an isolated candidate copy that has no node_modules, so the
check mirrors the candidate into the same persistent scratch the smoke stack uses (where
pnpm install has been run once) and runs `oxlint src` and `vue-tsc --noEmit` there. Exit code: 0 clean,
1 type errors, 2 environment error (no node_modules, sync failure).
"""

from __future__ import annotations

from pathlib import Path
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
        failed = subprocess.run([str(binaries / "vue-tsc"), "--noEmit"], cwd=frontend).returncode != 0 or failed
    else:
        print("frontend_check: vue-tsc skipped, no auto-import declarations yet (they appear after the first "
              "smoke run starts vite)", file=sys.stderr)
    return 1 if failed else 0


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
