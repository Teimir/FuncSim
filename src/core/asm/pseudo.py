"""Pseudo-instructions and branch resolution."""

from __future__ import annotations

from core.asm.encode import COND_ALIAS
from core.asm.errors import AssembleError
from core.asm.long_branch import expand_branch, needs_long_branch

BRANCH_MNEMONICS = ("JZ", "JNZ", "JC", "JS", "JO")


def expand_pseudo_line(mnemonic: str, args: list[str]) -> list[str]:
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


def branch_offset(target: int, pc: int) -> int:
    imm = (target - pc) & 0xFFFFFFFF
    if imm & 0x80000000:
        imm -= 0x100000000
    return imm


def resolve_branch_to_lines(
    mnemonic: str,
    args: list[str],
    labels: dict[str, int],
    pc: int,
) -> list[str]:
    """Resolve branch pseudo to one or more instruction lines (may use long-branch)."""
    m = mnemonic.upper()
    if m in COND_ALIAS and len(args) == 1:
        target = labels.get(args[0])
        if target is None:
            raise AssembleError(f"undefined label {args[0]!r}")
        imm = branch_offset(target, pc)
        if needs_long_branch(imm):
            return expand_branch(m, target, pc, cond=True)
        return [f"{m} 31 {imm}"]
    if m == "B" and len(args) == 1:
        target = labels.get(args[0])
        if target is None:
            raise AssembleError(f"undefined label {args[0]!r}")
        imm = branch_offset(target, pc)
        if needs_long_branch(imm):
            return expand_branch("JMP", target, pc, cond=False)
        return [f"JMP 31 {imm}"]
    if m == "JMP" and len(args) == 1:
        target = labels.get(args[0])
        if target is None:
            raise AssembleError(f"undefined label {args[0]!r}")
        imm = branch_offset(target, pc)
        if needs_long_branch(imm):
            return expand_branch("JMP", target, pc, cond=False)
        return [f"JMP 31 {imm}"]
    if m in BRANCH_MNEMONICS and len(args) == 1:
        target = labels.get(args[0])
        if target is None:
            raise AssembleError(f"undefined label {args[0]!r}")
        imm = branch_offset(target, pc)
        if needs_long_branch(imm):
            return expand_branch(m, target, pc, cond=True, flag_branch=True)
        return [f"{m} 31 {imm}"]
    if m in BRANCH_MNEMONICS and len(args) == 2:
        raddr = int(args[0], 0)
        try:
            imm = int(args[1], 0)
        except ValueError:
            target = labels.get(args[1])
            if target is None:
                raise AssembleError(f"undefined label {args[1]!r}")
            imm = branch_offset(target, pc)
        if needs_long_branch(imm):
            raise AssembleError(f"branch offset {imm} out of imm11 range (use label form)")
        return [f"{m} {raddr} {imm}"]
    return []
