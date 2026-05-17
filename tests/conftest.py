"""Pytest configuration and shared simulation helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from core.asm import assemble_text
from core.bus import SystemBus
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "slow: property-based and long integration tests")


def _zero_regs(pc: int = 0) -> list[int]:
    regs = [0] * 32
    regs[31] = pc & 0xFFFFFFFF
    return regs


@pytest.fixture
def mem16() -> Memory:
    return Memory(1 << 16)


@pytest.fixture
def cpu(mem16: Memory) -> CPUState:
    st = CPUState()
    st.regs = _zero_regs(0)
    return st


def run_one_step(
    word: int,
    *,
    regs: list[int] | None = None,
    flags: int = 0,
    mem: dict[int, int] | None = None,
    spr: dict[int, int] | None = None,
    pc: int = 0,
    bus: SystemBus | None = None,
) -> tuple[CPUState, Memory | SystemBus]:
    """Execute a single instruction at ``pc``; return (state, memory backend)."""
    backend: Memory | SystemBus
    if bus is not None:
        backend = bus
    else:
        backend = Memory(1 << 16)
    st = CPUState()
    st.regs = list(regs) if regs is not None else _zero_regs(pc)
    if len(st.regs) != 32:
        raise ValueError("regs must have length 32")
    st.regs = [x & 0xFFFFFFFF for x in st.regs]
    st.flags = flags & 0xFFFFFFFF
    for idx, val in (spr or {}).items():
        st.spr_write(int(idx), int(val))
    st.halted = False
    st.set_pc(pc)
    if mem:
        for addr, val in mem.items():
            backend.write_word(int(addr), int(val))
    backend.write_word(pc, word & 0xFFFFFFFF)
    Runner(st, backend).step()
    return st, backend


def run_program(
    asm: str,
    *,
    max_steps: int = 10_000,
    mmio: bool = False,
    on_step: Callable[..., Any] | None = None,
) -> tuple[CPUState, Memory | SystemBus]:
    words = assemble_text(asm)
    ram = Memory(max(0x10000, len(words) * 4 + 0x400))
    for i, w in enumerate(words):
        ram.write_word(i * 4, w)
    st = CPUState()
    st.set_pc(0)
    if mmio:
        bus = SystemBus(ram)
        run = Runner(st, bus, on_step=on_step)
    else:
        bus = ram
        run = Runner(st, bus, on_step=on_step)
    run.run(max_steps=max_steps)
    return st, bus
