"""System bus: RAM + MMIO peripherals."""

from __future__ import annotations

from core.cycles import CycleCounter
from core.exceptions import MisalignedAccess
from core.memory import Memory
from core.peripherals.gpio import Gpio
from core.peripherals.timer import CycleTimer
from core.peripherals.uart import Uart
from core.state import CPUState

MMIO_BASE_DEFAULT = 0xFFFF_0000
MMIO_WINDOW_SIZE = 0x3000

GPIO_OFFSET = 0x0000
UART_OFFSET = 0x1000
TIMER_OFFSET = 0x2000


class SystemBus:
    def __init__(
        self,
        ram: Memory,
        *,
        mmio_base: int = MMIO_BASE_DEFAULT,
        uart: Uart | None = None,
    ) -> None:
        self.ram = ram
        self.mmio_base = mmio_base & 0xFFFFFFFF
        self.gpio = Gpio()
        self.uart = uart if uart is not None else Uart()
        self.timer = CycleTimer(lambda: 0)

    @property
    def ram_size(self) -> int:
        return self.ram.size

    def set_cycle_counter(self, counter: CycleCounter) -> None:
        self.timer._get_cycles = lambda: counter.value  # type: ignore[method-assign]

    def _check_align(self, addr: int) -> None:
        if addr % 4 != 0:
            raise MisalignedAccess(f"address 0x{addr:x} not word-aligned")

    def _read_mmio(self, addr: int) -> int:
        off = (addr - self.mmio_base) & 0xFFFFFFFF
        if off == GPIO_OFFSET:
            return self.gpio.read_word()
        if UART_OFFSET <= off < UART_OFFSET + 0x10:
            return self.uart.read_reg(off - UART_OFFSET)
        if TIMER_OFFSET <= off < TIMER_OFFSET + 0x20:
            return self.timer.read_reg(off - TIMER_OFFSET)
        raise IndexError(f"unmapped MMIO read 0x{addr:x}")

    def _write_mmio(self, addr: int, value: int) -> None:
        off = (addr - self.mmio_base) & 0xFFFFFFFF
        if off == GPIO_OFFSET:
            self.gpio.write_word(value)
            return
        if UART_OFFSET <= off < UART_OFFSET + 0x10:
            self.uart.write_reg(off - UART_OFFSET, value)
            return
        if TIMER_OFFSET <= off < TIMER_OFFSET + 0x20:
            self.timer.write_reg(off - TIMER_OFFSET, value)
            return
        raise IndexError(f"unmapped MMIO write 0x{addr:x}")

    def read_word(self, addr: int) -> int:
        self._check_align(addr)
        if 0 <= addr < self.ram.size:
            return self.ram.read_word(addr)
        if self.mmio_base <= addr < self.mmio_base + MMIO_WINDOW_SIZE:
            return self._read_mmio(addr)
        raise IndexError(f"read out of range: 0x{addr:x}")

    def write_word(self, addr: int, value: int) -> None:
        self._check_align(addr)
        if 0 <= addr < self.ram.size:
            self.ram.write_word(addr, value)
            return
        if self.mmio_base <= addr < self.mmio_base + MMIO_WINDOW_SIZE:
            self._write_mmio(addr, value)
            return
        raise IndexError(f"write out of range: 0x{addr:x}")

    def write_bytes(self, addr: int, data: bytes) -> None:
        self.ram.write_bytes(addr, data)

    def on_step_end(self, total_cycles: int, state: CPUState, return_pc: int) -> None:
        self.timer.process(total_cycles, state, return_pc)
