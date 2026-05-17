"""CPU model exceptions."""


class CpuError(Exception):
    """Base for simulator errors."""


class IllegalInstruction(CpuError):
    """Unknown or reserved encoding."""


class MisalignedAccess(CpuError):
    """Word access at address not divisible by 4."""


class CpuHalted(CpuError):
    """Execution stopped via HALT."""


class BreakpointHit(CpuError):
    """Execution stopped at a breakpoint PC."""

    def __init__(self, pc: int) -> None:
        super().__init__(f"breakpoint hit at 0x{pc:x}")
        self.pc = pc


class WatchpointHit(CpuError):
    """Memory access hit a watch address."""

    def __init__(self, addr: int, kind: str) -> None:
        super().__init__(f"watchpoint {kind} at 0x{addr:x}")
        self.addr = addr
        self.kind = kind
