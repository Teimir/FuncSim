import pytest

from core.asm import assemble_text
from core.exceptions import WatchpointHit
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


def test_watch_write() -> None:
    mem = Memory(256)
    words = assemble_text("ADDI 0 1 4\nSTR 1 2 15 0\nHALT\n")
    for i, w in enumerate(words):
        mem.write_word(i * 4, w)
    st = CPUState()
    st.set_pc(0)
    st.reg_write(2, 0xAABBCCDD)
    run = Runner(st, mem, watch_write={4})
    run.step()
    with pytest.raises(WatchpointHit) as ei:
        run.step()
    assert ei.value.kind == "write"
    assert ei.value.addr == 4
