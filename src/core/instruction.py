"""Decoded instruction representation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Instruction:
    mnemonic: str
    format: str
    raw: int
    fields: Mapping[str, Any]
