"""CPU model exceptions."""


class CpuError(Exception):
    """Base for simulator errors."""


class IllegalInstruction(CpuError):
    """Unknown or reserved encoding."""


class MisalignedAccess(CpuError):
    """Word access at address not divisible by 4."""


class CpuHalted(CpuError):
    """Execution stopped via HALT."""
