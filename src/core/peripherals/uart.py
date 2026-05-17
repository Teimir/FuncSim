"""UART: TX/RX FIFO (depth 8), status flags aligned with test/src/uart.sv."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

FIFO_DEPTH = 8

UART_TX = 0
UART_RX = 4
UART_STATUS = 8
UART_CTRL = 12

FLAG_RX_READY = 1 << 0
FLAG_TX_IDLE = 1 << 1
FLAG_TX_FULL = 1 << 2
FLAG_RX_FULL = 1 << 3


class Uart:
    __slots__ = ("_tx_fifo", "_rx_fifo", "_on_tx_byte", "_tx_sending", "_tx_sent")

    def __init__(self, on_tx_byte: Callable[[int], None] | None = None) -> None:
        self._tx_fifo: deque[int] = deque(maxlen=FIFO_DEPTH)
        self._rx_fifo: deque[int] = deque(maxlen=FIFO_DEPTH)
        self._on_tx_byte = on_tx_byte
        self._tx_sending = False
        self._tx_sent: list[int] = []

    @property
    def tx_buffer(self) -> bytearray:
        """Bytes still in TX FIFO (not yet shifted out)."""
        return bytearray(self._tx_fifo)

    @property
    def tx_sent(self) -> bytearray:
        """Bytes already driven to TX (for tests)."""
        return bytearray(self._tx_sent)

    @property
    def rx_queued(self) -> int:
        return len(self._rx_fifo)

    def feed_rx(self, data: bytes) -> None:
        for b in data:
            if len(self._rx_fifo) >= FIFO_DEPTH:
                break
            self._rx_fifo.append(b & 0xFF)

    def _status(self) -> int:
        st = 0
        if self._rx_fifo:
            st |= FLAG_RX_READY
        if not self._tx_fifo and not self._tx_sending:
            st |= FLAG_TX_IDLE
        if len(self._tx_fifo) >= FIFO_DEPTH:
            st |= FLAG_TX_FULL
        if len(self._rx_fifo) >= FIFO_DEPTH:
            st |= FLAG_RX_FULL
        return st

    def read_reg(self, offset: int) -> int:
        if offset == UART_TX:
            return 0
        if offset == UART_RX:
            if not self._rx_fifo:
                return 0
            return self._rx_fifo.popleft() & 0xFF
        if offset == UART_STATUS:
            return self._status()
        if offset == UART_CTRL:
            return 0
        return 0

    def write_reg(self, offset: int, value: int) -> None:
        if offset == UART_TX:
            if len(self._tx_fifo) >= FIFO_DEPTH:
                return
            self._tx_fifo.append(value & 0xFF)
            return
        if offset == UART_CTRL:
            return

    def tick(self) -> None:
        """Shift one byte from TX FIFO to the line hook (one per CPU cycle in sim)."""
        if self._tx_sending or not self._tx_fifo:
            return
        self._tx_sending = True
        b = self._tx_fifo.popleft()
        self._tx_sent.append(b)
        if self._on_tx_byte is not None:
            self._on_tx_byte(b)
        self._tx_sending = False

    def set_on_tx_byte(self, cb: Callable[[int], None] | None) -> None:
        self._on_tx_byte = cb

    def clear_tx(self) -> None:
        self._tx_fifo.clear()
        self._tx_sent.clear()
        self._tx_sending = False
