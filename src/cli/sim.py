"""Run a binary image or hex listing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.asm import AssembleError, assemble_text
from core.bus import MMIO_BASE_DEFAULT, SystemBus
from core.exceptions import BreakpointHit
from core.loader import load_binary, load_words, words_from_hex_lines
from core.memory import Memory
from core.peripherals.uart import Uart
from core.runner import Runner
from core.state import CPUState
from core.trace import StepTrace


def main() -> None:
    p = argparse.ArgumentParser(description="E32C functional simulator")
    p.add_argument("--load-addr", type=lambda x: int(x, 0), default=0, help="Base address for --bin/--hex/--asm")
    p.add_argument("--bin", type=Path, help="Raw binary file (little-endian words as bytes)")
    p.add_argument("--hex", type=Path, help="Text file: one 32-bit hex word per line")
    p.add_argument("--asm", type=Path, help="Assembler source (one instruction per line)")
    p.add_argument("--max-steps", type=int, default=100_000)
    p.add_argument("--dump-regs", action="store_true")
    p.add_argument("--dump-gpio", action="store_true", help="Print GPIO_OUT after run (uses MMIO bus)")
    p.add_argument("--mmio", action="store_true", help="Use SystemBus with GPIO/UART/Timer")
    p.add_argument("--mmio-base", type=lambda x: int(x, 0), default=MMIO_BASE_DEFAULT, help="MMIO base address")
    p.add_argument("--cycle-ns", type=float, default=None, help="Approximate nanoseconds per cycle (report only)")
    p.add_argument("--uart-stdout", action="store_true", help="Mirror UART TX bytes to stdout (binary)")
    p.add_argument("--trace", action="store_true", help="Print one line per executed instruction")
    p.add_argument("--trace-file", type=Path, default=None, help="Append trace lines to this file")
    p.add_argument("--break", dest="break_addrs", action="append", default=[], type=lambda x: int(x, 0), help="Breakpoint PC (repeatable)")
    args = p.parse_args()

    ram = Memory()
    use_bus = args.mmio or args.dump_gpio or args.uart_stdout
    if use_bus:
        uart = Uart()
        if args.uart_stdout:
            uart.write_stream_hook(sys.stdout.buffer)
        mem: Memory | SystemBus = SystemBus(ram, mmio_base=args.mmio_base, uart=uart)
    else:
        mem = ram

    st = CPUState()
    if args.bin:
        load_binary(mem, args.load_addr, args.bin)
    elif args.hex:
        ws = words_from_hex_lines(args.hex.read_text(encoding="utf-8"))
        load_words(mem, args.load_addr, ws)
    elif args.asm:
        try:
            ws = assemble_text(args.asm.read_text(encoding="utf-8"))
        except AssembleError as e:
            print(f"assemble error: {e}", file=sys.stderr)
            sys.exit(1)
        load_words(mem, args.load_addr, ws)
    else:
        p.error("provide --bin, --hex, or --asm")

    st.set_pc(args.load_addr)
    brk = set(args.break_addrs) if args.break_addrs else set()
    trace_f = args.trace_file.open("w", encoding="utf-8") if args.trace_file else None

    def on_step(tr: StepTrace) -> None:
        line = f"0x{tr.pc:08x}\t0x{tr.word:08x}\t{tr.disasm}\tcycles={tr.cycles_after}\thalting={tr.halted_after}"
        if args.trace:
            print(line)
        if trace_f:
            trace_f.write(line + "\n")

    on_cb = on_step if (args.trace or trace_f) else None
    r = Runner(st, mem, break_pcs=brk, on_step=on_cb)

    steps = 0
    hit_bp = False
    try:
        while steps < args.max_steps and not st.halted:
            r.step()
            steps += 1
    except BreakpointHit as e:
        hit_bp = True
        print(f"breakpoint at 0x{e.pc:x} steps={steps} halted={st.halted}")
    finally:
        if trace_f:
            trace_f.close()

    cyc = r.cycle_counter.value
    if not hit_bp:
        print(f"steps={steps} halted={st.halted} cycles={cyc}")
    else:
        print(f"cycles={cyc}")
    if args.cycle_ns is not None:
        print(f"approx_ns={cyc * args.cycle_ns:g}")
    if args.dump_regs:
        for i in range(32):
            print(f"r{i:2d} = 0x{st.reg_read(i):08x}")
        print(f"flags = 0x{st.flags:08x}")
    if args.dump_gpio and isinstance(mem, SystemBus):
        print(f"gpio_out = 0x{mem.gpio.out:08x}")


if __name__ == "__main__":
    main()
