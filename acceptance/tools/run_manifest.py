"""Run every command of a StoryLoop manifest from the repository root (CI entry, no engine needed).

    python3 acceptance/tools/run_manifest.py acceptance/smoke/manifest.json
    python3 acceptance/tools/run_manifest.py acceptance/changes/FEAT-20260923-002/manifest.json

The manifest is the same file the StoryLoop loop protects; `{python}` expands to this
interpreter. Exit code 0 when every command passed, 1 on any failure.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    manifest_path = Path(argv[0])
    root = Path.cwd().resolve()
    tests = json.loads(manifest_path.read_text(encoding="utf-8"))["tests"]
    failed = []
    for test in tests:
        command = [sys.executable if arg == "{python}" else arg for arg in test["command"]]
        started = time.time()
        print(f"== {test['id']}: {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=root, timeout=int(test.get("timeout_seconds", 3600)))
        print(f"== {test['id']}: exit {result.returncode} in {time.time() - started:.0f}s", flush=True)
        if result.returncode != 0:
            failed.append(test["id"])
    if failed:
        print("FAILED: " + ", ".join(failed), file=sys.stderr)
        return 1
    print(f"PASSED: {len(tests)} test(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
