"""Smoke-run all docs/tutorial/asm lab programs."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.asm import assemble_text
from core.loader import load_words
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


LAB_DIR = Path(__file__).resolve().parents[2] / "docs" / "tutorial" / "asm"


@pytest.mark.parametrize("asm_path", sorted(LAB_DIR.glob("lab_*.asm")), ids=lambda p: p.name)
def test_tutorial_lab_runs_to_halt(asm_path: Path) -> None:
    text = asm_path.read_text(encoding="utf-8")
    words = assemble_text(text)
    mem = Memory()
    load_words(mem, 0, words)
    st = CPUState()
    st.set_pc(0)
    r = Runner(st, mem)
    steps = 0
    while steps < 10_000 and not st.halted:
        r.step()
        steps += 1
    assert st.halted, f"{asm_path.name} did not halt within step limit"
