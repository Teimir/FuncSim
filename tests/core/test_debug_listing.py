"""Disassembly listing window must not wrap below load_addr."""

from __future__ import annotations

from core.debug_controller import DebugController
from core.loader import load_words
from core.memory import Memory


def test_listing_at_pc_zero_starts_at_load_addr() -> None:
    ram = Memory(256)
    ctrl = DebugController.create(ram=ram, load_addr=0)
    load_words(ram, 0, [0xC020100A, 0x84432000, 0xFFFFFFFF])
    ctrl.state.set_pc(0)
    lines = ctrl._build_listing(0)
    assert lines
    assert lines[0].addr == 0
    assert lines[0].is_pc
    assert all(ln.addr >= 0 for ln in lines)
    assert not any("out of range" in ln.disasm for ln in lines)

    ctrl.state.set_pc(0x10)
    lines_halt = ctrl._build_listing(0x10)
    assert lines_halt[0].addr == 0
    assert not any(ln.addr >= 0x80000000 for ln in lines_halt)
    assert any(ln.is_pc and ln.addr == 0x10 for ln in lines_halt)
