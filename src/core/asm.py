"""Minimal assembler (one instruction per line; labels, .equ, PUSH/POP)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from core.isa_paths import find_opcodes_yaml


class AssembleError(ValueError):
    """Assembly syntax or range error."""


_COND_ALIAS = {
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

    if mnemonic in _COND_ALIAS:
        if len(args) != 2:
            raise AssembleError(f"{mnemonic} raddr imm11")
        raddr, imm = args
        if raddr < 0 or raddr > 31:
            raise AssembleError("raddr must be 0..31")
        tab = _mnemonic_table()
        ent = tab["BJ"]
        return _pack(
            ent,
            {"cond": _COND_ALIAS[mnemonic], "raddr": raddr, "imm11": _imm11_encode(imm)},
        )

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

    if fmt == "mla":
        if len(args) != 4:
            raise AssembleError(f"{mnemonic} r1 r2 racc res")
        r1, r2, racc, res = args
        return _pack(ent, {"r1": r1, "r2": r2, "racc": racc, "res": res})

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

    if fmt == "branch_cond":
        if len(args) != 3:
            raise AssembleError("BJ cond raddr imm11")
        cond, raddr, imm = args
        if cond < 0 or cond > 15:
            raise AssembleError("cond must be 0..15")
        if raddr < 0 or raddr > 31:
            raise AssembleError("raddr must be 0..31")
        return _pack(ent, {"cond": cond, "raddr": raddr, "imm11": _imm11_encode(imm)})

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
            raise AssembleError("READSPR/WRITESPR r spr")
        r1, spr = args
        return _pack(ent, {"r1": r1, "spr": spr})

    if fmt == "strex":
        if len(args) != 4:
            raise AssembleError("STREX raddr rsrc rstatus imm11")
        raddr, rsrc, rstatus, imm = args
        return _pack(ent, {"raddr": raddr, "rsrc": rsrc, "rstatus": rstatus, "imm11": _imm11_encode(imm)})

    raise AssembleError(f"unsupported format {fmt} for {mnemonic}")


_LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")
_EQU_RE = re.compile(r"^\.equ\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$", re.IGNORECASE)


def _subst_equ(text: str, equ: dict[str, int]) -> str:
    for name, val in sorted(equ.items(), key=lambda x: -len(x[0])):
        text = re.sub(rf"\b{name}\b", str(val), text)
    return text


def _expand_pseudo_line(mnemonic: str, args: list[str]) -> list[str]:
    m = mnemonic.upper()
    if m == "PUSH":
        if len(args) != 1:
            raise AssembleError("PUSH reg")
        r = args[0]
        return ["SUBI 30 30 4", f"STRPOST 30 {r} 15 0"]
    if m == "POP":
        if len(args) != 1:
            raise AssembleError("POP reg")
        r = args[0]
        return [f"LDRPOST 30 {r} 15 0", "ADDI 30 30 4"]
    return []


def _parse_args(s: str, equ: dict[str, int]) -> list[int]:
    s = _subst_equ(s.strip(), equ)
    if not s:
        return []
    return [int(x, 0) for x in s.replace(",", " ").split()]


def _resolve_branch_line(mnemonic: str, args: list[str], labels: dict[str, int], pc: int, equ: dict[str, int]) -> str:
    m = mnemonic.upper()
    if m in _COND_ALIAS and len(args) == 1:
        target = labels.get(args[0])
        if target is None:
            raise AssembleError(f"undefined label {args[0]!r}")
        imm = (target - pc) & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
        if imm < -1024 or imm > 1023:
            raise AssembleError(f"branch offset {imm} out of imm11 range")
        return f"{m} 31 {imm}"
    if m == "B" and len(args) == 1:
        target = labels.get(args[0])
        if target is None:
            raise AssembleError(f"undefined label {args[0]!r}")
        imm = (target - pc) & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
        if imm < -1024 or imm > 1023:
            raise AssembleError(f"branch offset {imm} out of imm11 range")
        return f"JMP 31 {imm}"
    if m in ("JZ", "JNZ", "JC", "JS", "JO") and len(args) == 1:
        target = labels.get(args[0])
        if target is None:
            raise AssembleError(f"undefined label {args[0]!r}")
        imm = (target - pc) & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
        if imm < -1024 or imm > 1023:
            raise AssembleError(f"branch offset {imm} out of imm11 range")
        return f"{m} 31 {imm}"
    if m in ("JZ", "JNZ", "JC", "JS", "JO") and len(args) == 2:
        raddr = int(args[0], 0)
        try:
            imm = int(args[1], 0)
        except ValueError:
            target = labels.get(args[1])
            if target is None:
                raise AssembleError(f"undefined label {args[1]!r}")
            imm = (target - pc) & 0xFFFFFFFF
            if imm & 0x80000000:
                imm = imm - 0x100000000
        if imm < -1024 or imm > 1023:
            raise AssembleError(f"branch offset {imm} out of imm11 range")
        return f"{m} {raddr} {imm}"
    return mnemonic + (" " + " ".join(args) if args else "")


def assemble_text(text: str) -> list[int]:
    equ: dict[str, int] = {}
    labels: dict[str, int] = {}
    pending: list[tuple[int, str, str | None, list[str], int]] = []
    pc = 0

    for i, raw in enumerate(text.splitlines(), start=1):
        frag = raw.split("#", 1)[0].strip()
        if not frag:
            continue
        m_equ = _EQU_RE.match(frag)
        if m_equ:
            equ[m_equ.group(1)] = int(_subst_equ(m_equ.group(2).strip(), equ), 0)
            continue
        m_label = _LABEL_RE.match(frag)
        if m_label:
            labels[m_label.group(1)] = pc
            frag = m_label.group(2).strip()
            if not frag:
                continue
        parts = _subst_equ(frag, equ).replace(",", " ").split()
        mnemonic = parts[0].upper()
        args = parts[1:]
        for expanded in _expand_pseudo_line(mnemonic, args):
            pending.append((i, expanded, None, [], pc))
            pc += 4
        if mnemonic in ("PUSH", "POP"):
            continue
        if mnemonic in _COND_ALIAS and len(args) == 1:
            pending.append((i, "", mnemonic, args, pc))
        elif mnemonic == "B" and len(args) == 1:
            pending.append((i, "", mnemonic, args, pc))
        elif mnemonic in ("JZ", "JNZ", "JC", "JS", "JO") and len(args) == 1:
            pending.append((i, "", mnemonic, args, pc))
        elif mnemonic in ("JZ", "JNZ", "JC", "JS", "JO") and len(args) == 2:
            pending.append((i, "", mnemonic, args, pc))
            pc += 4
            continue
        else:
            pending.append((i, frag, None, [], pc))
        pc += 4

    out: list[int] = []
    for line_no, text, mnemonic, args, at_pc in pending:
        if text:
            line = text
        else:
            line = _resolve_branch_line(mnemonic, args, labels, at_pc, equ)
        try:
            out.append(assemble_line(_subst_equ(line, equ)))
        except AssembleError as e:
            raise AssembleError(f"line {line_no}: {e}") from e
    return out


def assemble_file(path: Path | str) -> list[int]:
    p = Path(path)
    return assemble_text(p.read_text(encoding="utf-8"))
