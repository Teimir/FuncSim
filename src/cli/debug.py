"""Interactive debugger (minimal REPL)."""

from __future__ import annotations

import argparse
import cmd

from cli.debug_common import (
    add_sim_session_arguments,
    build_repl_memory,
    cpu_state_from_args,
    load_program_into_memory,
)
from core.bus import SystemBus
from core.disasm import disassemble_word
from core.exceptions import BreakpointHit, CpuHalted
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState


class DebugShell(cmd.Cmd):
    intro = "E32C debug. Type 'help' for commands.\n"
    prompt = "e32c> "

    def __init__(
        self,
        state: CPUState,
        mem: Memory | SystemBus,
        runner: Runner,
    ) -> None:
        super().__init__()
        self.state = state
        self.mem = mem
        self.runner = runner

    def do_s(self, arg: str) -> None:
        """s — step one instruction"""
        try:
            self.runner.step()
        except CpuHalted:
            print("CPU halted")
        except BreakpointHit as e:
            print(f"breakpoint 0x{e.pc:x}")

    def do_c(self, arg: str) -> None:
        """c [N] — continue up to N steps (default 10000) or until halt/break"""
        n = int(arg, 0) if arg.strip() else 10_000
        steps = 0
        try:
            while steps < n and not self.state.halted:
                self.runner.step()
                steps += 1
        except BreakpointHit as e:
            print(f"breakpoint 0x{e.pc:x} after {steps} steps")
            return
        print(f"continued {steps} steps halted={self.state.halted}")

    def do_r(self, arg: str) -> None:
        """r — print GPRs and flags"""
        for i in range(32):
            print(f"r{i:2d} = 0x{self.state.reg_read(i):08x}")
        print(f"flags = 0x{self.state.flags:08x} pc=0x{self.state.pc:08x} cycles={self.runner.cycle_counter.value}")

    def do_x(self, arg: str) -> None:
        """x ADDR [COUNT] — hex dump COUNT words (default 1)"""
        parts = arg.split()
        if not parts:
            print("usage: x ADDR [COUNT]")
            return
        addr = int(parts[0], 0)
        cnt = int(parts[1], 0) if len(parts) > 1 else 1
        for i in range(cnt):
            a = addr + i * 4
            try:
                w = self.mem.read_word(a)
                print(f"0x{a:08x}: 0x{w:08x}  {disassemble_word(w)}")
            except Exception as e:
                print(f"0x{a:08x}: <error {e}>")

    def do_dis(self, arg: str) -> None:
        """dis [ADDR] [COUNT] — disassemble COUNT words at ADDR (default PC, 8)"""
        parts = arg.split()
        addr = self.state.pc
        cnt = 8
        if len(parts) >= 1:
            addr = int(parts[0], 0)
        if len(parts) >= 2:
            cnt = int(parts[1], 0)
        for i in range(cnt):
            a = addr + i * 4
            try:
                w = self.mem.read_word(a)
                print(f"0x{a:08x}: 0x{w:08x}  {disassemble_word(w)}")
            except Exception as e:
                print(f"0x{a:08x}: <error {e}>")

    def do_b(self, arg: str) -> None:
        """b ADDR — add breakpoint at word address"""
        if not arg.strip():
            print("usage: b ADDR")
            return
        a = int(arg, 0)
        self.runner.break_pcs.add(a)
        print(f"breakpoint +0x{a:x}")

    def do_bl(self, arg: str) -> None:
        """bl — list breakpoints"""
        for a in sorted(self.runner.break_pcs):
            print(f"  0x{a:x}")

    def do_bc(self, arg: str) -> None:
        """bc — clear all breakpoints"""
        self.runner.break_pcs.clear()
        print("breakpoints cleared")

    def do_q(self, arg: str) -> bool:
        """q — quit"""
        return True

    def do_EOF(self, arg: str) -> bool:
        print()
        return True


def main() -> None:
    p = argparse.ArgumentParser(description="E32C interactive debugger")
    add_sim_session_arguments(p)
    args = p.parse_args()

    _, mem = build_repl_memory(args)

    st = cpu_state_from_args(args)
    if not args.bin and not args.hex:
        p.error("provide --hex or --bin")
    load_program_into_memory(mem, args.load_addr, args)

    st.set_pc(args.load_addr)
    r = Runner(st, mem)
    DebugShell(st, mem, r).cmdloop()


if __name__ == "__main__":
    main()
