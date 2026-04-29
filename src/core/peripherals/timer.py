"""Cycle compare timer with optional IRQ via CPUState.raise_irq."""

from __future__ import annotations

from typing import Callable

from core.state import CPUState

GetCycles = Callable[[], int]


class CycleTimer:
    CTRL_IRQ_EN = 1 << 0
    CTRL_PENDING = 1 << 1
    CTRL_ACK_W1C = 1 << 2

    __slots__ = (
        "_get_cycles",
        "_compare",
        "_irq_en",
        "_pending",
    )

    def __init__(self, get_cycles: GetCycles) -> None:
        self._get_cycles = get_cycles
        self._compare = 0
        self._irq_en = False
        self._pending = False

    @property
    def compare(self) -> int:
        return self._compare

    def read_reg(self, offset: int) -> int:
        c = self._get_cycles() & ((1 << 64) - 1)
        if offset == 0:
            return c & 0xFFFFFFFF
        if offset == 4:
            return (c >> 32) & 0xFFFFFFFF
        if offset == 8:
            return self._compare & 0xFFFFFFFF
        if offset == 12:
            return (self._compare >> 32) & 0xFFFFFFFF
        if offset == 16:
            st = 0
            if self._irq_en:
                st |= self.CTRL_IRQ_EN
            if self._pending:
                st |= self.CTRL_PENDING
            return st
        return 0

    def write_reg(self, offset: int, value: int) -> None:
        v = value & 0xFFFFFFFF
        if offset == 8:
            self._compare = (self._compare & 0xFFFF_FFFF_0000_0000) | v
        elif offset == 12:
            self._compare = (self._compare & 0xFFFF_FFFF) | (v << 32)
        elif offset == 16:
            self._irq_en = bool(v & self.CTRL_IRQ_EN)
            if v & self.CTRL_ACK_W1C:
                self._pending = False

    def process(self, total_cycles: int, state: CPUState, return_pc: int) -> None:
        """After incrementing global cycle count; may call raise_irq once."""
        if self._pending or not self._irq_en:
            return
        if total_cycles >= self._compare:
            self._pending = True
            state.raise_irq(return_pc)
