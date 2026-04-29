"""Memory / bus protocol for word-aligned access."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WordMemory(Protocol):
    def read_word(self, addr: int) -> int: ...
    def write_word(self, addr: int, value: int) -> None: ...
