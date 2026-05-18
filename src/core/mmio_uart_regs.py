"""GENERATED FILE — do not edit by hand."""
# Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py

from __future__ import annotations

# UartRegs offsets relative to device base in SystemBus

class UartRegs:
    REG_TXDATA = 0
    REG_RXDATA = 4
    REG_STATUS = 8
    REG_CTRL = 12
    FIFO_DEPTH = 8

    STAT_RX_READY = 1 << 0
    STAT_TX_IDLE = 1 << 1
    STAT_TX_FULL = 1 << 2
    STAT_RX_FULL = 1 << 3

    CTRL_IRQ_RX = 1 << 0
    CTRL_IRQ_TX = 1 << 1

    # Legacy aliases (Python drivers)
    UART_TX = REG_TXDATA
    UART_RX = REG_RXDATA
    UART_STATUS = REG_STATUS
    UART_CTRL = REG_CTRL
    FLAG_RX_READY = STAT_RX_READY
    FLAG_TX_IDLE = STAT_TX_IDLE
    FLAG_TX_FULL = STAT_TX_FULL
    FLAG_RX_FULL = STAT_RX_FULL


__all__ = ['UartRegs']
