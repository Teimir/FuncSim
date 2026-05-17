from core.asm import assemble_line
from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


def test_cmp_expands_to_subs() -> None:
    w = assemble_line("CMP 3 4")
    ins = decode_word(w)
    assert ins.mnemonic == "SUBS"
    assert ins.fields["res"] == 0


def test_cmp_sets_zero_flag() -> None:
    w = assemble_line("CMP 1 2")
    st = CPUState()
    mem = Memory(256)
    st.reg_write(1, 5)
    st.reg_write(2, 5)
    execute(st, mem, decode_word(w))
    assert st.flags & 2


def test_cmn_expands_to_adds() -> None:
    assert decode_word(assemble_line("CMN 1 2")).mnemonic == "ADDS"


def test_mov_addi() -> None:
    w = assemble_line("MOV 3 42")
    assert decode_word(w).mnemonic == "ADDI"
    st = CPUState()
    mem = Memory(256)
    execute(st, mem, decode_word(w))
    assert st.reg_read(3) == 42
