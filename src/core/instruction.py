"""Decoded instruction representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Instruction:
    mnemonic: str
    format: str
    raw: int
    fields: Mapping[str, Any]
