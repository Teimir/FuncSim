from core import flags as F
from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


def test_add_execute() -> None:
    s = CPUState()
    m = Memory(256)
    ins = decode_word(0x84221800)
    s.reg_write(1, 5)
    s.reg_write(2, 7)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 12


def test_adds_zero_flag() -> None:
    s = CPUState()
    m = Memory(256)
    ins = decode_word(0x8C221800)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 0
    assert s.flags & F.FLAG_ZERO


def test_adds_signed_overflow_max_plus_one() -> None:
    """0x7fffffff + 1 signed overflows; result is INT_MIN pattern, V=1."""
    s = CPUState()
    m = Memory(256)
    ins = decode_word(0x8C221800)  # ADDS r1 r2 -> r3
    s.reg_write(1, 0x7FFFFFFF)
    s.reg_write(2, 1)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 0x80000000
    assert s.flags & F.FLAG_OVERFLOW
    assert s.flags & F.FLAG_SIGN
    assert not (s.flags & F.FLAG_ZERO)


def test_subs_signed_overflow_int_min_minus_one() -> None:
    """INT_MIN - 1 signed overflows; result is INT_MAX pattern, V=1."""
    s = CPUState()
    m = Memory(256)
    # SUBS: opcode 0b100100 = 0x24 -> 0x24<<26 | 1<<21 | 2<<16 | 3<<11
    ins = decode_word(0x90221800)
    s.reg_write(1, 0x80000000)
    s.reg_write(2, 1)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 0x7FFFFFFF
    assert s.flags & F.FLAG_OVERFLOW


def test_subs_no_overflow_small_values() -> None:
    s = CPUState()
    m = Memory(256)
    ins = decode_word(0x90221800)
    s.reg_write(1, 10)
    s.reg_write(2, 3)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 7
    assert not (s.flags & F.FLAG_OVERFLOW)
    assert not (s.flags & F.FLAG_ZERO)


def test_mul_64bit() -> None:
    s = CPUState()
    m = Memory(256)
    # MUL opcode 0b101100 (44); word = 44<<26 | 1<<21 | 2<<16 | 3<<11 | 4<<6
    w = 0xB0221900
    ins = decode_word(w)
    s.reg_write(1, 0x10000)
    s.reg_write(2, 0x10000)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 0
    assert s.reg_read(4) == 1


def test_addi() -> None:
    s = CPUState()
    m = Memory(256)
    # ADDI r1=1 res=2 imm16=4 -> immh=0 imm11=4
    w = 0xC0201004
    ins = decode_word(w)
    s.reg_write(1, 10)
    assert execute(s, m, ins) is False
    assert s.reg_read(2) == 14
