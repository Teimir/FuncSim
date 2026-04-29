"""Status flag bit positions (see docs/isa/spec.md)."""

FLAG_INTENABLE = 1 << 0
FLAG_ZERO = 1 << 1
FLAG_CARRY = 1 << 2
FLAG_OVERFLOW = 1 << 3
FLAG_SIGN = 1 << 4

ALL_STATUS = FLAG_INTENABLE | FLAG_ZERO | FLAG_CARRY | FLAG_OVERFLOW | FLAG_SIGN


def flags_set_zcs(flags: int, *, z: bool, c: bool, v: bool, s: bool) -> int:
    """Return new flags word with Z/C/V/S updated; Intenable preserved."""
    flags &= ~ (FLAG_ZERO | FLAG_CARRY | FLAG_OVERFLOW | FLAG_SIGN)
    if z:
        flags |= FLAG_ZERO
    if c:
        flags |= FLAG_CARRY
    if v:
        flags |= FLAG_OVERFLOW
    if s:
        flags |= FLAG_SIGN
    return flags
