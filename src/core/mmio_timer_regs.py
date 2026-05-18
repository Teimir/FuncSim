"""GENERATED FILE — do not edit by hand."""
# Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py

from __future__ import annotations

# TimerRegs offsets relative to device base in SystemBus

class TimerRegs:
    REG_COUNTER = 0
    REG_COUNTER_HI_PAD = 4
    REG_PERIOD_LO = 8
    REG_PERIOD_HI = 12
    REG_CTRL = 0x10
    REG_PERIOD_LO_ALIAS = 0x18
    REG_PERIOD_HI_ALIAS = 0x1c

    CTRL_IRQ_EN = 1 << 0
    CTRL_PENDING = 1 << 1
    CTRL_ACK_W1C = 1 << 2


__all__ = ['TimerRegs']
