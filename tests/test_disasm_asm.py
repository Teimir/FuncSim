import pytest

from core.asm import assemble_line, assemble_text
from core.decode import decode_word
from core.disasm import disassemble_word, format_instruction


def test_disassemble_smoke() -> None:
    assert "NOP" in disassemble_word(0)
    assert "HALT" in disassemble_word(0xFFFFFFFF)


def test_asm_add_roundtrip() -> None:
    w = assemble_line("ADD 1 2 3")
    ins = decode_word(w)
    assert ins.mnemonic == "ADD"
    assert ins.fields["r1"] == 1 and ins.fields["r2"] == 2 and ins.fields["res"] == 3
    assert "ADD r1 r2 r3" == format_instruction(ins)


def test_assemble_program() -> None:
    ws = assemble_text(
        """
        ADDI 0 1 10
        ADDI 1 2 5
        HALT
        """
    )
    assert len(ws) == 3
    assert ws[2] == 0xFFFFFFFF


def test_breakpoint_import() -> None:
    from core.exceptions import BreakpointHit

    assert BreakpointHit(4).pc == 4


def test_runner_breakpoint_before_fetch() -> None:
    from core.exceptions import BreakpointHit

    from core.memory import Memory
    from core.runner import Runner
    from core.state import CPUState

    mem = Memory(64)
    mem.write_word(0, 0x00000000)
    mem.write_word(4, 0xFFFFFFFF)
    st = CPUState()
    st.set_pc(0)
    r = Runner(st, mem, break_pcs={4})
    r.step()
    assert st.pc == 4
    with pytest.raises(BreakpointHit) as ei:
        r.step()
    assert ei.value.pc == 4
