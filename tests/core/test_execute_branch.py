from core import flags as F
from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


def test_jmp_sets_pc_explicit() -> None:
    s = CPUState()
    m = Memory(256)
    ins = decode_word(0x40A00004)
    s.reg_write(5, 0x10)
    assert execute(s, m, ins) is True
    assert s.pc == 0x14


def test_jz_taken() -> None:
    s = CPUState()
    m = Memory(256)
    s.flags |= F.FLAG_ZERO
    # JZ same encoding pattern as JMP opcode 010001 = 0x11
    w = 0x44A00004  # 0x11<<26 | 5<<21 | 4
    ins = decode_word(w)
    s.reg_write(5, 0x10)
    assert execute(s, m, ins) is True
    assert s.pc == 0x14


def test_jz_not_taken() -> None:
    s = CPUState()
    m = Memory(256)
    s.flags &= ~F.FLAG_ZERO
    w = 0x44A00004
    ins = decode_word(w)
    s.reg_write(5, 0x10)
    assert execute(s, m, ins) is False
