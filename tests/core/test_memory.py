import pytest

from core.exceptions import MisalignedAccess
from core.memory import Memory


def test_read_write_word_roundtrip() -> None:
    m = Memory(256)
    m.write_word(0, 0xAABBCCDD)
    assert m.read_word(0) == 0xAABBCCDD


def test_misaligned_raises() -> None:
    m = Memory(256)
    with pytest.raises(MisalignedAccess):
        m.read_word(1)
