"""Execute one decoded instruction."""

from __future__ import annotations

from core import flags as F
from core.instruction import Instruction
from core.memory import Memory
from core.state import CPUState, SPR_SAVED_IRQ_PC


def _u32(x: int) -> int:
    return x & 0xFFFFFFFF


def _adds_flags(a: int, b: int) -> tuple[int, int]:
    """Return (result_u32, new_flags_word) for Z,C,V,S (Intenable not set here)."""
    au = _u32(a)
    bu = _u32(b)
    res = _u32(au + bu)
    carry = 1 if (au + bu) > 0xFFFFFFFF else 0
    overflow = 1 if ((~(au ^ bu)) & (au ^ res) & 0x80000000) else 0
    z = 1 if res == 0 else 0
    s = 1 if (res & 0x80000000) else 0
    return res, F.flags_set_zcs(0, z=bool(z), c=bool(carry), v=bool(overflow), s=bool(s))


def _subs_flags(a: int, b: int) -> tuple[int, int]:
    au = _u32(a)
    bu = _u32(b)
    res = _u32(au - bu)
    carry = 1 if au >= bu else 0  # NOT borrow
    overflow = 1 if ((au ^ bu) & (au ^ res) & 0x80000000) else 0
    z = 1 if res == 0 else 0
    s = 1 if (res & 0x80000000) else 0
    return res, F.flags_set_zcs(0, z=bool(z), c=bool(carry), v=bool(overflow), s=bool(s))


def _apply_ldr_mask(word: int, mask: int) -> int:
    out = 0
    for k in range(4):
        if mask & (1 << k):
            out |= ((word >> (8 * k)) & 0xFF) << (8 * k)
    return _u32(out)


def _merge_str_mask(old: int, value: int, mask: int) -> int:
    w = old
    for k in range(4):
        if mask & (1 << k):
            byte = (value >> (8 * k)) & 0xFF
            w = (w & ~(0xFF << (8 * k))) | (byte << (8 * k))
    return _u32(w)


def execute(state: CPUState, mem: Memory, ins: Instruction) -> bool:
    """
    Mutate state and memory.
    Returns True if PC was explicitly written (no +4 bump by runner).
    """
    m = ins.mnemonic
    f = ins.format
    fld = ins.fields

    if m == "NOP" and f == "special_nop":
        return False

    if m == "HALT" and f == "special_halt":
        state.halted = True
        return True

    if f == "bare":
        if m == "EI":
            state.flags |= F.FLAG_INTENABLE
            return False
        if m == "DI":
            state.flags &= ~F.FLAG_INTENABLE
            return False
        if m == "IRET":
            state.set_pc(state.spr_read(SPR_SAVED_IRQ_PC))
            return True
        raise NotImplementedError(m)

    if f == "rrr":
        r1 = int(fld["r1"])
        r2 = int(fld["r2"])
        res_i = int(fld["res"])
        a = state.reg_read(r1)
        b = state.reg_read(r2)
        if m == "ADD":
            state.reg_write(res_i, _u32(a + b))
        elif m == "SUB":
            state.reg_write(res_i, _u32(a - b))
        elif m == "ADDS":
            val, fl = _adds_flags(a, b)
            state.reg_write(res_i, val)
            state.flags = F.flags_set_zcs(state.flags, z=bool(fl & F.FLAG_ZERO), c=bool(fl & F.FLAG_CARRY), v=bool(fl & F.FLAG_OVERFLOW), s=bool(fl & F.FLAG_SIGN))
        elif m == "SUBS":
            val, fl = _subs_flags(a, b)
            state.reg_write(res_i, val)
            state.flags = F.flags_set_zcs(state.flags, z=bool(fl & F.FLAG_ZERO), c=bool(fl & F.FLAG_CARRY), v=bool(fl & F.FLAG_OVERFLOW), s=bool(fl & F.FLAG_SIGN))
        elif m == "AND":
            state.reg_write(res_i, a & b)
        elif m == "OR":
            state.reg_write(res_i, a | b)
        elif m == "XOR":
            state.reg_write(res_i, a ^ b)
        elif m in ("SLL", "SAL"):
            sh = b & 0x1F
            state.reg_write(res_i, _u32(a << sh))
        elif m == "SLR":
            sh = b & 0x1F
            state.reg_write(res_i, _u32(a >> sh))
        else:
            raise NotImplementedError(m)
        return False

    if f == "mul":
        r1 = int(fld["r1"])
        r2 = int(fld["r2"])
        res_i = int(fld["res"])
        resh = int(fld["resh"])
        a = state.reg_read(r1)
        b = state.reg_read(r2)
        if m != "MUL":
            raise NotImplementedError(m)
        au = _u32(a)
        bu = _u32(b)
        prod64 = au * bu
        state.reg_write(res_i, _u32(prod64))
        state.reg_write(resh, _u32(prod64 >> 32))
        return False

    if f == "imm16":
        r1 = int(fld["r1"])
        res_i = int(fld["res"])
        imm = int(fld["imm32"])
        a = state.reg_read(r1)
        if m == "ADDI":
            state.reg_write(res_i, _u32(a + imm))
        elif m == "SUBI":
            state.reg_write(res_i, _u32(a - imm))
        else:
            raise NotImplementedError(m)
        return False

    if f == "load_store":
        raddr = int(fld["raddr"])
        rdest = int(fld["rdest"])
        mask = int(fld["mask"])
        imm = int(fld["imm32"])
        ea = _u32(state.reg_read(raddr) + imm)
        if mask == 0:
            state.reg_write(rdest, 0)
            return False
        w = mem.read_word(ea)
        state.reg_write(rdest, _apply_ldr_mask(w, mask))
        return False

    if f == "store":
        raddr = int(fld["raddr"])
        rdata = int(fld["rdata"])
        mask = int(fld["mask"])
        imm = int(fld["imm32"])
        ea = _u32(state.reg_read(raddr) + imm)
        if mask == 0:
            return False
        old = mem.read_word(ea)
        v = state.reg_read(rdata)
        mem.write_word(ea, _merge_str_mask(old, v, mask))
        return False

    if f == "branch":
        raddr = int(fld["raddr"])
        imm = int(fld["imm32"])
        target = _u32(state.reg_read(raddr) + imm)
        take = False
        if m == "JMP":
            take = True
        elif m == "JZ":
            take = bool(state.flags & F.FLAG_ZERO)
        elif m == "JNZ":
            take = not bool(state.flags & F.FLAG_ZERO)
        elif m == "JC":
            take = bool(state.flags & F.FLAG_CARRY)
        elif m == "JS":
            take = bool(state.flags & F.FLAG_SIGN)
        elif m == "JO":
            take = bool(state.flags & F.FLAG_OVERFLOW)
        else:
            raise NotImplementedError(m)
        if take:
            state.set_pc(target)
            return True
        return False

    if f == "spr":
        r1 = int(fld["r1"])
        spr_i = int(fld["spr"])
        state.reg_write(r1, state.spr_read(spr_i))
        return False

    raise NotImplementedError(f"{m} {f}")
