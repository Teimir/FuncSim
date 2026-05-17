#!/usr/bin/env python3
"""Run TN9K UART+Timer+SD demo in the Python simulator (same MMIO map as RTL/FPGA)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.asm import assemble_text
from core.bus import SystemBus
from core.cycles import CycleCounter
from core.loader import load_words
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState

MAIN = ROOT / "examples" / "tn9k_demo_uart_timer_sd_main.asm"
HANDLER = ROOT / "examples" / "tn9k_demo_uart_timer_sd_handler.asm"
SD_IMG = ROOT / "examples" / "_sd_spi_test.img"


def build_image() -> list[int]:
    words = assemble_text(MAIN.read_text(encoding="utf-8"))
    idx = 0x200 // 4
    while len(words) < idx:
        words.append(0)
    words.extend(assemble_text(HANDLER.read_text(encoding="utf-8")))
    return words


def main() -> int:
    words = build_image()
    mem = Memory(64 * 1024)
    load_words(mem, 0, words)
    st = CPUState()
    st.set_pc(0)
    bus = SystemBus(mem, sd_spi=True, sd_image=SD_IMG, sd_create_sectors=4)
    bus.set_cycle_counter(CycleCounter())
    steps = Runner(st, bus).run(max_steps=500_000)
    tx = bytes(bus.uart.tx_sent)
    print(f"steps={steps} uart={tx!r}")
    if not tx.startswith(b"US"):
        print("FAIL: expected US... banner")
        return 1
    if b"G" not in tx and b"E" not in tx:
        print("FAIL: expected G or E after SD init")
        return 1
    if b"R" not in tx:
        print("FAIL: expected R (IRQ armed)")
        return 1
    ticks = tx.count(b"T")
    if ticks < 2:
        print(f"FAIL: expected >=2 timer ticks (T), got {ticks}")
        return 1
    print("OK tn9k_demo uart+timer+sd")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
