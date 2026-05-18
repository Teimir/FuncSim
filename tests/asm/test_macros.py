"""Macro expansion."""

from __future__ import annotations

from core.asm import assemble_text


def test_macro_expand() -> None:
    words = assemble_text(
        """
        .macro INC reg
        ADDI {reg} {reg} 1
        .endm
        INC r1
        HALT
        """
    )
    assert len(words) == 2


def test_macro_default_param() -> None:
    words = assemble_text(
        """
        .macro LOAD_IMM dst=1 val=0
        ADDI 0 {dst} {val}
        .endm
        LOAD_IMM val=9
        HALT
        """
    )
    assert len(words) == 2
