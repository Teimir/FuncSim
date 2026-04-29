import pytest

from core.decode import decode_word, imm16_from_parts, sext11
from core.exceptions import IllegalInstruction


def test_sext11_negative() -> None:
    assert sext11(0x400) == 0xFFFFFC00


def test_imm16_sign_extend() -> None:
    # Composite 0x8000 (bit 15 set): immh=16<<11, imm11=0
    v = imm16_from_parts(16, 0)
    assert v == 0xFFFF8000


def test_decode_nop_and_halt() -> None:
    assert decode_word(0).mnemonic == "NOP"
    assert decode_word(0xFFFFFFFF).mnemonic == "HALT"


def test_decode_add_fields() -> None:
    ins = decode_word(0x84221800)
    assert ins.mnemonic == "ADD"
    assert ins.fields["r1"] == 1
    assert ins.fields["r2"] == 2
    assert ins.fields["res"] == 3


def test_illegal_nonzero_opcode0() -> None:
    with pytest.raises(IllegalInstruction):
        decode_word(0x00000001)
