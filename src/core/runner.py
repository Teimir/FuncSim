"""Fetch-decode-execute loop."""

from __future__ import annotations

from core.decode import decode_word
from core.exceptions import CpuHalted
from core.execute import execute
from core.memory import Memory
from core.state import CPUState


class Runner:
    def __init__(self, state: CPUState, mem: Memory) -> None:
        self.state = state
        self.mem = mem

    def step(self) -> None:
        if self.state.halted:
            raise CpuHalted("CPU is halted")
        old_pc = self.state.pc
        word = self.mem.read_word(old_pc)
        ins = decode_word(word)
        explicit_pc = execute(self.state, self.mem, ins)
        if self.state.halted:
            return
        if not explicit_pc:
            self.state.set_pc(old_pc + 4)

    def run(self, max_steps: int = 10_000) -> int:
        steps = 0
        while steps < max_steps:
            if self.state.halted:
                return steps
            self.step()
            steps += 1
        return steps
