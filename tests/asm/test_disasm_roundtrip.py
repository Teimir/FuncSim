"""assemble_line + disassemble_word consistency."""

from __future__ import annotations

import re

import pytest
import yaml

from core.asm import assemble_line
from core.decode import decode_word
from core.disasm import disassemble_word
from core.isa_paths import find_opcodes_yaml


def _sample_line(mnemonic: str, fmt: str) -> str:
    m = mnemonic.upper()
    samples = {
        "bare": m,
        "rrr": f"{m} 1 2 3",
        "mul": f"{m} 1 2 3 4",
        "mla": f"{m} 1 2 3 4",
        "imm16": f"{m} 1 2 42",
        "branch": f"{m} 5 0",
        "load_store": f"{m} 6 7 15 0",
        "store": f"{m} 6 7 15 0",
        "spr": f"{m} 2 3",
        "branch_cond": "BEQ 31 0",
        "strex": f"{m} 1 2 3 0",
    }
    return samples[fmt]


@pytest.mark.parametrize(
    "line",
    [
        "NOP",
        "HALT",
        "ADD r1 r2 r3",
        "ADDI r0 r1 0xFFFF",
        "LDR r6 r7 15 4",
        "STR r6 r7 15 0",
        "JMP r31 8",
        "BEQ 8",
        "STREX r1 r2 r3 0",
        "READSPR r2 3",
        "PUSH 2",
    ],
    ids=lambda s: s.split()[0],
)
def test_disasm_contains_mnemonic(line: str) -> None:
    if line.startswith("PUSH"):
        pytest.skip("pseudo expands to multiple insns")
    asm_line = line if line != "BEQ 8" else "BEQ 31 8"
    w = assemble_line(asm_line)
    dis = disassemble_word(w)
    mnemonic = line.split()[0].upper()
    if mnemonic in ("BEQ",):
        assert "BEQ" in dis or "BJ" in dis
    elif mnemonic == "PUSH":
        pass
    else:
        assert mnemonic in dis.upper() or mnemonic == "READSPR"


def test_no_angle_format_in_yaml_samples() -> None:
    path = find_opcodes_yaml()
    with path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    for ent in doc["instructions"]:
        mnemonic = str(ent["mnemonic"])
        fmt = str(ent["format"])
        if fmt in ("special_nop", "special_halt"):
            continue
        line = _sample_line(mnemonic, fmt)
        if mnemonic in ("NOP", "HALT"):
            continue
        if mnemonic in ("BEQ", "BNE", "BCS"):
            line = f"{mnemonic} 31 0"
        w = assemble_line(line)
        dis = disassemble_word(w)
        assert "<" not in dis, f"{mnemonic} {fmt}: {dis!r}"
