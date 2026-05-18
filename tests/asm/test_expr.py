"""Expression evaluator (.equ and operands)."""

from __future__ import annotations

import pytest

from core.asm import AssembleError, assemble_text
from core.asm.expr import eval_expr


def test_eval_hex_bin() -> None:
    assert eval_expr("0xFF", {}) == 0xFF
    assert eval_expr("0b1010", {}) == 10


def test_eval_arithmetic() -> None:
    assert eval_expr("1 + 2 * 3", {}) == 7
    assert eval_expr("(1 + 2) * 3", {}) == 9


def test_eval_bitwise() -> None:
    assert eval_expr("0xF0 & 0x0F", {}) == 0
    assert eval_expr("1 << 4", {}) == 16
    assert eval_expr("0x100 >> 4", {}) == 0x10


def test_eval_symbol() -> None:
    assert eval_expr("BASE + 4", {"BASE": 0x100}) == 0x104


def test_eval_undefined_symbol() -> None:
    with pytest.raises(AssembleError):
        eval_expr("NOPE", {})


def test_equ_chain_in_asm() -> None:
    words = assemble_text(
        """
        .equ A 1
        .equ B A + 1
        .equ C B << 2
        ADDI 0 1 C
        HALT
        """
    )
    assert len(words) == 2


def test_operand_expression_in_instruction() -> None:
    words = assemble_text(
        """
        .equ MASK 15
        .equ OFF 8
        ADDI 0 1 (1<<4)+2
        HALT
        """
    )
    assert len(words) == 2
