from pathlib import Path

import pytest

from tests.conftest import run_program

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "name,max_steps",
    [
        ("blink_uart.asm", 5000),
    ],
)
def test_example_asm_smoke(name: str, max_steps: int) -> None:
    path = ROOT / "examples" / name
    asm = path.read_text(encoding="utf-8")
    st, _bus = run_program(asm, max_steps=max_steps, mmio=True)
    assert st is not None
