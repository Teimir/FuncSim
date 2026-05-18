"""Cycle timer (RTL apb_timer; register map from docs/isa/mmio_map.yaml)."""

from __future__ import annotations

from collections.abc import Callable

from core.mmio_timer_regs import TimerRegs
from core.state import CPUState

GetCycles = Callable[[], int]


class CycleTimer:
    CTRL_IRQ_EN = TimerRegs.CTRL_IRQ_EN
    CTRL_PENDING = TimerRegs.CTRL_PENDING
    CTRL_ACK_W1C = TimerRegs.CTRL_ACK_W1C

    __slots__ = (
        "_get_cycles",
        "_last_cycles",
        "_counter",
        "_period",
        "_irq_en",
        "_pending",
    )

    def __init__(self, get_cycles: GetCycles) -> None:
        self._get_cycles = get_cycles
        self._last_cycles = 0
        self._counter = 0
        self._period = 27_000_000
        self._irq_en = False
        self._pending = False

    def read_reg(self, offset: int) -> int:
        if offset == TimerRegs.REG_COUNTER:
            return self._counter & 0xFFFFFFFF
        if offset == TimerRegs.REG_COUNTER_HI_PAD:
            return 0
        if offset in (TimerRegs.REG_PERIOD_LO, TimerRegs.REG_PERIOD_LO_ALIAS):
            return self._period & 0xFFFFFFFF
        if offset in (TimerRegs.REG_PERIOD_HI, TimerRegs.REG_PERIOD_HI_ALIAS):
            return (self._period >> 16) & 0xFFFF
        if offset == TimerRegs.REG_CTRL:
            st = 0
            if self._irq_en:
                st |= self.CTRL_IRQ_EN
            if self._pending:
                st |= self.CTRL_PENDING
            return st
        return 0

    def write_reg(self, offset: int, value: int) -> None:
        v = value & 0xFFFFFFFF
        if offset in (TimerRegs.REG_PERIOD_LO, TimerRegs.REG_PERIOD_LO_ALIAS):
            self._period = (self._period & 0xFFFF_0000) | v
        elif offset in (TimerRegs.REG_PERIOD_HI, TimerRegs.REG_PERIOD_HI_ALIAS):
            self._period = (self._period & 0xFFFF) | ((v & 0xFFFF) << 16)
        elif offset == TimerRegs.REG_CTRL:
            self._irq_en = bool(v & self.CTRL_IRQ_EN)
            if v & self.CTRL_ACK_W1C:
                self._pending = False
                self._counter = 0
        elif offset in (TimerRegs.REG_COUNTER, TimerRegs.REG_COUNTER_HI_PAD):
            pass

    def process(self, total_cycles: int, state: CPUState, return_pc: int) -> None:
        """Advance counter by retired cycles; deliver IRQ when line active (RTL level model)."""
        delta = total_cycles - self._last_cycles
        self._last_cycles = total_cycles
        if delta <= 0:
            delta = 1
        self._counter = (self._counter + delta) & 0xFFFFFFFF
        if self._period == 0:
            return
        if not self._pending and self._counter >= self._period:
            self._pending = True
        if not self._pending or not self._irq_en:
            return
        from core import flags as F

        if not (state.flags & F.FLAG_INTENABLE) or state.irq_in_service:
            return
        state.raise_irq(return_pc, line=0)
