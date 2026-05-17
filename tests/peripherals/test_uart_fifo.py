"""UART FIFO depth and STATUS flags (Python model vs RTL contract)."""

from __future__ import annotations

from core.bus import SystemBus
from core.memory import Memory
from core.peripherals.uart import (
    FIFO_DEPTH,
    FLAG_RX_FULL,
    FLAG_RX_READY,
    FLAG_TX_FULL,
    FLAG_TX_IDLE,
    UART_RX,
    UART_STATUS,
    UART_TX,
)


def test_tx_fifo_depth_and_full() -> None:
    bus = SystemBus(Memory(4096))
    base = bus.mmio_base + 0x1000
    for i in range(FIFO_DEPTH):
        bus.write_word(base + UART_TX, ord("0") + i)
    assert bus.read_word(base + UART_STATUS) & FLAG_TX_FULL
    bus.write_word(base + UART_TX, ord("X"))
    assert len(bus.uart.tx_buffer) == FIFO_DEPTH
    assert bus.read_word(base + UART_STATUS) & FLAG_TX_FULL


def test_tx_idle_after_drain() -> None:
    bus = SystemBus(Memory(4096))
    base = bus.mmio_base + 0x1000
    bus.write_word(base + UART_TX, ord("A"))
    bus.uart.tick()
    st = bus.read_word(base + UART_STATUS)
    assert st & FLAG_TX_IDLE


def test_rx_fifo_and_full() -> None:
    bus = SystemBus(Memory(4096))
    base = bus.mmio_base + 0x1000
    bus.uart.feed_rx(bytes(range(FIFO_DEPTH)))
    assert bus.read_word(base + UART_STATUS) & FLAG_RX_READY
    assert bus.read_word(base + UART_STATUS) & FLAG_RX_FULL
    bus.uart.feed_rx(b"Z")
    assert bus.read_word(base + UART_RX) == 0


def test_rx_pop() -> None:
    bus = SystemBus(Memory(4096))
    base = bus.mmio_base + 0x1000
    bus.uart.feed_rx(b"AB")
    assert bus.read_word(base + UART_RX) == ord("A")
    assert bus.read_word(base + UART_RX) == ord("B")
