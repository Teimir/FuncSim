"""Byte-addressable little-endian memory."""

from __future__ import annotations

from core.exceptions import MisalignedAccess


class Memory:
    def __init__(self, size: int = 1 << 20) -> None:
        if size <= 0 or size % 4 != 0:
            raise ValueError("size must be positive multiple of 4")
        self._size = size
        self._data = bytearray(size)

    @property
    def size(self) -> int:
        return self._size

    def _check_align(self, addr: int) -> None:
        if addr % 4 != 0:
            raise MisalignedAccess(f"address 0x{addr:x} not word-aligned")

    def _check_range(self, addr: int, nbytes: int) -> None:
        if addr < 0 or addr + nbytes > self._size:
            raise IndexError(f"memory access out of range: 0x{addr:x} len={nbytes}")

    def read_word(self, addr: int) -> int:
        self._check_align(addr)
        self._check_range(addr, 4)
        b0, b1, b2, b3 = self._data[addr : addr + 4]
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def write_word(self, addr: int, value: int) -> None:
        self._check_align(addr)
        self._check_range(addr, 4)
        v = value & 0xFFFFFFFF
        self._data[addr] = v & 0xFF
        self._data[addr + 1] = (v >> 8) & 0xFF
        self._data[addr + 2] = (v >> 16) & 0xFF
        self._data[addr + 3] = (v >> 24) & 0xFF

    def write_bytes(self, addr: int, data: bytes) -> None:
        self._check_range(addr, len(data))
        self._data[addr : addr + len(data)] = data
