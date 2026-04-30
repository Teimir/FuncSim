#!/usr/bin/env python3
"""Open GUI debugger with UART calculator demo loaded.

Use "View -> UART terminal..." in GUI:
- send text like: 7+2
- click Step/Run N/Continue to execute
- check UART TX output in terminal window

Run from repo root:
  python examples/uart_calculator_gui.py
"""

from __future__ import annotations

import sys
import tkinter as tk
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
from uart_calculator import MAIN, prepare_uart_calculator


def _send_example(ctrl: DebugController, expr: str) -> None:
    ctrl.feed_uart_rx(expr.encode("utf-8", errors="replace"))


def main() -> None:
    ram = Memory(1 << 20)
    ctrl = DebugController.create(ram=ram, use_mmio=True, load_addr=MAIN)
    bus = ctrl.mem
    assert isinstance(bus, SystemBus)
    prepare_uart_calculator(ram, bus, ctrl.state)
    ctrl.state.set_pc(MAIN)
    ctrl.runner.break_pcs.clear()
    ctrl.clear_trace()
    ctrl.instruction_count = 0
    ctrl.runner.cycle_counter.reset()

    app = DebuggerApp(ctrl)
    app.geometry("1500x980")
    examples_menu = tk.Menu(app, tearoff=0)
    examples_menu.add_command(label="Send: 8*8", command=lambda: _send_example(ctrl, "8*8\n"))
    examples_menu.add_command(label="Send: 12*12", command=lambda: _send_example(ctrl, "12*12\n"))
    examples_menu.add_command(label="Send: HALT", command=lambda: _send_example(ctrl, "HALT\n"))
    if app["menu"]:
        app.nametowidget(app["menu"]).add_cascade(label="Examples", menu=examples_menu)

    def _open_uart_big() -> None:
        app._open_uart_terminal()
        if app._uart_win is not None and app._uart_win.winfo_exists():
            app._uart_win.geometry("900x520")

    app.after(50, _open_uart_big)
    app.mainloop()


if __name__ == "__main__":
    main()
