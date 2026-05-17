"""Execute one decoded instruction."""

from __future__ import annotations

from core import flags as F
from core.instruction import Instruction
from core.mem_if import WordMemory
from core.state import SPR_SAVED_IRQ_PC, CPUState


def _u32(x: int) -> int:
    return x & 0xFFFFFFFF


_S32_MIN = -(1 << 31)
_S32_MAX = (1 << 31) - 1


def _s32(x: int) -> int:
    """Two's-complement signed 32-bit value (Python int in range [-2³¹, 2³¹-1])."""
    x = _u32(x)
    return x - (1 << 32) if x & 0x80000000 else x


def _ror32(x: int, k: int) -> int:
    k &= 31
    x = _u32(x)
    if k == 0:
        return x
    return _u32((x >> k) | (x << (32 - k)))


def _rol32(x: int, k: int) -> int:
    k &= 31
    x = _u32(x)
    if k == 0:
        return x
    return _u32((x << k) | (x >> (32 - k)))


def _adds_flags(a: int, b: int) -> tuple[int, int]:
    """ADDS: signed 32-bit addition (two's complement), result truncated to 32 bits.

    Operands are interpreted as signed; the stored result is ``(s32(a)+s32(b)) & 0xFFFFFFFF``.
    **V** is set iff the mathematical sum is outside signed 32-bit range.
    **C** is unsigned carry out of bit 31 (ARM-style); **Z**/**S** from the truncated result.
    """
    sa = _s32(a)
    sb = _s32(b)
    sum_wide = sa + sb
    res = sum_wide & 0xFFFFFFFF
    au, bu = _u32(a), _u32(b)
    c = (au + bu) > 0xFFFFFFFF
    v = not (_S32_MIN <= sum_wide <= _S32_MAX)
    z = res == 0
    s = bool(res & 0x80000000)
    return res, F.flags_set_zcs(0, z=z, c=c, v=v, s=s)


def _subs_flags(a: int, b: int) -> tuple[int, int]:
    """SUBS: signed 32-bit subtraction ``s32(a) - s32(b)``, result truncated to 32 bits.

    **V** iff the mathematical difference is outside signed 32-bit range.
    **C** is ``1`` when there is no unsigned borrow (``u32(a) >= u32(b)``), ARM-style.
    """
    sa = _s32(a)
    sb = _s32(b)
    diff_wide = sa - sb
    res = diff_wide & 0xFFFFFFFF
    au, bu = _u32(a), _u32(b)
    c = au >= bu
    v = not (_S32_MIN <= diff_wide <= _S32_MAX)
    z = res == 0
    s = bool(res & 0x80000000)
    return res, F.flags_set_zcs(0, z=z, c=c, v=v, s=s)


def _adcs_flags(a: int, b: int, c_in: bool) -> tuple[int, int]:
    au, bu = _u32(a), _u32(b)
    cin = 1 if c_in else 0
    sum_u = au + bu + cin
    res = sum_u & 0xFFFFFFFF
    c = sum_u > 0xFFFFFFFF
    sa, sb = _s32(a), _s32(b)
    sum_wide = sa + sb + cin
    v = not (_S32_MIN <= sum_wide <= _S32_MAX)
    z = res == 0
    s = bool(res & 0x80000000)
    return res, F.flags_set_zcs(0, z=z, c=c, v=v, s=s)


def _sbcs_flags(a: int, b: int, c_old: bool) -> tuple[int, int]:
    au, bu = _u32(a), _u32(b)
    borrow = 0 if c_old else 1
    total = au - bu - borrow
    res = total & 0xFFFFFFFF
    c = total >= 0
    sa, sb = _s32(a), _s32(b)
    diff_wide = sa - sb - borrow
    v = not (_S32_MIN <= diff_wide <= _S32_MAX)
    z = res == 0
    s = bool(res & 0x80000000)
    return res, F.flags_set_zcs(0, z=z, c=c, v=v, s=s)


def _flags_logical(res: int) -> int:
    """ANDS: Z,S from result; C=V=0 (ARM-style logical, no barrel shifter carry)."""
    return F.flags_set_zcs(0, z=res == 0, c=False, v=False, s=bool(res & 0x80000000))


