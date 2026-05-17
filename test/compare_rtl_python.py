from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from core import flags as F
from core.asm import assemble_text
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


ROOT = Path(__file__).resolve().parents[1]
SOC_PSRAM_F = ROOT / "test" / "iverilog_soc_psram.f"


def run_python_program(asm: str, *, max_steps: int = 32) -> CPUState:
    words = assemble_text(asm)
    mem = Memory(256)
    for i, w in enumerate(words):
        mem.write_word(i * 4, w)
    st = CPUState()
    st.set_pc(0)
    run = Runner(st, mem)
    for _ in range(max_steps):
        if st.halted:
            break
        run.step()
    return st


def run_rtl_addi_halt() -> int:
    out_vvp = ROOT / "test" / "out_tb_equiv_basic.vvp"
    cmd = [
        "iverilog",
        "-g2012",
        "-f",
        str(SOC_PSRAM_F),
        "-o",
        str(out_vvp),
        str(ROOT / "test" / "src" / "tb_equiv_basic.sv"),
    ]
    c1 = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if c1.returncode != 0:
        raise RuntimeError(f"iverilog failed:\n{c1.stdout}\n{c1.stderr}")
    c2 = subprocess.run(
        ["vvp", str(out_vvp)],
        cwd=ROOT / "test" / "src",
        capture_output=True,
        text=True,
        check=False,
    )
    if c2.returncode != 0:
        raise RuntimeError(f"vvp failed:\n{c2.stdout}\n{c2.stderr}")
    m = re.search(r"RTL_R1=(\d+)", c2.stdout)
    if not m:
        raise RuntimeError(f"no RTL_R1= in vvp output:\n{c2.stdout}")
    return int(m.group(1))


def run_rtl_core_isa() -> int:
    out_vvp = ROOT / "test" / "out_tb_core_isa_cosim.vvp"
    cmd = [
        "iverilog",
        "-g2012",
        "-f",
        str(SOC_PSRAM_F),
        "-o",
        str(out_vvp),
        str(ROOT / "test" / "src" / "tb_core_isa.sv"),
    ]
    c1 = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if c1.returncode != 0:
        raise RuntimeError(f"iverilog tb_core_isa failed:\n{c1.stdout}\n{c1.stderr}")
    c2 = subprocess.run(
        ["vvp", f"../{out_vvp.name}"],
        cwd=ROOT / "test" / "src",
        capture_output=True,
        text=True,
        check=False,
    )
    if c2.returncode != 0:
        raise RuntimeError(f"vvp tb_core_isa failed:\n{c2.stdout}\n{c2.stderr}")
    if "tb_core_isa PASS" not in c2.stdout:
        raise RuntimeError(f"tb_core_isa did not pass:\n{c2.stdout}")
    m = re.search(r"r1=(\d+)", c2.stdout)
    if not m:
        raise RuntimeError(f"no r1= in tb_core_isa output:\n{c2.stdout}")
    return int(m.group(1))


def main() -> int:
    checks: list[tuple[str, Callable[[], None]]] = []

    def check_addi_halt() -> None:
        st = run_python_program("ADDI 0 1 5\nHALT\n")
        py_r1 = st.reg_read(1)
        rtl_r1 = run_rtl_addi_halt()
        if py_r1 != rtl_r1:
            raise RuntimeError(f"ADDI/HALT mismatch python R1={py_r1} rtl R1={rtl_r1}")

    def check_add_chain() -> None:
        st = run_python_program("ADDI 0 1 3\nADDI 1 1 2\nHALT\n")
        assert st.reg_read(1) == 5
        assert st.halted

    def check_core_isa_rtl() -> None:
        st = run_python_program("ADDI 0 1 5\nHALT\n")
        rtl_r1 = run_rtl_core_isa()
        if st.reg_read(1) != rtl_r1:
            raise RuntimeError(f"tb_core_isa mismatch python R1={st.reg_read(1)} rtl R1={rtl_r1}")

    def check_subi_jnz_python() -> None:
        st = run_python_program("ADDI 0 1 1\nSUBI 1 1 1\nJNZ 31 0\nHALT\n")
        assert st.flags & F.FLAG_ZERO
        assert st.halted

    checks.append(("addi_halt_rtl", check_addi_halt))
    checks.append(("add_chain_python", check_add_chain))
    checks.append(("subi_z_python", check_subi_jnz_python))
    if "--full" in sys.argv:
        checks.append(("core_isa_rtl", check_core_isa_rtl))

    for name, fn in checks:
        fn()
        print(f"  OK {name}")

    print(f"compare_rtl_python PASS ({len(checks)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
