"""Fetch-decode-execute loop."""

from __future__ import annotations

from collections.abc import Callable

from core.bus import SystemBus
from core.cycles import CycleCounter, cycles_for_mnemonic
from core.decode import decode_word
from core.disasm import format_instruction
from core.exceptions import BreakpointHit, CpuHalted
from core.execute import execute
from core.mem_if import WordMemory
from core.state import CPUState
from core.trace import StepTrace


class Runner:
    def __init__(
        self,
        state: CPUState,
        mem: WordMemory,
        *,
        cycle_counter: CycleCounter | None = None,
        break_pcs: set[int] | None = None,
        on_step: Callable[[StepTrace], None] | None = None,
    ) -> None:
        self.state = state
        self.mem = mem
        self.cycle_counter = cycle_counter if cycle_counter is not None else CycleCounter()
        self.break_pcs: set[int] = set(break_pcs) if break_pcs else set()
        self.on_step = on_step
        if isinstance(mem, SystemBus):
            mem.set_cycle_counter(self.cycle_counter)

    def step(self) -> None:
        if self.state.halted:
            raise CpuHalted("CPU is halted")
        old_pc = self.state.pc
        if old_pc in self.break_pcs:
            raise BreakpointHit(old_pc)
        word = self.mem.read_word(old_pc)
        ins = decode_word(word)
        explicit_pc = execute(self.state, self.mem, ins)
        if not self.state.halted:
            if not explicit_pc:
                self.state.set_pc(old_pc + 4)
        cost = cycles_for_mnemonic(ins.mnemonic)
        self.cycle_counter.add(cost)
        if isinstance(self.mem, SystemBus):
            self.mem.on_step_end(self.cycle_counter.value, self.state, self.state.pc)
        if self.on_step is not None:
            self.on_step(
                StepTrace(
                    pc=old_pc,
                    word=word & 0xFFFFFFFF,
                    disasm=format_instruction(ins),
                    cycles_after=self.cycle_counter.value,
                    halted_after=self.state.halted,
                )
            )

    def run(self, max_steps: int = 10_000) -> int:
        steps = 0
        while steps < max_steps:
            if self.state.halted:
                return steps
            self.step()
            steps += 1
        return steps
