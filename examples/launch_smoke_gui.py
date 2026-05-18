#!/usr/bin/env python3
"""Open debugger GUI with the smoke image preloaded.

Run from repo root:
  python examples/launch_smoke_gui.py
  python examples/launch_smoke_gui.py --core tn9k
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cli.debug_gui.app import main


if __name__ == "__main__":
    # parse_args(argv) does not skip argv[0] — only pass flags, not script path
    argv = ["--hex", str(ROOT / "examples" / "smoke.hex"), *sys.argv[1:]]
    raise SystemExit(main(argv))
