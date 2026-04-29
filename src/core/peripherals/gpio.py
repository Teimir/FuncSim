"""32-bit GPIO output latch."""

from __future__ import annotations


class Gpio:
    __slots__ = ("_out",)

    def __init__(self) -> None:
        self._out = 0

    @property
    def out(self) -> int:
        return self._out & 0xFFFFFFFF

    def read_word(self) -> int:
        return self.out

    def write_word(self, value: int) -> None:
        self._out = value & 0xFFFFFFFF
