from pathlib import Path

import yaml

from core.mmio_constants import GPIO_OFFSET, MMIO_BASE_DEFAULT, TIMER_OFFSET, UART_OFFSET
from core.mmio_timer_regs import TimerRegs
from core.mmio_uart_regs import UartRegs
from scripts.gen_mmio import main as gen_main


def _reg_offset(dev: dict, name: str) -> int:
    for reg in dev["registers"]:
        if reg["name"] == name:
            off = reg["offset"]
            return int(off, 0) if isinstance(off, str) else int(off)
    raise KeyError(name)


def test_mmio_offsets_match_yaml() -> None:
    root = Path(__file__).resolve().parents[2]
    doc = yaml.safe_load((root / "docs" / "isa" / "mmio_map.yaml").read_text(encoding="utf-8"))
    dev = doc["devices"]
    def _off(key: str) -> int:
        v = dev[key]["offset"]
        if isinstance(v, int):
            return v
        return int(str(v), 0)

    assert GPIO_OFFSET == _off("gpio")
    assert UART_OFFSET == _off("uart")
    assert TIMER_OFFSET == _off("timer")
    base = doc["mmio_base"]
    assert MMIO_BASE_DEFAULT == (int(base, 0) if isinstance(base, str) else int(base))


def test_uart_timer_regs_match_yaml() -> None:
    root = Path(__file__).resolve().parents[2]
    doc = yaml.safe_load((root / "docs" / "isa" / "mmio_map.yaml").read_text(encoding="utf-8"))
    uart = doc["devices"]["uart"]
    timer = doc["devices"]["timer"]

    assert UartRegs.REG_TXDATA == _reg_offset(uart, "TXDATA")
    assert UartRegs.REG_RXDATA == _reg_offset(uart, "RXDATA")
    assert UartRegs.REG_STATUS == _reg_offset(uart, "STATUS")
    assert UartRegs.REG_CTRL == _reg_offset(uart, "CTRL")
    assert UartRegs.FIFO_DEPTH == uart["fifo_depth"]

    assert TimerRegs.REG_COUNTER == _reg_offset(timer, "COUNTER")
    assert TimerRegs.REG_PERIOD_LO == _reg_offset(timer, "PERIOD_LO")
    assert TimerRegs.REG_PERIOD_HI == _reg_offset(timer, "PERIOD_HI")
    assert TimerRegs.REG_CTRL == _reg_offset(timer, "CTRL")
    assert TimerRegs.REG_PERIOD_LO_ALIAS == _reg_offset(timer, "PERIOD_LO_ALIAS")
    assert TimerRegs.REG_PERIOD_HI_ALIAS == _reg_offset(timer, "PERIOD_HI_ALIAS")


def test_gen_mmio_idempotent() -> None:
    gen_main()
    gen_main()
