"""Pretty-print decoded instructions."""

from __future__ import annotations

from core.decode import decode_word
from core.exceptions import IllegalInstruction
from core.instruction import Instruction


def _imm11_signed(v: int) -> int:
    v &= 0x7FF
    if v & 0x400:
        return v - 0x800
    return v


def _imm32_signed(u: int) -> int:
    u &= 0xFFFFFFFF
    if u & 0x80000000:
        return u - 0x100000000
    return u


def format_instruction(ins: Instruction) -> str:
    m = ins.mnemonic
    f = ins.format
    fld = ins.fields

    if f == "special_nop":
        return "NOP"
    if f == "special_halt":
        return "HALT"
    if f == "bare":
        return m

    if f == "rrr":
        return f"{m} r{fld['r1']} r{fld['r2']} r{fld['res']}"

    if f == "mul":
        return f"{m} r{fld['r1']} r{fld['r2']} r{fld['res']} r{fld['resh']}"

    if f == "imm16":
        imm = _imm32_signed(int(fld["imm32"]))
        return f"{m} r{fld['r1']} r{fld['res']} {imm}"

    if f in ("branch",):
        imm = _imm11_signed(int(fld["imm11"]))
        return f"{m} r{fld['raddr']} {imm}"

    if f == "load_store":
        imm = _imm11_signed(int(fld["imm11"]))
        return f"{m} r{fld['raddr']} r{fld['rdest']} {fld['mask']} {imm}"

    if f == "store":
        imm = _imm11_signed(int(fld["imm11"]))
        return f"{m} r{fld['raddr']} r{fld['rdata']} {fld['mask']} {imm}"

    if f == "spr":
        return f"{m} r{fld['r1']} {fld['spr']}"

    return f"{m} <{f}>"


def disassemble_word(word: int) -> str:
    try:
        ins = decode_word(word & 0xFFFFFFFF)
    except IllegalInstruction:
        return f".word 0x{word & 0xFFFFFFFF:08x}  ; illegal"
    return format_instruction(ins)
