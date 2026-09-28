"""StoryLoop `unit_commands` entry for ruoyi-platform: frontend unit tests (vitest) in the scratch copy.

    python3 acceptance/tools/frontend_unit.py             # StoryLoop unit layer: sync to scratch first
    python3 acceptance/tools/frontend_unit.py --in-place  # CI: node_modules already installed in the checkout

StoryLoop runs unit commands in an isolated candidate copy without node_modules, so the tool
mirrors the candidate into the persistent scratch the smoke stack uses (pnpm install done once
there) and runs `vitest run` on `frontend/src/**/*.test.ts`. Exit code: 0 green, 1 test failures,
2 environment error (no node_modules, sync failure). `--passWithNoTests` keeps a frontend without
unit tests green: the layer is a gate on what exists, not a demand that tests exist.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Callable

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_harness import env_error, sync_scratch  # noqa: E402

SCRATCH_NAME = "ruoyi-smoke"  # shared with ruoyi_smoke.py / frontend_check.py so node_modules is reused


def resolve_frontend(root: Path, in_place: bool, sync: Callable[[Path, str], Path] = sync_scratch) -> Path:
    """Where vitest runs: the checkout itself in CI, otherwise the synced scratch copy."""
    if in_place:
        return root / "frontend"
    return sync(root, SCRATCH_NAME) / "frontend"


def run_vitest(frontend: Path) -> int:
    vitest = frontend / "node_modules/.bin/vitest"
    if not vitest.is_file():
        return env_error(f"{vitest} missing: run `pnpm install` in {frontend} once")
    result = subprocess.run([str(vitest), "run", "--passWithNoTests", "--reporter=dot"], cwd=frontend)
    return 0 if result.returncode == 0 else 1


def main() -> int:
    root = Path.cwd().resolve()
    in_place = "--in-place" in sys.argv[1:]
    try:
        frontend = resolve_frontend(root, in_place)
    except Exception as exc:  # noqa: BLE001
        return env_error(f"scratch sync failed: {exc}")
    return run_vitest(frontend)


if __name__ == "__main__":
    sys.exit(main())
