from core.asm import assemble_line
from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


def test_ldr_mask() -> None:
    s = CPUState()
    m = Memory(0x2000)
    m.write_word(0x1000, 0xAABBCCDD)
    ins = decode_word(0x0422A800)
    s.reg_write(1, 0x1000)
    assert execute(s, m, ins) is False
    assert s.reg_read(2) == 0x00BB00DD


def test_ldrpost_load_then_bump_base() -> None:
    s = CPUState()
    m = Memory(0x2000)
    m.write_word(0x1000, 0xCAFEBABE)
    ins = decode_word(assemble_line("LDRPOST 1 2 15 4"))
    s.reg_write(1, 0x1000)
    assert execute(s, m, ins) is False
    assert s.reg_read(2) == 0xCAFEBABE
    assert s.reg_read(1) == 0x1004


def test_str_mask_merge() -> None:
    s = CPUState()
    m = Memory(0x2000)
    m.write_word(0x1000, 0x11223344)
    # STR raddr=1 rdata=2 mask=0x3 imm=0  opcode 000010
    w = 0x08221800
    ins = decode_word(w)
    s.reg_write(1, 0x1000)
    s.reg_write(2, 0xAABBCCDD)
    assert execute(s, m, ins) is False
    assert m.read_word(0x1000) == 0x1122CCDD
