"""Execution trace record."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepTrace:
    pc: int
    word: int
    disasm: str
    cycles_after: int
    halted_after: bool
