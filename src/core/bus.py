"""System bus: RAM + MMIO peripherals."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from core.cycles import CycleCounter
from core.exceptions import MisalignedAccess
from core.memory import Memory
from core.mmio_constants import (
    GPIO_OFFSET,
    GPIO_REGION_SIZE,
    MMIO_BASE_DEFAULT,
    MMIO_WINDOW_SIZE,
    SD_OFFSET,
    SD_REGION_SIZE,
    TIMER_OFFSET,
    TIMER_REGION_SIZE,
    UART_OFFSET,
    UART_REGION_SIZE,
)
from core.peripherals.gpio import Gpio
from core.peripherals.sd_card import SdCardMmio
from core.peripherals.timer import CycleTimer
from core.peripherals.uart import Uart
from core.state import CPUState

__all__ = [
    "MMIO_BASE_DEFAULT",
    "MMIO_WINDOW_SIZE",
    "GPIO_OFFSET",
    "GPIO_REGION_SIZE",
    "UART_OFFSET",
    "UART_REGION_SIZE",
    "TIMER_OFFSET",
    "TIMER_REGION_SIZE",
    "SD_OFFSET",
    "SD_REGION_SIZE",
    "SystemBus",
]


class SystemBus:
    def __init__(
        self,
        ram: Memory,
        *,
        mmio_base: int = MMIO_BASE_DEFAULT,
        uart: Uart | None = None,
        sd_image: Path | None = None,
        sd_create_sectors: int | None = None,
    ) -> None:
        self.ram = ram
        self.mmio_base = mmio_base & 0xFFFFFFFF
        self.gpio = Gpio()
        self.uart = uart if uart is not None else Uart()
        self.timer = CycleTimer(lambda: 0)
        self.sd = SdCardMmio()
        if sd_image is not None:
            self.sd.mount(sd_image, create_sectors=sd_create_sectors)

        self._mmio_regions: list[
            tuple[int, int, Callable[[int], int], Callable[[int, int], None]]
        ] = [
            (GPIO_OFFSET, GPIO_OFFSET + GPIO_REGION_SIZE, self._mmio_gpio_read, self._mmio_gpio_write),
            (UART_OFFSET, UART_OFFSET + UART_REGION_SIZE, self._mmio_uart_read, self._mmio_uart_write),
            (TIMER_OFFSET, TIMER_OFFSET + TIMER_REGION_SIZE, self._mmio_timer_read, self._mmio_timer_write),
            (SD_OFFSET, SD_OFFSET + SD_REGION_SIZE, self._mmio_sd_read, self._mmio_sd_write),
        ]

    @property
    def ram_size(self) -> int:
        return self.ram.size

    def set_cycle_counter(self, counter: CycleCounter) -> None:
        self.timer._get_cycles = lambda: counter.value  # type: ignore[method-assign]

    def _check_align(self, addr: int) -> None:
        if addr % 4 != 0:
            raise MisalignedAccess(f"address 0x{addr:x} not word-aligned")

    def _mmio_offset(self, addr: int) -> int:
        return (addr - self.mmio_base) & 0xFFFFFFFF

    def _mmio_gpio_read(self, rel: int) -> int:
        if rel != 0:
            raise IndexError(f"GPIO bad offset +0x{rel:x}")
        return self.gpio.read_word()

    def _mmio_gpio_write(self, rel: int, value: int) -> None:
        if rel != 0:
            raise IndexError(f"GPIO bad offset +0x{rel:x}")
        self.gpio.write_word(value)

    def _mmio_uart_read(self, rel: int) -> int:
        return self.uart.read_reg(rel)

    def _mmio_uart_write(self, rel: int, value: int) -> None:
        self.uart.write_reg(rel, value)

    def _mmio_timer_read(self, rel: int) -> int:
        return self.timer.read_reg(rel)

    def _mmio_timer_write(self, rel: int, value: int) -> None:
        self.timer.write_reg(rel, value)

    def _mmio_sd_read(self, rel: int) -> int:
        return self.sd.read_word(rel)

    def _mmio_sd_write(self, rel: int, value: int) -> None:
        self.sd.write_word(rel, value)

    def _read_mmio(self, addr: int) -> int:
        off = self._mmio_offset(addr)
        for lo, hi, rfn, _ in self._mmio_regions:
            if lo <= off < hi:
                return rfn(off - lo)
        raise IndexError(f"unmapped MMIO read 0x{addr:x}")

    def _write_mmio(self, addr: int, value: int) -> None:
        off = self._mmio_offset(addr)
        for lo, hi, _, wfn in self._mmio_regions:
            if lo <= off < hi:
                wfn(off - lo, value)
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
