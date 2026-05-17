"""TN9K RTL profile: full ISA in Python except multiply opcodes."""

from core.decode import decode_word
from core.exceptions import IllegalInstruction
from core.execute import execute
from core.memory import Memory
from core.spr_constants import TN9K_ILLEGAL_OPCODES
from core.state import CPUState


def test_tn9k_profile_mul_marked_illegal() -> None:
    assert "MUL" in TN9K_ILLEGAL_OPCODES
    assert len(TN9K_ILLEGAL_OPCODES) == 5


def test_tn9k_execute_mul_raises() -> None:
    s = CPUState.for_variant("tn9k")
    m = Memory(256)
    w = (0b101100 << 26) | (1 << 21) | (2 << 16) | (3 << 11)
    ins = decode_word(w)
    try:
        execute(s, m, ins)
        raised = False
    except IllegalInstruction:
        raised = True
    assert raised


def test_jc_uses_carry_flag() -> None:
    from core import flags as F

    s = CPUState()
    m = Memory(256)
    s.flags |= F.FLAG_CARRY
    w = (0b010011 << 26) | (5 << 21) | 4
    ins = decode_word(w)
    s.reg_write(5, 0x20)
    assert execute(s, m, ins) is True
    assert s.pc == 0x24


def test_bj_eq_alias_encoding() -> None:
    from core import flags as F

    s = CPUState()
    m = Memory(256)
    s.flags |= F.FLAG_ZERO
    w = (0b011000 << 26) | (0 << 22) | (5 << 17) | (4 << 6)
    ins = decode_word(w)
    s.reg_write(5, 0x30)
    assert execute(s, m, ins) is True
    assert s.pc == 0x34
