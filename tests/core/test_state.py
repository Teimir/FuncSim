from core import flags as F
from core.state import SPR_IRQ_MASK, CPUState


def test_r0_read_zero_write_ignored() -> None:
    s = CPUState()
    s.reg_write(0, 0xDEADBEEF)
    assert s.reg_read(0) == 0


def test_pc_is_r31() -> None:
    s = CPUState()
    s.set_pc(0x1000)
    assert s.pc == 0x1000
    assert s.reg_read(31) == 0x1000


def test_spr_roundtrip() -> None:
    s = CPUState()
    s.spr_write(6, 0x12345678)
    assert s.spr_read(6) == 0x12345678


def test_spr_core_info_read_only() -> None:
    from core.spr_constants import CORE_INFO_FULL, SPR_CORE_INFO

    s = CPUState()
    s.spr_write(SPR_CORE_INFO, 0xDEADBEEF)
    assert s.spr_read(SPR_CORE_INFO) == CORE_INFO_FULL


def test_raise_irq_when_enabled() -> None:
    s = CPUState()
    s.flags |= F.FLAG_INTENABLE
    s.spr_write(1, 0x4000)
    s.set_pc(0x100)
    s.raise_irq(return_pc=0x104)
    assert s.spr_read(0) == 0x104
    assert s.pc == 0x4000


def test_raise_irq_masked_line0() -> None:
    s = CPUState()
    s.flags |= F.FLAG_INTENABLE
    s.spr_write(1, 0x4000)
    s.spr_write(SPR_IRQ_MASK, 1)
    s.set_pc(0x100)
    s.raise_irq(return_pc=0x104, line=0)
    assert s.pc == 0x100
    assert s.spr_read(0) == 0
