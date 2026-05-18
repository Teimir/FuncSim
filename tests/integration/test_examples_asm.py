"""Assemble and optionally run all example programs."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.asm import assemble_text
from tests.conftest import run_program

ROOT = Path(__file__).resolve().parents[2]

# Examples that assemble but are not meant for short sim runs (infinite loops / huge).
ASSEMBLE_ONLY = {
    "blink_uart.asm",
    "blink_uart_spam.asm",
    "sd_gui_demo.asm",
    "_tn9k_demo_fpga_main.asm",
    "tn9k_sd_spi_uart.asm",
    "tn9k_demo_uart_timer_sd_main.asm",
}

# Quick sim smoke (must halt or produce UART within step budget).
RUN_SMOKE = {
    "boot_smoke.asm": (500, True),
    "hello.asm": (500, True),
    "tn9k_uart_hello.asm": (30_000, True),
    "tn9k_uart_beacon.asm": (10_000, True),
}


@pytest.mark.parametrize(
    "name",
    sorted(p.name for p in (ROOT / "examples").glob("*.asm")),
)
def test_example_assembles(name: str) -> None:
    path = ROOT / "examples" / name
    words = assemble_text(path.read_text(encoding="utf-8"))
    assert len(words) >= 1


@pytest.mark.parametrize("name,params", list(RUN_SMOKE.items()), ids=[n for n in RUN_SMOKE])
def test_example_sim_smoke(name: str, params: tuple[int, bool]) -> None:
    max_steps, use_mmio = params
    path = ROOT / "examples" / name
    if not path.is_file():
        pytest.skip(f"{name} missing")
    asm = path.read_text(encoding="utf-8")
    st, _bus = run_program(asm, max_steps=max_steps, mmio=use_mmio)
    assert st is not None
    if name == "hello.asm":
        assert st.halted
