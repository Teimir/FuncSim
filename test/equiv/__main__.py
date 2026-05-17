from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from core.asm import assemble_text
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState

ROOT = Path(__file__).resolve().parents[2]


def run_python(asm: str, setup: dict | None) -> CPUState:
    words = assemble_text(asm)
    mem = Memory(0x10000)
    for i, w in enumerate(words):
        mem.write_word(i * 4, w)
    st = CPUState()
    if setup:
        for ri, val in setup.get("regs", {}).items():
            st.reg_write(int(ri), int(val))
    st.set_pc(0)
    Runner(st, mem).run(max_steps=500)
    return st


def main() -> int:
    p = argparse.ArgumentParser(description="Run Python-side equiv programs")
    p.add_argument("--program", type=str, default=None)
    p.add_argument("--all", action="store_true")
    args = p.parse_args()
    doc = yaml.safe_load((Path(__file__).parent / "programs.yaml").read_text(encoding="utf-8"))
    progs = doc["programs"]
    if args.program:
        progs = [x for x in progs if x["name"] == args.program]
    if not args.all and not args.program:
        print("specify --program NAME or --all", file=sys.stderr)
        return 2
    for ent in progs:
        st = run_python(ent["asm"], ent.get("setup"))
        for chk in ent.get("checks", []):
            got = st.reg_read(int(chk["reg"]))
            want = int(chk["val"])
            if got != want:
                print(f"{ent['name']} FAIL reg {chk['reg']}: got {got} want {want}", file=sys.stderr)
                return 1
        print(f"  OK {ent['name']}")
    print(f"equiv PASS ({len(progs)} programs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