def _branch_cond_take(cond: int, flags: int) -> bool:
    z = bool(flags & F.FLAG_ZERO)
    c = bool(flags & F.FLAG_CARRY)
    s = bool(flags & F.FLAG_SIGN)
    v = bool(flags & F.FLAG_OVERFLOW)
    sv = s ^ v
    if cond == 0:
        return z
    if cond == 1:
        return not z
    if cond == 2:
        return c
    if cond == 3:
        return not c
    if cond == 4:
        return s
    if cond == 5:
        return not s
    if cond == 6:
        return v
    if cond == 7:
        return not v
    if cond == 8:
        return c and not z
    if cond == 9:
        return (not c) or z
    if cond == 10:
        return not sv
    if cond == 11:
        return sv
    if cond == 12:
        return (not z) and (not sv)
    if cond == 13:
        return z or sv
    if cond == 14:
        return True
    return False


def _apply_zcs_to_state(state: CPUState, fl_word: int) -> None:
    state.flags = F.flags_set_zcs(
        state.flags,
        z=bool(fl_word & F.FLAG_ZERO),
        c=bool(fl_word & F.FLAG_CARRY),
        v=bool(fl_word & F.FLAG_OVERFLOW),
        s=bool(fl_word & F.FLAG_SIGN),
    )


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


