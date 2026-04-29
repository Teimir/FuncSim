"""Minimal assembler (one instruction per line)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from core.isa_paths import find_opcodes_yaml


class AssembleError(ValueError):
    """Assembly syntax or range error."""


def _split_imm16(imm: int) -> tuple[int, int]:
    u = imm & 0xFFFF
    imm11 = u & 0x7FF
    immh = (u >> 11) & 0x1F
    return immh, imm11


def _imm11_encode(signed: int) -> int:
    if signed < -1024 or signed > 1023:
        raise AssembleError(f"imm11 out of range: {signed}")
    return signed & 0x7FF


@lru_cache(maxsize=1)
def _mnemonic_table() -> dict[str, dict[str, Any]]:
    path = find_opcodes_yaml()
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    out: dict[str, dict[str, Any]] = {}
    for ent in doc["instructions"]:
        out[str(ent["mnemonic"]).upper()] = ent
    return out


def _pack(ent: dict[str, Any], values: dict[str, int]) -> int:
    opc = int(ent["opcode"])
    w = opc << 26
    for spec in ent.get("fields", []):
        name = str(spec["name"])
        hi, lo = spec["bits"]
        width = hi - lo + 1
        mask = (1 << width) - 1
        if name not in values:
            raise AssembleError(f"missing field {name}")
        val = values[name]
        if val < 0 or val > mask:
            raise AssembleError(f"field {name} value {val} out of 0..{mask}")
        w |= (val & mask) << lo
    return w & 0xFFFFFFFF


def assemble_line(line: str) -> int:
    s = line.split("#", 1)[0].strip()
    if not s:
        raise AssembleError("empty line")
    parts = s.replace(",", " ").split()
    if not parts:
        raise AssembleError("empty line")
    mnemonic = parts[0].upper()
    args = [int(x, 0) for x in parts[1:]]

    if mnemonic == "NOP":
        if args:
            raise AssembleError("NOP takes no operands")
        return 0
    if mnemonic == "HALT":
        if args:
            raise AssembleError("HALT takes no operands")
        return 0xFFFFFFFF

    tab = _mnemonic_table()
    if mnemonic not in tab:
        raise AssembleError(f"unknown mnemonic {mnemonic}")
    ent = tab[mnemonic]
    fmt = str(ent["format"])

    if fmt == "bare":
        if args:
            raise AssembleError(f"{mnemonic} takes no operands")
        return _pack(ent, {})

    if fmt == "rrr":
        if len(args) != 3:
            raise AssembleError(f"{mnemonic} r1 r2 res")
        r1, r2, res = args
        return _pack(ent, {"r1": r1, "r2": r2, "res": res})

    if fmt == "mul":
        if len(args) != 4:
            raise AssembleError(f"{mnemonic} r1 r2 res resh")
        r1, r2, res, resh = args
        return _pack(ent, {"r1": r1, "r2": r2, "res": res, "resh": resh})

    if fmt == "imm16":
        if len(args) != 3:
            raise AssembleError(f"{mnemonic} r1 res imm16")
        r1, res, imm = args
        immh, imm11 = _split_imm16(imm)
        return _pack(ent, {"r1": r1, "res": res, "immh": immh, "imm11": imm11})

    if fmt == "branch":
        if len(args) != 2:
            raise AssembleError(f"{mnemonic} raddr imm11")
        raddr, imm = args
        return _pack(ent, {"raddr": raddr, "imm11": _imm11_encode(imm)})

    if fmt == "load_store":
        if len(args) != 4:
            raise AssembleError("LDR raddr rdest mask imm11")
        raddr, rdest, mask, imm = args
        return _pack(ent, {"raddr": raddr, "rdest": rdest, "mask": mask, "imm11": _imm11_encode(imm)})

    if fmt == "store":
        if len(args) != 4:
            raise AssembleError("STR raddr rdata mask imm11")
        raddr, rdata, mask, imm = args
        return _pack(ent, {"raddr": raddr, "rdata": rdata, "mask": mask, "imm11": _imm11_encode(imm)})

    if fmt == "spr":
        if len(args) != 2:
            raise AssembleError("READSPR r1 spr")
        r1, spr = args
        return _pack(ent, {"r1": r1, "spr": spr})

    raise AssembleError(f"unsupported format {fmt} for {mnemonic}")


def assemble_text(text: str) -> list[int]:
    out: list[int] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        frag = raw.split("#", 1)[0].strip()
        if not frag:
            continue
        try:
            out.append(assemble_line(frag))
        except AssembleError as e:
            raise AssembleError(f"line {i}: {e}") from e
    return out
