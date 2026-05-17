"""Instruction decode from 32-bit words using docs/isa/opcodes.yaml."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from core.exceptions import IllegalInstruction
from core.instruction import Instruction
from core.isa_paths import find_opcodes_yaml


def _extract_field(word: int, hi: int, lo: int) -> int:
    width = hi - lo + 1
    mask = (1 << width) - 1
    return (word >> lo) & mask


def sext11(v: int) -> int:
    v &= 0x7FF
    if v & 0x400:
        v |= 0xFFFF_F800
    return v & 0xFFFFFFFF


def imm16_from_parts(immh: int, imm11: int) -> int:
    u = ((immh & 0x1F) << 11) | (imm11 & 0x7FF)
    u &= 0xFFFF
    if u & 0x8000:
        u |= 0xFFFF_0000
    return u & 0xFFFFFFFF


@lru_cache(maxsize=1)
def _load_table() -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    path = find_opcodes_yaml()
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    by_opcode: dict[int, dict[str, Any]] = {}
    for ent in doc["instructions"]:
        opc = int(ent["opcode"])
        if opc in by_opcode:
            raise ValueError(f"duplicate opcode {opc:#x}")
        by_opcode[opc] = ent
    return by_opcode, doc


def decode_word(word: int) -> Instruction:
    w = word & 0xFFFFFFFF
    if w == 0:
        return Instruction("NOP", "special_nop", w, {})
    if w == 0xFFFFFFFF:
        return Instruction("HALT", "special_halt", w, {})

    opcode = (w >> 26) & 0x3F
    if opcode == 0 and w != 0:
        raise IllegalInstruction(f"reserved NOP encoding with non-zero payload: {w:#010x}")
    if opcode == 0x3F and w != 0xFFFFFFFF:
        raise IllegalInstruction(f"reserved HALT opcode with non-full word: {w:#010x}")

    by_opcode, _doc = _load_table()
    ent = by_opcode.get(opcode)
    if ent is None:
        raise IllegalInstruction(f"unknown opcode {opcode:#x} in word {w:#010x}")

    fields: dict[str, Any] = {}
    for spec in ent.get("fields", []):
        name = spec["name"]
        hi, lo = spec["bits"]
        fields[name] = _extract_field(w, hi, lo)

    fmt = ent["format"]
    if fmt == "imm16":
        fields["imm32"] = imm16_from_parts(int(fields["immh"]), int(fields["imm11"]))
    elif fmt in ("branch", "load_store", "store", "branch_cond", "strex"):
        fields["imm32"] = sext11(int(fields["imm11"]))

    return Instruction(ent["mnemonic"], fmt, w, fields)
