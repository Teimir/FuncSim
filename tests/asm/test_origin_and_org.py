"""Origin / .org placement."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.asm import assemble_file, assemble_text

from tests.asm.conftest import ROOT


def test_assemble_file_with_origin() -> None:
    src = "NOP\nHALT\n"
    p = ROOT / "tests" / "asm" / "_origin.asm"
    p.write_text(src, encoding="utf-8")
    try:
        words = assemble_file(p, origin=0x200)
        assert words[0] == 0
        assert len(words) == 2
    finally:
        p.unlink(missing_ok=True)


def test_org_gap_zeros() -> None:
    words = assemble_text(
        """
        NOP
        .org 0x40
        HALT
        """
    )
    assert words[0] == 0
    assert words[0x40 // 4] == 0xFFFFFFFF
    for i in range(1, 0x40 // 4):
        assert words[i] == 0
