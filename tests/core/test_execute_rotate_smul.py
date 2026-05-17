from core.asm import assemble_line
from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


def test_ror_1() -> None:
    s = CPUState()
    m = Memory(64)
    ins = decode_word(assemble_line("ROR 1 2 3"))
    s.reg_write(1, 0x80000001)
    s.reg_write(2, 1)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 0xC0000000


def test_rol_1() -> None:
    s = CPUState()
    m = Memory(64)
    ins = decode_word(assemble_line("ROL 1 2 3"))
    s.reg_write(1, 0x40000000)
    s.reg_write(2, 1)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 0x80000000


def test_smul_signed() -> None:
    s = CPUState()
    m = Memory(64)
    ins = decode_word(assemble_line("SMUL 1 2 3"))
    s.reg_write(1, 3)
    s.reg_write(2, 0xFFFFFFFE)
    assert execute(s, m, ins) is False
    assert s.reg_read(3) == 0xFFFFFFFA


def test_smul_matches_smull_low() -> None:
    s = CPUState()
    m = Memory(64)
    a, b = 0x12345678, 0x80000001
    w_mul = assemble_line("SMUL 1 2 3")
    w_full = assemble_line("SMULL 1 2 3 4")
    s.reg_write(1, a)
    s.reg_write(2, b)
    execute(s, m, decode_word(w_mul))
    low_smul = s.reg_read(3)
    s2 = CPUState()
    s2.reg_write(1, a)
    s2.reg_write(2, b)
    execute(s2, m, decode_word(w_full))
    assert low_smul == s2.reg_read(3)
