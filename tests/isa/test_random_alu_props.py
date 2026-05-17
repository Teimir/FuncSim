import hypothesis.strategies as st
import pytest
from hypothesis import given

from core.asm import assemble_line
from core.decode import decode_word
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


def _run_rrr(mnemonic: str, a: int, b: int) -> int:
    s = CPUState()
    m = Memory(256)
    ins = decode_word(assemble_line(f"{mnemonic} 1 2 3"))
    s.reg_write(1, a)
    s.reg_write(2, b)
    execute(s, m, ins)
    return s.reg_read(3)


@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_add_wraps_unsigned(a: int, b: int) -> None:
    assert _run_rrr("ADD", a, b) == (a + b) & 0xFFFFFFFF


@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_sub_wraps_unsigned(a: int, b: int) -> None:
    assert _run_rrr("SUB", a, b) == (a - b) & 0xFFFFFFFF


@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_and_or_xor(a: int, b: int) -> None:
    assert _run_rrr("AND", a, b) == a & b
    assert _run_rrr("OR", a, b) == a | b
    assert _run_rrr("XOR", a, b) == a ^ b


@pytest.mark.slow
@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=0xFFFFFFFF),
)
def test_mul_low32(a: int, b: int) -> None:
    s = CPUState()
    m = Memory(256)
    ins = decode_word(assemble_line("MUL 1 2 3 4"))
    s.reg_write(1, a)
    s.reg_write(2, b)
    execute(s, m, ins)
    assert s.reg_read(3) == (a * b) & 0xFFFFFFFF


@pytest.mark.slow
@given(
    st.integers(min_value=0, max_value=0xFFFFFFFF),
    st.integers(min_value=0, max_value=3),
)
def test_rol_ror_roundtrip(val: int, sh: int) -> None:
    s = CPUState()
    m = Memory(256)
    rol = decode_word(assemble_line("ROL 1 2 3"))
    ror = decode_word(assemble_line("ROR 3 2 1"))
    s.reg_write(1, val)
    s.reg_write(2, sh)
    execute(s, m, rol)
    s.reg_write(2, sh)
    execute(s, m, ror)
    assert s.reg_read(1) == val


@pytest.mark.slow
@given(
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
)
def test_smul_signed(a: int, b: int) -> None:
    s = CPUState()
    m = Memory(256)
    ins = decode_word(assemble_line("SMUL 1 2 3"))
    s.reg_write(1, a & 0xFFFFFFFF)
    s.reg_write(2, b & 0xFFFFFFFF)
    execute(s, m, ins)
    expected = (a * b) & 0xFFFFFFFF
    assert s.reg_read(3) == expected
