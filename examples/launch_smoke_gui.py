#!/usr/bin/env python3
"""Open debugger GUI with the smoke image preloaded.

Run from repo root:
  python examples/launch_smoke_gui.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cli.debug_gui import DebuggerApp
from core.debug_controller import DebugController
from core.memory import Memory


def main() -> None:
    ram = Memory()
    ctrl = DebugController.create(ram=ram, use_mmio=False, load_addr=0)
    ctrl.load_hex_file(ROOT / "examples" / "smoke.hex")
    ctrl.reset_cpu(preserve_breakpoints=True)
    DebuggerApp(ctrl).mainloop()


if __name__ == "__main__":
    main()
