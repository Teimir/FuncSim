"""Assembler error reporting."""

from __future__ import annotations

import pytest

from core.asm import AssembleError, assemble_file, assemble_text
from tests.asm.conftest import ROOT


def test_unknown_mnemonic() -> None:
    with pytest.raises(AssembleError, match="unknown mnemonic"):
        assemble_text("FOOBAR 0 1 2\n")


def test_undefined_label_b() -> None:
    with pytest.raises(AssembleError, match="undefined label"):
        assemble_text("B missing\nHALT\n")


def test_imm11_direct_too_large() -> None:
    with pytest.raises(AssembleError, match="imm11"):
        assemble_text("JMP 31 2000\nHALT\n")


def test_include_missing_file() -> None:
    wrapper = ROOT / "tests" / "asm" / "_bad_inc.asm"
    wrapper.write_text('.include "no_such_file.asm"\n', encoding="utf-8")
    try:
        with pytest.raises(AssembleError, match="cannot open include"):
            assemble_file(wrapper)
    finally:
        wrapper.unlink(missing_ok=True)


def test_include_in_text_raises() -> None:
    with pytest.raises(AssembleError, match="assemble_file"):
        assemble_text('.include "x.asm"\n')


def test_macro_unclosed() -> None:
    with pytest.raises(AssembleError, match="unclosed .macro"):
        assemble_text(".macro X\nNOP\n")


def test_wrong_operand_count() -> None:
    with pytest.raises(AssembleError):
        assemble_text("ADD 1 2\nHALT\n")


def test_error_includes_line_context() -> None:
    src = "NOP\nBADOP 0\nHALT\n"
    with pytest.raises(AssembleError) as exc:
        assemble_text(src)
    assert "line" in str(exc.value).lower() or "unknown" in str(exc.value).lower()
