"""All cosim programs.yaml snippets must assemble."""

from __future__ import annotations

import pytest
import yaml

from core.asm import assemble_text
from tests.asm.conftest import ROOT

PROGRAMS_YAML = ROOT / "test" / "tn9k" / "cosim" / "programs.yaml"


def _program_cases() -> list[tuple[str, str]]:
    if not PROGRAMS_YAML.is_file():
        return []
    with PROGRAMS_YAML.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    out: list[tuple[str, str]] = []
    for prog in doc.get("programs", []):
        name = str(prog.get("name", "anon"))
        asm = str(prog.get("asm", ""))
        if asm.strip():
            out.append((name, asm))
    return out


@pytest.mark.parametrize("name,asm", _program_cases(), ids=[n for n, _ in _program_cases()] or ["none"])
def test_cosim_program_assembles(name: str, asm: str) -> None:
    words = assemble_text(asm)
    assert len(words) >= 1, name


def test_cosim_programs_yaml_nonempty() -> None:
    cases = _program_cases()
    assert len(cases) >= 10
