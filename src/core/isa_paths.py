"""Locate ISA assets (opcodes YAML) relative to install or repo root."""

from __future__ import annotations

import os
from pathlib import Path


def find_opcodes_yaml() -> Path:
    env = os.environ.get("E32C_ISA_YAML")
    if env:
        p = Path(env)
        if p.is_file():
            return p
    start = Path(__file__).resolve()
    for base in [start.parent, *start.parents]:
        cand = base / "docs" / "isa" / "opcodes.yaml"
        if cand.is_file():
            return cand
    raise FileNotFoundError("docs/isa/opcodes.yaml not found; set E32C_ISA_YAML")
