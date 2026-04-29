"""Simplified UART: TX buffer, RX queue, status."""

from __future__ import annotations

from collections import deque
from typing import BinaryIO, Callable


class Uart:
    UART_TX = 0
    UART_RX = 4
    UART_STATUS = 8

    FLAG_RX_READY = 1 << 0
    FLAG_TX_IDLE = 1 << 1

    __slots__ = ("_tx_buf", "_rx", "_on_tx_byte")

    def __init__(self, on_tx_byte: Callable[[int], None] | None = None) -> None:
        self._tx_buf = bytearray()
        self._rx: deque[int] = deque()
        self._on_tx_byte = on_tx_byte

    @property
    def tx_buffer(self) -> bytearray:
        return self._tx_buf

    def feed_rx(self, data: bytes) -> None:
        for b in data:
            self._rx.append(b & 0xFF)

    def read_reg(self, offset: int) -> int:
        if offset == self.UART_TX:
            return 0
        if offset == self.UART_RX:
            if not self._rx:
                return 0
            return self._rx.popleft() & 0xFF
        if offset == self.UART_STATUS:
            st = self.FLAG_TX_IDLE
            if self._rx:
                st |= self.FLAG_RX_READY
            return st
        return 0

    def write_reg(self, offset: int, value: int) -> None:
        if offset == self.UART_TX:
            b = value & 0xFF
            self._tx_buf.append(b)
            if self._on_tx_byte is not None:
                self._on_tx_byte(b)

    def write_stream_hook(self, stream: BinaryIO) -> None:
        """Append bytes to stream on each TX (e.g. stdout.buffer)."""

        def hook(b: int) -> None:
            stream.write(bytes([b]))
            stream.flush()

        self._on_tx_byte = hook
