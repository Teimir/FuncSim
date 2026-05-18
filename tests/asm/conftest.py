"""Shared fixtures for assembler tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _collect_asm_files(*dirs: Path) -> list[Path]:
    out: list[Path] = []
    for d in dirs:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("**/*.asm")):
            if p.name.startswith("."):
                continue
            out.append(p)
    return out


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def example_asm_files(repo_root: Path) -> list[Path]:
    return _collect_asm_files(repo_root / "examples")


@pytest.fixture(scope="session")
def tutorial_lab_files(repo_root: Path) -> list[Path]:
    return _collect_asm_files(repo_root / "docs" / "tutorial" / "asm")
