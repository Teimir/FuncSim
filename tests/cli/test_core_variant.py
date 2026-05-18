"""CLI --core variant wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.debug_common import cpu_state_from_args, create_debug_controller
from core.asm import assemble_text
from core.exceptions import IllegalInstruction
from core.loader import load_words
from core.memory import Memory
from core.runner import Runner
from core.spr_constants import CORE_INFO_FULL, CORE_INFO_TN9K, SPR_CORE_INFO
from core.state import CPUState

ROOT = Path(__file__).resolve().parents[2]
MUL_ASM = """
MOV 1 6
MOV 2 7
MUL 1 2 3 0
HALT
"""


def _args(**kw: object) -> object:
    defaults: dict[str, object] = {
        "core": "full",
        "mmio": False,
        "mmio_base": 0xFFFF_0000,
        "sd_image": None,
        "sd_create_sectors": None,
        "sd_spi": False,
        "load_addr": 0,
    }
    defaults.update(kw)
    return type("Args", (), defaults)()


def test_cpu_state_from_args_variants() -> None:
    full = cpu_state_from_args(_args(core="full"))
    tn9k = cpu_state_from_args(_args(core="tn9k"))
    assert full.spr_read(SPR_CORE_INFO) == CORE_INFO_FULL
    assert tn9k.spr_read(SPR_CORE_INFO) == CORE_INFO_TN9K


def test_full_core_runs_mul_program() -> None:
    st = CPUState.for_variant("full")
    mem = Memory()
    load_words(mem, 0, assemble_text(MUL_ASM))
    st.set_pc(0)
    r = Runner(st, mem)
    steps = 0
    while steps < 20 and not st.halted:
        r.step()
        steps += 1
    assert st.halted
    assert st.reg_read(3) == 42


def test_tn9k_core_mul_illegal() -> None:
    st = CPUState.for_variant("tn9k")
    mem = Memory()
    load_words(mem, 0, assemble_text(MUL_ASM))
    st.set_pc(0)
    r = Runner(st, mem)
    with pytest.raises(IllegalInstruction):
        for _ in range(20):
            if st.halted:
                break
            r.step()


def test_debug_controller_honors_core_variant() -> None:
    ram = Memory()
    ctrl = create_debug_controller(ram, _args(core="tn9k"))
    assert ctrl.state.core_variant == "tn9k"
    assert ctrl.state.spr_read(SPR_CORE_INFO) == CORE_INFO_TN9K
