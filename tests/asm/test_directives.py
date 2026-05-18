"""Assembler directives: .org, .align, .word, .skip, .include, .equ."""

from __future__ import annotations

from pathlib import Path

from core.asm import assemble_file, assemble_text

ROOT = Path(__file__).resolve().parents[2]


def test_equ_expression() -> None:
    words = assemble_text(
        """
        .equ BASE 0x100
        .equ OFF BASE + 4
        ADDI 0 1 OFF
        HALT
        """
    )
    assert len(words) == 2


def test_org_and_skip() -> None:
    words = assemble_text(
        """
        NOP
        .org 0x20
        .word 0xDEADBEEF
        HALT
        """
    )
    assert words[0] == 0
    assert words[8] == 0xDEADBEEF


def test_align() -> None:
    words = assemble_text(
        """
        NOP
        .align 16
        HALT
        """
    )
    assert len(words) >= 5


def test_include_boot_smoke() -> None:
    wrapper = ROOT / "tests" / "asm" / "_wrapper.asm"
    wrapper.write_text('.include "../../examples/boot_smoke.asm"\n', encoding="utf-8")
    try:
        words = assemble_file(wrapper)
        assert len(words) >= 1
    finally:
        wrapper.unlink(missing_ok=True)


def test_rn_syntax() -> None:
    words = assemble_text(
        """
        ADDI r0 r1 42
        HALT
        """
    )
    assert len(words) == 2
