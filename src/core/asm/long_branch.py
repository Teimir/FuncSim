"""Long-branch veneers when PC-relative offset exceeds imm11."""

from __future__ import annotations

from core.asm.encode import COND_ALIAS, COND_INVERSE, SCRATCH_REG

IMM11_MAX = 1023
IMM11_MIN = -1024


def needs_long_branch(imm_bytes: int) -> bool:
    return imm_bytes < IMM11_MIN or imm_bytes > IMM11_MAX


def _load_address_simple(addr: int) -> list[str]:
    """Load 32-bit byte address into SCRATCH_REG."""
    reg = SCRATCH_REG
    addr &= 0xFFFFFFFF
    low = addr & 0xFFFF
    high = (addr >> 16) & 0xFFFF
    lines: list[str] = []
    if high == 0:
        lines.append(f"ADDI 0 {reg} {low}")
        return lines
    lines.append(f"ADDI 0 {reg} {low}")
    lines.append("ADDI 0 2 16")
    lines.append(f"SLL {reg} 2 {reg}")
    if high <= 0xFFFF:
        lines.append(f"ADDI {reg} {reg} {high}")
    return lines


def _invert_cond_mnemonic(m: str) -> str:
    if m not in COND_ALIAS:
        return m
    inv = COND_INVERSE[COND_ALIAS[m]]
    for name, code in COND_ALIAS.items():
        if code == inv:
            return name
    return "BNE"


def expand_branch(
    mnemonic: str,
    target: int,
    pc: int,
    *,
    cond: bool,
    flag_branch: bool = False,
) -> list[str]:
    """Expand to instruction text lines."""
    m = mnemonic.upper()
    lines: list[str] = []
    scratch = SCRATCH_REG

    if cond and m in COND_ALIAS:
        inv = _invert_cond_mnemonic(m)
        lines.append(f"{inv} 31 4")
        lines.extend(_load_address_simple(target))
        lines.append(f"JMP {scratch} 0")
        return lines

    if flag_branch and m in ("JZ", "JNZ", "JC", "JS", "JO"):
        inv_map = {"JZ": "JNZ", "JNZ": "JZ", "JC": "JS", "JS": "JC", "JO": "JZ"}
        inv = inv_map.get(m, "JNZ")
        lines.append(f"{inv} 31 4")
        lines.extend(_load_address_simple(target))
        lines.append(f"JMP {scratch} 0")
        return lines

    lines.extend(_load_address_simple(target))
    lines.append(f"JMP {scratch} 0")
    return lines
