"""Instruction cycle costs (functional timing model)."""

from __future__ import annotations

_DEFAULT = 1

_COSTS: dict[str, int] = {
    "MUL": 3,
    "UMULL": 3,
    "SMULL": 3,
    "SMUL": 3,
    "MLA": 3,
    "LDR": 2,
    "STR": 2,
    "LDRPOST": 2,
    "STRPOST": 2,
    "LDRPRE": 2,
    "STRPRE": 2,
    "LDREX": 2,
    "STREX": 2,
}


def cycles_for_mnemonic(mnemonic: str) -> int:
    return _COSTS.get(mnemonic, _DEFAULT)


class CycleCounter:
    """Monotonic 64-bit cycle accumulator (Python int)."""

    __slots__ = ("_value",)

    def __init__(self) -> None:
        self._value = 0

    @property
    def value(self) -> int:
        return self._value

    def add(self, n: int) -> None:
        if n < 0:
            raise ValueError("cycle delta must be non-negative")
        self._value += n

    def reset(self) -> None:
        self._value = 0
