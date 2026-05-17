import hypothesis.strategies as st
import pytest
from hypothesis import given

from core.decode import decode_word
from core.execute import _adds_flags, _subs_flags, execute
from core.memory import Memory
from core.state import CPUState

pytestmark = pytest.mark.slow


@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_adds_flags_match_reference(a: int, b: int) -> None:
    st_cpu = CPUState()
    mem = Memory(256)
    ins = decode_word(0x8C221800)
    st_cpu.reg_write(1, a)
    st_cpu.reg_write(2, b)
    execute(st_cpu, mem, ins)
    res, fl = _adds_flags(a, b)
    assert st_cpu.reg_read(3) == res
    assert (st_cpu.flags & 0x1E) == (fl & 0x1E)


@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_subs_flags_match_reference(a: int, b: int) -> None:
    st_cpu = CPUState()
    mem = Memory(256)
    ins = decode_word(0x90221800)
    st_cpu.reg_write(1, a)
    st_cpu.reg_write(2, b)
    execute(st_cpu, mem, ins)
    res, fl = _subs_flags(a, b)
    assert st_cpu.reg_read(3) == res
    assert (st_cpu.flags & 0x1E) == (fl & 0x1E)
