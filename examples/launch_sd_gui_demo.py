#!/usr/bin/env python3
"""Open debugger GUI with MMIO + SD image and a small SD read/write demo.

Run from repo root:
  python examples/launch_sd_gui_demo.py

The program at 0x200 writes 0xDEADC0DE to LBA 0, reads it back, and sets GPIO
MMIO to 1 on success or 2 on failure (then HALT). Step in the GUI to watch SD
registers on the Storage tab.

Assembler source follows docs/isa/spec.md (R30=SP, R31=PC; demo uses CMP/MOV).
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cli.debug_gui import DebuggerApp
from cli.debug_common import add_core_argument
from core.asm import assemble_text
from core.debug_controller import DebugController
from core.loader import load_words
from core.memory import Memory

POOL = 0x100
MAIN = 0x200


def main() -> None:
    p = argparse.ArgumentParser(description="SD block demo in debugger GUI")
    add_core_argument(p)
    args = p.parse_args()

    asm_path = ROOT / "examples" / "sd_gui_demo.asm"
    words = assemble_text(asm_path.read_text(encoding="utf-8"))

    ram = Memory()
    ctrl: DebugController | None = None
    with tempfile.NamedTemporaryFile(prefix="e32c_sd_demo_", suffix=".img", delete=False) as f:
        img_path = Path(f.name)
    try:
        ctrl = DebugController.create(
            ram=ram,
            use_mmio=True,
            load_addr=MAIN,
            sd_image=img_path,
            sd_create_sectors=2,
            core_variant=args.core,
        )
        ctrl.mem.write_word(POOL, 0xFFFF3000)
        ctrl.mem.write_word(POOL + 4, 0xDEADC0DE)
        load_words(ctrl.mem, MAIN, words)
        ctrl.state.set_pc(MAIN)
        DebuggerApp(ctrl).mainloop()
    finally:
        if ctrl is not None:
            try:
                if hasattr(ctrl.mem, "sd"):
                    ctrl.mem.sd.unmount()
            except OSError:
                pass
        img_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
