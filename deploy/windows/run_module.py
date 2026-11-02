"""Run a Python module from a deployment root without relying on cwd."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("module name is required")
    root = Path(
        os.environ.get("AIWORLD_ROOT")
        or Path(__file__).resolve().parents[2]
    ).resolve()
    sys.path.insert(0, str(root))
    module_name = sys.argv[1]
    sys.argv = [module_name, *sys.argv[2:]]
    runpy.run_module(module_name, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
