"""Every checked-in .asm example and tutorial lab must assemble."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.asm import AssembleError, assemble_file, assemble_text

from tests.asm.conftest import ROOT


@pytest.mark.parametrize(
    "asm_path",
    sorted((ROOT / "examples").glob("*.asm")),
    ids=lambda p: p.name,
)
def test_example_file_assembles(asm_path: Path) -> None:
    words = assemble_file(asm_path)
    assert isinstance(words, list)
    assert len(words) >= 1
    assert all(isinstance(w, int) for w in words)


@pytest.mark.parametrize(
    "asm_path",
    sorted((ROOT / "docs" / "tutorial" / "asm").glob("lab_*.asm")),
    ids=lambda p: p.name,
)
def test_tutorial_lab_assembles(asm_path: Path) -> None:
    words = assemble_file(asm_path)
    assert len(words) >= 1


def test_boot_smoke_word_count() -> None:
    words = assemble_file(ROOT / "examples" / "boot_smoke.asm")
    assert len(words) >= 10
    assert any(w == 0 for w in words)


def test_hello_asm() -> None:
    path = ROOT / "examples" / "hello.asm"
    if not path.is_file():
        pytest.skip("hello.asm not present")
    words = assemble_file(path)
    assert len(words) >= 1
