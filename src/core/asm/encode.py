"""Instruction encoding from opcodes.yaml."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from core.asm.errors import AssembleError
from core.isa_paths import find_opcodes_yaml

COND_ALIAS = {
    "BEQ": 0,
    "BNE": 1,
    "BCS": 2,
    "BHS": 2,
    "BCC": 3,
    "BLO": 3,
    "BMI": 4,
    "BPL": 5,
    "BVS": 6,
    "BVC": 7,
    "BHI": 8,
    "BLS": 9,
    "BGE": 10,
    "BLT": 11,
    "BGT": 12,
    "BLE": 13,
    "BAL": 14,
}

COND_INVERSE = {
    0: 1,
    1: 0,
    2: 3,
    3: 2,
    4: 5,
    5: 4,
    6: 7,
    7: 6,
    8: 9,
    9: 8,
    10: 11,
    11: 10,
    12: 13,
    13: 12,
    14: 14,
}

SCRATCH_REG = 14


def split_imm16(imm: int) -> tuple[int, int]:
    u = imm & 0xFFFF
    imm11 = u & 0x7FF
    immh = (u >> 11) & 0x1F
    return immh, imm11


def imm11_encode(signed: int) -> int:
    if signed < -1024 or signed > 1023:
        raise AssembleError(f"imm11 out of range: {signed}")
    return signed & 0x7FF


@lru_cache(maxsize=1)
def mnemonic_table() -> dict[str, dict[str, Any]]:
    path = find_opcodes_yaml()
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    out: dict[str, dict[str, Any]] = {}
    for ent in doc["instructions"]:
        out[str(ent["mnemonic"]).upper()] = ent
    return out


def pack(ent: dict[str, Any], values: dict[str, int]) -> int:
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
    try:
        args = [int(x, 0) for x in parts[1:]]
    except ValueError:
        from core.asm.parse import parse_line_body

        mnemonic, args = parse_line_body(s, {})

    if mnemonic == "NOP":
        if args:
            raise AssembleError("NOP takes no operands")
        return 0
    if mnemonic == "HALT":
        if args:
            raise AssembleError("HALT takes no operands")
        return 0xFFFFFFFF

    if mnemonic == "CMP":
        if len(args) != 2:
            raise AssembleError("CMP r1 r2")
        return assemble_line(f"SUBS {args[0]} {args[1]} 0")
    if mnemonic == "CMN":
        if len(args) != 2:
            raise AssembleError("CMN r1 r2")
        return assemble_line(f"ADDS {args[0]} {args[1]} 0")
    if mnemonic in ("TST", "TEST"):
        if len(args) != 2:
            raise AssembleError("TST r1 r2")
        return assemble_line(f"ANDS {args[0]} {args[1]} 0")
    if mnemonic in ("MOV", "MOVI"):
        if len(args) != 2:
            raise AssembleError("MOV dst imm16")
        return assemble_line(f"ADDI 0 {args[0]} {args[1]}")

    if mnemonic in COND_ALIAS:
        if len(args) != 2:
            raise AssembleError(f"{mnemonic} raddr imm11")
        raddr, imm = args
        if raddr < 0 or raddr > 31:
            raise AssembleError("raddr must be 0..31")
        tab = mnemonic_table()
        ent = tab["BJ"]
        return pack(
            ent,
            {"cond": COND_ALIAS[mnemonic], "raddr": raddr, "imm11": imm11_encode(imm)},
        )

    tab = mnemonic_table()
    if mnemonic not in tab:
        raise AssembleError(f"unknown mnemonic {mnemonic}")
    ent = tab[mnemonic]
    fmt = str(ent["format"])

    if fmt == "bare":
        if args:
            raise AssembleError(f"{mnemonic} takes no operands")
        return pack(ent, {})

    if fmt == "rrr":
        if len(args) != 3:
            raise AssembleError(f"{mnemonic} r1 r2 res")
        r1, r2, res = args
        return pack(ent, {"r1": r1, "r2": r2, "res": res})

    if fmt == "mul":
        if len(args) != 4:
            raise AssembleError(f"{mnemonic} r1 r2 res resh")
        r1, r2, res, resh = args
        return pack(ent, {"r1": r1, "r2": r2, "res": res, "resh": resh})

    if fmt == "mla":
        if len(args) != 4:
            raise AssembleError(f"{mnemonic} r1 r2 racc res")
        r1, r2, racc, res = args
        return pack(ent, {"r1": r1, "r2": r2, "racc": racc, "res": res})

    if fmt == "imm16":
        if len(args) != 3:
            raise AssembleError(f"{mnemonic} r1 res imm16")
        r1, res, imm = args
        immh, imm11 = split_imm16(imm)
        return pack(ent, {"r1": r1, "res": res, "immh": immh, "imm11": imm11})

    if fmt == "branch":
        if len(args) != 2:
            raise AssembleError(f"{mnemonic} raddr imm11")
        raddr, imm = args
        return pack(ent, {"raddr": raddr, "imm11": imm11_encode(imm)})

    if fmt == "branch_cond":
        if len(args) != 3:
            raise AssembleError("BJ cond raddr imm11")
        cond, raddr, imm = args
        if cond < 0 or cond > 15:
            raise AssembleError("cond must be 0..15")
        if raddr < 0 or raddr > 31:
            raise AssembleError("raddr must be 0..31")
        return pack(ent, {"cond": cond, "raddr": raddr, "imm11": imm11_encode(imm)})

    if fmt == "load_store":
        if len(args) != 4:
            raise AssembleError("LDR raddr rdest mask imm11")
        raddr, rdest, mask, imm = args
        return pack(ent, {"raddr": raddr, "rdest": rdest, "mask": mask, "imm11": imm11_encode(imm)})

    if fmt == "store":
        if len(args) != 4:
            raise AssembleError("STR raddr rdata mask imm11")
        raddr, rdata, mask, imm = args
        return pack(ent, {"raddr": raddr, "rdata": rdata, "mask": mask, "imm11": imm11_encode(imm)})

    if fmt == "spr":
        if len(args) != 2:
            raise AssembleError("READSPR/WRITESPR r spr")
        r1, spr = args
        return pack(ent, {"r1": r1, "spr": spr})

    if fmt == "strex":
        if len(args) != 4:
            raise AssembleError("STREX raddr rsrc rstatus imm11")
        raddr, rsrc, rstatus, imm = args
        return pack(ent, {"raddr": raddr, "rsrc": rsrc, "rstatus": rstatus, "imm11": imm11_encode(imm)})

    raise AssembleError(f"unsupported format {fmt} for {mnemonic}")
