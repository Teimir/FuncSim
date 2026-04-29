#!/usr/bin/env python3
"""
Demo: GPIO, UART (TX bytes, RX, STATUS), timer (compare + IRQ + ACK), EI/IRET.

Run from repo root:
  python examples/device_demo.py
Paths: adds src/ to sys.path.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.bus import SystemBus
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState, SPR_IRQ_VECTOR
from core.asm import assemble_text

POOL = 0x100
MAIN = 0x200
HANDLER = 0x400


def main() -> None:
    ram = Memory(1 << 20)
    bus = SystemBus(ram)
    st = CPUState()

    ram.write_word(POOL + 0x00, 0xFFFF_0000)
    ram.write_word(POOL + 0x04, 0xCAFE_BABE)
    ram.write_word(POOL + 0x08, 0x00FF_00FF)
    ram.write_word(POOL + 0x0C, 0x0A21_6948)
    ram.write_word(POOL + 0x10, 0x0A52_4948)

    bus.uart.feed_rx(b"X")
    st.spr_write(SPR_IRQ_VECTOR, HANDLER)

    # Timer compare low: fire after EI + a few NOPs (total cycles ~30+ early in run).
    # UART model appends only the low byte per TX register write — send H i ! \\n with mask 1.
    nops = "\n".join(["NOP"] * 24)
    main_src = f"""
ADDI 0 20 256
LDR 20 21 15 0
LDR 20 22 15 4
ADDI 21 23 4096
ADDI 21 24 8192
STR 21 22 15 0
ADDI 0 27 72
STR 23 27 1 0
ADDI 0 27 105
STR 23 27 1 0
ADDI 0 27 33
STR 23 27 1 0
ADDI 0 27 10
STR 23 27 1 0
LDR 24 30 15 0
ADDI 0 26 28
STR 24 26 15 8
ADDI 0 26 0
STR 24 26 15 12
ADDI 0 26 1
STR 24 26 15 16
EI
{nops}
DI
LDR 23 5 15 8
LDR 23 6 15 4
HALT
"""
    handler_src = """
DI
ADDI 0 20 256
LDR 20 21 15 0
LDR 20 28 15 8
STR 21 28 15 0
LDR 20 29 15 16
ADDI 21 23 4096
STR 23 29 15 0
ADDI 21 24 8192
ADDI 0 26 5
STR 24 26 15 16
IRET
"""

    main_words = assemble_text(main_src)
    handler_words = assemble_text(handler_src)

    a = MAIN
    for w in main_words:
        ram.write_word(a, w)
        a += 4
    a = HANDLER
    for w in handler_words:
        ram.write_word(a, w)
        a += 4

    st.set_pc(MAIN)
    r = Runner(st, bus)
    steps = r.run(max_steps=5000)

    print("=== device_demo ===")
    print(f"steps={steps} halted={st.halted} cycles={r.cycle_counter.value}")
    print(f"gpio_out      = 0x{bus.gpio.out:08x}  (expected 0x00ff00ff after IRQ handler)")
    tx = bytes(bus.uart.tx_buffer)
    print(f"uart_tx bytes = {tx!r}  text={tx.decode('latin-1', errors='replace')!r}")
    print(f"r5 uart STATUS = 0x{st.reg_read(5):08x}")
    print(f"r6 uart RX read = 0x{st.reg_read(6):08x} (queued 'X' = 0x58)")
    print(f"r30 tmr CYCLES_LO snapshot (before timer arm) = 0x{st.reg_read(30):08x}")
    print(f"flags = 0x{st.flags:08x}")
    print(f"SPR0 saved_irq = 0x{st.spr_read(0):08x}")
    if st.halted and bus.gpio.out == 0x00FF_00FF:
        print("OK: HALT and GPIO latched from IRQ handler.")
    elif st.halted:
        print("HALT ok; GPIO mismatch — IRQ may not have run (tune compare/NOP).")
    else:
        print("WARN: not halted — increase max_steps.")


if __name__ == "__main__":
    main()
