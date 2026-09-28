"""frontend_unit.py runs vitest in the scratch copy (or in place for CI) and maps exit codes like every executor."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import frontend_unit  # noqa: E402


def _fake_vitest(frontend: Path, exit_code: int) -> None:
    binaries = frontend / "node_modules/.bin"
    binaries.mkdir(parents=True, exist_ok=True)
    script = binaries / "vitest"
    script.write_text(f"#!/bin/sh\necho \"$@\" > \"{frontend}/vitest-args.txt\"\nexit {exit_code}\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


class FrontendUnitTests(unittest.TestCase):
    def test_exit_codes_follow_the_executor_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            frontend = Path(folder) / "frontend"
            self.assertEqual(frontend_unit.run_vitest(frontend), 2)  # no node_modules: environment error
            _fake_vitest(frontend, 0)
            self.assertEqual(frontend_unit.run_vitest(frontend), 0)
            args = (frontend / "vitest-args.txt").read_text(encoding="utf-8")
            self.assertIn("run", args)
            self.assertIn("--passWithNoTests", args)  # a project without frontend tests yet is not a failure
            _fake_vitest(frontend, 1)
            self.assertEqual(frontend_unit.run_vitest(frontend), 1)  # test failures are behaviour failures

    def test_in_place_uses_the_checkout_and_scratch_mode_syncs_first(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            synced = []
            self.assertEqual(frontend_unit.resolve_frontend(root, in_place=True, sync=lambda r, n: synced.append(n)),
                             root / "frontend")
            self.assertEqual(synced, [])
            scratch = root / "scratch"
            self.assertEqual(frontend_unit.resolve_frontend(root, in_place=False,
                                                            sync=lambda r, n: (synced.append(n), scratch)[1]),
                             scratch / "frontend")
            self.assertEqual(synced, [frontend_unit.SCRATCH_NAME])


if __name__ == "__main__":
    unittest.main()
