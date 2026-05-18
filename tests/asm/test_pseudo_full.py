"""All pseudo-instructions and PUSH/POP expansion."""

from __future__ import annotations

import pytest

from core.asm import assemble_line, assemble_text
from core.decode import decode_word


@pytest.mark.parametrize(
    "line,expected_mnemonic",
    [
        ("CMP 1 2", "SUBS"),
        ("CMN 3 4", "ADDS"),
        ("TST 5 6", "ANDS"),
        ("TEST 5 6", "ANDS"),
        ("MOV 7 100", "ADDI"),
    ],
)
def test_pseudo_single_line(line: str, expected_mnemonic: str) -> None:
    w = assemble_line(line)
    assert decode_word(w).mnemonic == expected_mnemonic


def test_push_pop_word_count() -> None:
    words = assemble_text("PUSH 2\nPOP 2\nHALT\n")
    assert len(words) == 5


def test_all_cond_branch_aliases_encode() -> None:
    aliases = (
        "BEQ",
        "BNE",
        "BCS",
        "BCC",
        "BMI",
        "BPL",
        "BVS",
        "BVC",
        "BHI",
        "BLS",
        "BGE",
        "BLT",
        "BGT",
        "BLE",
        "BAL",
    )
    for a in aliases:
        w = assemble_line(f"{a} 31 0")
        ins = decode_word(w)
        assert ins.mnemonic == "BJ"


def test_b_pseudo_resolves() -> None:
    words = assemble_text(
        """
        B fwd
        NOP
    fwd:
        HALT
        """
    )
    assert len(words) == 3
    assert words[-1] == 0xFFFFFFFF
