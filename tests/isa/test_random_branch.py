import hypothesis.strategies as st
import pytest
from hypothesis import given

from core import flags as F
from core.execute import _branch_cond_take

pytestmark = pytest.mark.slow


def _flags_word(*, z: bool, c: bool, v: bool, s: bool) -> int:
    f = 0
    if z:
        f |= F.FLAG_ZERO
    if c:
        f |= F.FLAG_CARRY
    if v:
        f |= F.FLAG_OVERFLOW
    if s:
        f |= F.FLAG_SIGN
    return f


@given(
    st.integers(min_value=0, max_value=15),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans(),
)
def test_branch_cond_table(cond: int, z: bool, c: bool, v: bool, s: bool) -> None:
    fl = _flags_word(z=z, c=c, v=v, s=s)
    got = _branch_cond_take(cond, fl)
    if cond == 0:
        assert got == z
    elif cond == 1:
        assert got != z
    elif cond == 14:
        assert got is True
    elif cond == 15:
        assert got is False
