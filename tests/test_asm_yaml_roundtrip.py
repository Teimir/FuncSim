"""Assemble one sample per YAML format and verify decode mnemonic."""

from __future__ import annotations

import yaml

from core.asm import AssembleError, assemble_line
from core.decode import decode_word
from core.isa_paths import find_opcodes_yaml


def _sample_line(mnemonic: str, fmt: str) -> str:
    m = mnemonic.upper()
    if fmt == "special_nop":
        return "NOP"
    if fmt == "special_halt":
        return "HALT"
    if fmt == "bare":
        return m
    if fmt == "rrr":
        return f"{m} 1 2 3"
    if fmt == "mul":
        return f"{m} 1 2 3 4"
    if fmt == "imm16":
        return f"{m} 1 2 42"
    if fmt == "branch":
        return f"{m} 5 0"
    if fmt == "load_store":
        return f"{m} 6 7 15 0"
    if fmt == "store":
        return f"{m} 6 7 15 0"
    if fmt == "spr":
        return f"{m} 2 3"
    raise ValueError(fmt)


def test_all_yaml_mnemonics_roundtrip() -> None:
    path = find_opcodes_yaml()
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    seen: set[str] = set()
    for ent in doc["instructions"]:
        mnemonic = str(ent["mnemonic"])
        fmt = str(ent["format"])
        key = f"{mnemonic}:{fmt}"
        if key in seen:
            continue
        seen.add(key)
        if mnemonic in ("NOP", "HALT"):
            w = assemble_line(_sample_line(mnemonic, fmt))
        else:
            line = _sample_line(mnemonic, fmt)
            try:
                w = assemble_line(line)
            except AssembleError as e:
                raise AssertionError(f"{mnemonic} {fmt} line={line!r}: {e}") from e
        ins = decode_word(w)
        assert ins.mnemonic == mnemonic, f"{line} -> {ins.mnemonic}"