def execute(state: CPUState, mem: WordMemory, ins: Instruction) -> bool:
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
            state.irq_in_service = False
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
            _apply_zcs_to_state(state, fl)
        elif m == "SUBS":
            val, fl = _subs_flags(a, b)
            state.reg_write(res_i, val)
            _apply_zcs_to_state(state, fl)
        elif m == "ADC":
            cin = bool(state.flags & F.FLAG_CARRY)
            state.reg_write(res_i, _u32(_u32(a) + _u32(b) + (1 if cin else 0)))
        elif m == "ADCS":
            val, fl = _adcs_flags(a, b, bool(state.flags & F.FLAG_CARRY))
            state.reg_write(res_i, val)
            _apply_zcs_to_state(state, fl)
        elif m == "SBC":
            borrow = 0 if (state.flags & F.FLAG_CARRY) else 1
            state.reg_write(res_i, _u32(_u32(a) - _u32(b) - borrow))
        elif m == "SBCS":
            val, fl = _sbcs_flags(a, b, bool(state.flags & F.FLAG_CARRY))
            state.reg_write(res_i, val)
            _apply_zcs_to_state(state, fl)
        elif m == "AND":
            state.reg_write(res_i, a & b)
        elif m == "ANDS":
            val = _u32(a & b)
            state.reg_write(res_i, val)
            _apply_zcs_to_state(state, _flags_logical(val))
        elif m == "OR":
            state.reg_write(res_i, a | b)
        elif m == "XOR":
            state.reg_write(res_i, a ^ b)
        elif m == "BIC":
            state.reg_write(res_i, _u32(a & (~_u32(b))))
        elif m == "MVN":
            state.reg_write(res_i, _u32(~_u32(b)))
        elif m == "NEG":
            state.reg_write(res_i, _u32(-_s32(b)))
        elif m in ("SLL", "SAL"):
            sh = b & 0x1F
            state.reg_write(res_i, _u32(a << sh))
        elif m == "SLR":
            sh = b & 0x1F
            state.reg_write(res_i, _u32(a >> sh))
        elif m == "ROR":
            sh = b & 0x1F
            state.reg_write(res_i, _ror32(a, sh))
        elif m == "ROL":
            sh = b & 0x1F
            state.reg_write(res_i, _rol32(a, sh))
        elif m == "SMUL":
            state.reg_write(res_i, (_s32(a) * _s32(b)) & 0xFFFFFFFF)
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
        if m in ("MUL", "UMULL"):
            au = _u32(a)
            bu = _u32(b)
            prod64 = au * bu
            state.reg_write(res_i, _u32(prod64))
            state.reg_write(resh, _u32(prod64 >> 32))
        elif m == "SMULL":
            sa, sb = _s32(a), _s32(b)
            prod = sa * sb
            state.reg_write(res_i, prod & 0xFFFFFFFF)
            state.reg_write(resh, (prod >> 32) & 0xFFFFFFFF)
        else:
            raise NotImplementedError(m)
        return False

    if f == "mla":
        r1 = int(fld["r1"])
        r2 = int(fld["r2"])
        racc = int(fld["racc"])
        res_i = int(fld["res"])
        a = state.reg_read(r1)
        b = state.reg_read(r2)
        acc = state.reg_read(racc)
        if m != "MLA":
            raise NotImplementedError(m)
        state.reg_write(res_i, _u32(_u32(a * b) + acc))
        return False

    if f == "imm16":
        r1 = int(fld["r1"])
        res_i = int(fld["res"])
        imm = int(fld["imm32"])
        a = state.reg_read(r1)
        if m == "ADDI":
            state.reg_write(res_i, _u32(a + imm))
        elif m == "SUBI":
            val = _u32(a - imm)
            state.reg_write(res_i, val)
            state.flags = (state.flags & ~F.FLAG_ZERO) | (
                F.FLAG_ZERO if val == 0 else 0
            )
        elif m == "ADDSI":
            val, fl = _adds_flags(a, imm)
            state.reg_write(res_i, val)
            _apply_zcs_to_state(state, fl)
        elif m == "SUBSI":
            val, fl = _subs_flags(a, imm)
            state.reg_write(res_i, val)
            _apply_zcs_to_state(state, fl)
        else:
            raise NotImplementedError(m)
        return False

    if f == "load_store":
        raddr = int(fld["raddr"])
        rdest = int(fld["rdest"])
        mask = int(fld["mask"])
        imm = int(fld["imm32"])
        base = state.reg_read(raddr)
        if m == "LDR":
            ea = _u32(base + imm)
        elif m == "LDRPOST":
            ea = _u32(base)
        elif m == "LDRPRE":
            base = _u32(base + imm)
            state.reg_write(raddr, base)
            ea = base
        elif m == "LDREX":
            ea = _u32(base + imm)
            state.exclusive_addr = ea
            state.exclusive_valid = True
        else:
            raise NotImplementedError(m)
        if mask == 0:
            state.reg_write(rdest, 0)
        else:
            w = mem.read_word(ea)
            state.reg_write(rdest, _apply_ldr_mask(w, mask))
        if m == "LDRPOST":
            state.reg_write(raddr, _u32(base + imm))
        return False

    if f == "store":
        raddr = int(fld["raddr"])
        rdata = int(fld["rdata"])
        mask = int(fld["mask"])
        imm = int(fld["imm32"])
        base = state.reg_read(raddr)
        if m == "STR":
            ea = _u32(base + imm)
            state.exclusive_valid = False
        elif m == "STRPOST":
            ea = _u32(base)
            state.exclusive_valid = False
        elif m == "STRPRE":
            base = _u32(base + imm)
            state.reg_write(raddr, base)
            ea = base
            state.exclusive_valid = False
        else:
            raise NotImplementedError(m)
        if mask == 0:
            if m in ("STRPOST", "STRPRE"):
                state.reg_write(raddr, _u32(base + imm))
            return False
        old = mem.read_word(ea)
        v = state.reg_read(rdata)
        mem.write_word(ea, _merge_str_mask(old, v, mask))
        if m == "STRPOST":
            state.reg_write(raddr, _u32(base + imm))
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

    if f == "branch_cond":
        raddr = int(fld["raddr"])
        imm = int(fld["imm32"])
        cond = int(fld["cond"])
        target = _u32(state.reg_read(raddr) + imm)
        if _branch_cond_take(cond, state.flags):
            state.set_pc(target)
            return True
        return False

    if f == "strex":
        raddr = int(fld["raddr"])
        rsrc = int(fld["rsrc"])
        rstatus = int(fld["rstatus"])
        imm = int(fld["imm32"])
        ea = _u32(state.reg_read(raddr) + imm)
        ok = state.exclusive_valid and state.exclusive_addr == ea
        state.exclusive_valid = False
        if ok:
            mem.write_word(ea, state.reg_read(rsrc))
            state.reg_write(rstatus, 0)
        else:
            state.reg_write(rstatus, 1)
        return False

    if f == "spr":
        r1 = int(fld["r1"])
        spr_i = int(fld["spr"])
        if m == "READSPR":
            state.reg_write(r1, state.spr_read(spr_i))
        elif m == "WRITESPR":
            state.spr_write(spr_i, state.reg_read(r1))
        else:
            raise NotImplementedError(m)
        return False

    raise NotImplementedError(f"{m} {f}")
