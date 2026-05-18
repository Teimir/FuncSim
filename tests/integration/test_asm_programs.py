"""Assemble and run example programs in the Python simulator."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.asm import AssembleError, assemble_text
from core.bus import SystemBus
from core.cycles import CycleCounter
from core.loader import load_words, words_from_hex_lines
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState

ROOT = Path(__file__).resolve().parents[2]


def _run_asm(source: str, *, max_steps: int = 50_000) -> tuple[CPUState, SystemBus, int]:
    words = assemble_text(source)
    mem = Memory(64 * 1024)
    load_words(mem, 0, words)
    st = CPUState()
    st.set_pc(0)
    bus = SystemBus(mem)
    bus.set_cycle_counter(CycleCounter())
    steps = Runner(st, bus).run(max_steps=max_steps)
    return st, bus, steps


def test_launch_smoke_hex() -> None:
    image = ROOT / "examples" / "smoke.hex"
    words = words_from_hex_lines(image.read_text(encoding="utf-8"))
    mem = Memory()
    st = CPUState()
    load_words(mem, 0, words)
    st.set_pc(0)
    steps = Runner(st, mem).run(max_steps=1000)
    assert steps > 0


def test_blink_uart_runs_without_hang() -> None:
    asm_path = ROOT / "examples" / "blink_uart.asm"
    source = asm_path.read_text(encoding="utf-8")
    st, bus, steps = _run_asm(source, max_steps=2_000_000)
    assert steps > 0
    assert not st.halted
    tx = bytes(bus.uart.tx_sent)
    assert len(tx) >= 2
    assert tx[0:2] == b"BL"
    if len(tx) >= 4:
        assert tx[2:4] == b"\r\n"


def test_uart_tx_mmio_mini_program() -> None:
    prog = """
    MOV 1 -1
    MOV 2 16
    SLL 1 2 1
    ADDI 1 1 4096
    MOV 10 65
    STR 1 10 15 0
    HALT
    """
    st, bus, steps = _run_asm(prog, max_steps=500)
    assert st.halted
    assert steps > 0
    assert bytes(bus.uart.tx_sent) == b"A"


def test_tn9k_uart_hello_once() -> None:
    asm_path = ROOT / "examples" / "tn9k_uart_hello.asm"
    st, bus, steps = _run_asm(asm_path.read_text(encoding="utf-8"), max_steps=30_000)
    assert steps > 0
    tx = bytes(bus.uart.tx_sent)
    assert tx == b"Hi!\r\n", f"unexpected uart: {tx!r}"


def test_tn9k_uart_beacon_once() -> None:
    asm_path = ROOT / "examples" / "tn9k_uart_beacon.asm"
    st, bus, steps = _run_asm(asm_path.read_text(encoding="utf-8"), max_steps=10_000)
    assert steps > 0
    tx = bytes(bus.uart.tx_sent)
    assert tx == b"U", f"unexpected uart: {tx!r}"
    assert 0x0A not in tx


def test_blink_uart_assembles() -> None:
    asm_path = ROOT / "examples" / "blink_uart.asm"
    words = assemble_text(asm_path.read_text(encoding="utf-8"))
    assert len(words) > 10


@pytest.mark.slow
def test_blink_uart_irq_timer_fires() -> None:
    """Main @0 + handler @0x100; timer IRQ emits BL."""
    main = (ROOT / "examples" / "blink_uart_irq_main.asm").read_text(encoding="utf-8")
    handler = (ROOT / "examples" / "blink_uart_irq_handler.asm").read_text(encoding="utf-8")
    words = assemble_text(main)
    idx = 0x100 // 4
    while len(words) < idx:
        words.append(0)
    words.extend(assemble_text(handler))
    mem = Memory(64 * 1024)
    load_words(mem, 0, words)
    st = CPUState()
    st.set_pc(0)
    bus = SystemBus(mem)
    bus.set_cycle_counter(CycleCounter())
    steps = Runner(st, bus).run(max_steps=30_000_000)
    tx = bytes(bus.uart.tx_sent)
    assert steps > 0
    assert not st.halted
    assert b"BL" in tx


@pytest.mark.slow
def test_tn9k_demo_uart_timer_sd() -> None:
    """UART banner + SD SPI init + timer IRQ ticks (see examples/launch_tn9k_demo.py)."""
    main = (ROOT / "examples" / "tn9k_demo_uart_timer_sd_main.asm").read_text(encoding="utf-8")
    handler = (ROOT / "examples" / "tn9k_demo_uart_timer_sd_handler.asm").read_text(encoding="utf-8")
    words = assemble_text(main)
    idx = 0x200 // 4
    while len(words) < idx:
        words.append(0)
    words.extend(assemble_text(handler))
    mem = Memory(64 * 1024)
    load_words(mem, 0, words)
    st = CPUState()
    st.set_pc(0)
    img = ROOT / "examples" / "_sd_spi_test.img"
    bus = SystemBus(mem, sd_spi=True, sd_image=img, sd_create_sectors=4)
    bus.set_cycle_counter(CycleCounter())
    steps = Runner(st, bus).run(max_steps=500_000)
    tx = bytes(bus.uart.tx_sent)
    assert steps > 0
    assert tx.startswith(b"US")
    assert b"G" in tx
    assert b"R" in tx
    assert tx.count(b"T") >= 2


def test_invalid_asm_raises() -> None:
    with pytest.raises(AssembleError):
        assemble_text("NOT_AN_INSTRUCTION 0 1 2")
