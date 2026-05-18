"""MMIO snapshot for GUI must use generated register offsets."""

from __future__ import annotations

from core.bus import SystemBus
from core.debug_controller import _mmio_snapshot
from core.memory import Memory
from core.peripherals.uart import Uart


def test_mmio_snapshot_uart_status() -> None:
    ram = Memory(4096)
    uart = Uart()
    bus = SystemBus(ram, uart=uart)
    snap = _mmio_snapshot(bus)
    assert snap.uart_status >= 0
    assert snap.timer_ctrl >= 0
