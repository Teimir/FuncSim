from pathlib import Path

import yaml

from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


def _load_vectors():
    p = Path(__file__).resolve().parent / "test_vectors.yaml"
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_yaml_vectors():
    for case in _load_vectors():
        mem = Memory(1 << 16)
        st = CPUState()
        for addr, val in case.get("mem", {}).items():
            mem.write_word(int(addr), int(val))
        regs = list(case["regs"])
        assert len(regs) == 32
        st.regs = [x & 0xFFFFFFFF for x in regs]
        st.flags = int(case["flags"])
        st.halted = False
        pc = int(case["pc"])
        st.set_pc(pc)
        mem.write_word(pc, int(case["word"]))
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
