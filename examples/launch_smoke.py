#!/usr/bin/env python3
"""Minimal launch smoke example for the simulator.

Run from repo root:
  python examples/launch_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.loader import load_words, words_from_hex_lines
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


def main() -> None:
    image_path = ROOT / "examples" / "smoke.hex"
    words = words_from_hex_lines(image_path.read_text(encoding="utf-8"))

    mem = Memory()
    st = CPUState()
    load_words(mem, 0, words)
    st.set_pc(0)

    runner = Runner(st, mem)
    steps = runner.run(max_steps=1000)
    cycles = runner.cycle_counter.value

    print("=== launch_smoke ===")
    print(f"image={image_path}")
    print(f"steps={steps} halted={st.halted} cycles={cycles}")

    if not st.halted:
        raise SystemExit("FAIL: CPU did not halt within max_steps")
    print("OK: simulator starts and executes smoke image.")


if __name__ == "__main__":
    main()
