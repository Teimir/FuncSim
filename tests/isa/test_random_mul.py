import hypothesis.strategies as st
import pytest
from hypothesis import given

from core.asm import assemble_line
from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState

pytestmark = pytest.mark.slow


@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_umull_low_high(a: int, b: int) -> None:
    st_cpu = CPUState()
    mem = Memory(256)
    w = assemble_line("UMULL 1 2 3 4")
    ins = decode_word(w)
    st_cpu.reg_write(1, a)
    st_cpu.reg_write(2, b)
    execute(st_cpu, mem, ins)
    prod = (a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)
    assert st_cpu.reg_read(3) == prod & 0xFFFFFFFF
    assert st_cpu.reg_read(4) == (prod >> 32) & 0xFFFFFFFF
