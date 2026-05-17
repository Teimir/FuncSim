from pathlib import Path

import pytest
import yaml

from core.asm import assemble_line
from core.bus import SystemBus
from core.exceptions import MisalignedAccess
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


def _load_vectors():
    p = Path(__file__).resolve().parent / "test_vectors.yaml"
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _word_for_case(case: dict) -> int:
    if "word" in case:
        return int(case["word"])
    if "asm" in case:
        return assemble_line(str(case["asm"]).strip())
    raise KeyError(case.get("name", "?"))


def _backend_for_case(case: dict) -> Memory | SystemBus:
    if case.get("bus") == "mmio":
        return SystemBus(Memory(1 << 16))
    return Memory(1 << 16)


def test_yaml_vectors():
    for case in _load_vectors():
        mem = _backend_for_case(case)
        st = CPUState()
        for addr, val in case.get("mem", {}).items():
            mem.write_word(int(addr), int(val))
        regs = list(case["regs"])
        assert len(regs) == 32
        st.regs = [x & 0xFFFFFFFF for x in regs]
        st.flags = int(case["flags"])
        for idx, val in case.get("spr", {}).items():
            st.spr_write(int(idx), int(val))
        st.halted = False
        pc = int(case["pc"])
        st.set_pc(pc)
        word = _word_for_case(case)
        mem.write_word(pc, word)

        exc_name = case.get("expect", {}).get("exception")
        if exc_name == "MisalignedAccess":
            with pytest.raises(MisalignedAccess):
                Runner(st, mem).step()
            continue
        if exc_name:
            raise AssertionError(f"unsupported exception {exc_name!r} in {case['name']}")

        Runner(st, mem).step()
        ex = case["expect"]
        if "pc" in ex:
            assert st.pc == int(ex["pc"]), case["name"]
        if "halted" in ex:
            assert st.halted == bool(ex["halted"]), case["name"]
        for ri, rv in ex.get("regs", {}).items():
            assert st.reg_read(int(ri)) == int(rv), case["name"]
        if "flags_mask" in ex:
            m = int(ex["flags_mask"])
            exp = int(ex["flags_expected"])
            assert (st.flags & m) == exp, case["name"]
        for addr, val in ex.get("mem", {}).items():
            assert mem.read_word(int(addr)) == int(val), case["name"]
        for idx, val in ex.get("spr", {}).items():
            assert st.spr_read(int(idx)) == int(val), case["name"]
