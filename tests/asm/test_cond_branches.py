"""Conditional branches with labels and r31."""

from __future__ import annotations

import pytest

from core.asm import AssembleError, assemble_text
from core.decode import decode_word


@pytest.mark.parametrize("branch", ["JZ", "JNZ", "JC", "JS", "JO"])
def test_flag_branch_to_label(branch: str) -> None:
    src = f"""
        {branch} tgt
        NOP
    tgt:
        HALT
    """
    words = assemble_text(src)
    assert len(words) == 3


@pytest.mark.parametrize("cond", ["BEQ", "BNE", "BMI", "BAL"])
def test_cond_alias_to_label(cond: str) -> None:
    src = f"""
        {cond} tgt
        NOP
    tgt:
        HALT
    """
    words = assemble_text(src)
    assert len(words) == 3
    assert decode_word(words[0]).mnemonic == "BJ"


def test_jz_two_operand_form() -> None:
    words = assemble_text(
        """
        ADDI 0 0 0
        JZ 5 4
        HALT
        """
    )
    assert len(words) == 3
