from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState
from core import flags as F


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
