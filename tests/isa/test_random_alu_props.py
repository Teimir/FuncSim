from hypothesis import given
import hypothesis.strategies as st

from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_add_wraps_unsigned(a: int, b: int) -> None:
    s = CPUState()
    m = Memory(256)
    # ADD r1=1 r2=2 res=3
    ins = decode_word(0x84221800)
    s.reg_write(1, a)
    s.reg_write(2, b)
    execute(s, m, ins)
    assert s.reg_read(3) == (a + b) & 0xFFFFFFFF
