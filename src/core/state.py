"""CPU architectural state."""

from __future__ import annotations

from dataclasses import dataclass, field

from core import flags as F

SPR_SAVED_IRQ_PC = 0
SPR_IRQ_VECTOR = 1
# Бит i = 1: линия прерывания i замаскирована (не доставляется). 0 = все линии разрешены.
SPR_IRQ_MASK = 2

# Соглашение ABI (программное): указатель стека — **R30**. Аппаратно это обычный GPR.
GPR_STACK_POINTER = 30


@dataclass
class CPUState:
    """R31 is IP; R0 reads as 0 and ignores writes."""

    regs: list[int] = field(default_factory=lambda: [0] * 32)
    flags: int = 0
    halted: bool = False
    spr: dict[int, int] = field(default_factory=dict)
    irq_in_service: bool = False
    exclusive_addr: int | None = None
    exclusive_valid: bool = False

    def __post_init__(self) -> None:
        if len(self.regs) != 32:
            raise ValueError("regs must have length 32")
        self.regs = [x & 0xFFFFFFFF for x in self.regs]

    def reg_read(self, index: int) -> int:
        if index == 0:
            return 0
        return self.regs[index] & 0xFFFFFFFF

    def reg_write(self, index: int, value: int) -> None:
        if index == 0:
            return
        self.regs[index] = value & 0xFFFFFFFF

    @property
    def pc(self) -> int:
        return self.reg_read(31)

    def set_pc(self, value: int) -> None:
        self.reg_write(31, value & 0xFFFFFFFF)

    def spr_read(self, index: int) -> int:
        return int(self.spr.get(index, 0)) & 0xFFFFFFFF

    def spr_write(self, index: int, value: int) -> None:
        self.spr[index] = value & 0xFFFFFFFF

    def raise_irq(self, return_pc: int, line: int = 0) -> None:
        """Save return PC and jump to IRQ vector (RTL: blocked while irq_in_service)."""
        if self.irq_in_service:
            return
        if not (self.flags & F.FLAG_INTENABLE):
            return
        if line < 0 or line > 31:
            raise ValueError(f"irq line must be 0..31, got {line}")
        if self.spr_read(SPR_IRQ_MASK) & (1 << line):
            return
        self.irq_in_service = True
        self.spr_write(SPR_SAVED_IRQ_PC, return_pc & 0xFFFFFFFF)
        self.set_pc(self.spr_read(SPR_IRQ_VECTOR))
