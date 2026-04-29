"""Run a binary image or hex listing."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.loader import load_binary, load_words, words_from_hex_lines
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


def main() -> None:
    p = argparse.ArgumentParser(description="E32C functional simulator")
    p.add_argument("--load-addr", type=lambda x: int(x, 0), default=0, help="Base address for --bin/--hex")
    p.add_argument("--bin", type=Path, help="Raw binary file (little-endian words as bytes)")
    p.add_argument("--hex", type=Path, help="Text file: one 32-bit hex word per line")
    p.add_argument("--max-steps", type=int, default=100_000)
    p.add_argument("--dump-regs", action="store_true")
    args = p.parse_args()

    mem = Memory()
    st = CPUState()
    if args.bin:
        load_binary(mem, args.load_addr, args.bin)
    elif args.hex:
        ws = words_from_hex_lines(args.hex.read_text(encoding="utf-8"))
        load_words(mem, args.load_addr, ws)
    else:
        p.error("provide --bin or --hex")

    st.set_pc(args.load_addr)
    r = Runner(st, mem)
    n = r.run(max_steps=args.max_steps)
    print(f"steps={n} halted={st.halted}")
    if args.dump_regs:
        for i in range(32):
            print(f"r{i:2d} = 0x{st.reg_read(i):08x}")
        print(f"flags = 0x{st.flags:08x}")


if __name__ == "__main__":
    main()
