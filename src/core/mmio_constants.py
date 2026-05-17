"""GENERATED FILE — do not edit by hand."""
# Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py

from __future__ import annotations

MMIO_BASE_DEFAULT = 0xffff0000
MMIO_WINDOW_SIZE = 0x4000

GPIO_OFFSET = 0
GPIO_REGION_SIZE = 4
UART_OFFSET = 0x1000
UART_REGION_SIZE = 0x10
TIMER_OFFSET = 0x2000
TIMER_REGION_SIZE = 0x20
SD_OFFSET = 0x3000
SD_REGION_SIZE = 0x210

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
]
