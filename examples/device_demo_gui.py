#!/usr/bin/env python3
"""Open the tkinter debugger with the same image as device_demo.py (MMIO + IRQ + UART + timer).

From repo root:
  python examples/device_demo_gui.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EXAMPLES = ROOT / "examples"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(EXAMPLES) not in sys.path:
    sys.path.append(str(EXAMPLES))

from cli.debug_gui import DebuggerApp
from core.bus import SystemBus
from core.debug_controller import DebugController
from core.memory import Memory

from device_demo import MAIN, prepare_device_demo


def main() -> None:
    ram = Memory(1 << 20)
    ctrl = DebugController.create(ram=ram, use_mmio=True, load_addr=MAIN)
    bus = ctrl.mem
    assert isinstance(bus, SystemBus)
    prepare_device_demo(ram, bus, ctrl.state)
    ctrl.state.set_pc(MAIN)
    ctrl.runner.break_pcs.clear()
    ctrl.clear_trace()
    ctrl.instruction_count = 0
    ctrl.runner.cycle_counter.reset()
    DebuggerApp(ctrl).mainloop()


if __name__ == "__main__":
    main()
