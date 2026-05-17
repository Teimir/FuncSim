"""Every YAML opcode: assemble sample line, decode, execute one step without IllegalInstruction."""

from __future__ import annotations

import yaml

from core.asm import AssembleError, assemble_line
from core.decode import decode_word
from core.execute import execute
from core.isa_paths import find_opcodes_yaml
from core.memory import Memory
from core.state import CPUState
from tests.test_asm_yaml_roundtrip import _sample_line


def _smoke_word(mnemonic: str, fmt: str) -> int:
    if mnemonic in ("NOP", "HALT"):
        return assemble_line(_sample_line(mnemonic, fmt))
    return assemble_line(_sample_line(mnemonic, fmt))


def test_all_opcodes_decode_and_execute_one_step() -> None:
    path = find_opcodes_yaml()
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    seen: set[str] = set()
    for ent in doc["instructions"]:
        mnemonic = str(ent["mnemonic"])
        fmt = str(ent["format"])
        key = f"{mnemonic}:{fmt}"
        if key in seen:
            continue
        seen.add(key)
        try:
            w = _smoke_word(mnemonic, fmt)
        except AssembleError as e:
            raise AssertionError(f"{mnemonic} {fmt}: {e}") from e
        ins = decode_word(w)
        assert ins.mnemonic == mnemonic, mnemonic
        st = CPUState()
        st.regs = [0] * 32
        st.set_pc(0x1000)
        mem = Memory(0x2000)
        mem.write_word(0x1000, w)
        if mnemonic == "HALT":
            execute(st, mem, ins)
            assert st.halted
            continue
        execute(st, mem, ins)
        assert not st.halted
