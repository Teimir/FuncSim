from core.loader import load_words
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


def test_addi_then_halt() -> None:
    # ADDI r1=1 res=2 imm=4 at 0x1000, then HALT at 0x1004
    addi = 0xC0201004
    halt = 0xFFFFFFFF
    mem = Memory(0x2000)
    st = CPUState()
    load_words(mem, 0x1000, [addi, halt])
    st.set_pc(0x1000)
    st.reg_write(1, 10)
    r = Runner(st, mem)
    n = r.run(max_steps=10)
    assert n == 2
    assert st.halted
    assert st.reg_read(2) == 14
    assert st.pc == 0x1004


def test_iret_restores_pc() -> None:
    mem = Memory(256)
    st = CPUState()
    st.spr_write(0, 0x8000)
    # IRET: opcode 111110 = 0x3E
    iret = 0xF8000000
    load_words(mem, 0, [iret])
    st.set_pc(0)
    Runner(st, mem).step()
    assert st.pc == 0x8000
