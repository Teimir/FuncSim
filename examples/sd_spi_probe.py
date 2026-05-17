#!/usr/bin/env python3
"""Exercise SD SPI MMIO: CMD0, CMD8, ACMD41, CMD17 read sector 0."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.bus import SystemBus
from core.memory import Memory
from core.peripherals.sd_spi import REG_ARG, REG_BLKIDX, REG_CMD, REG_CTRL, REG_DATAIX, REG_DATARD, REG_STATUS

ST_READY = 1 << 1
ST_RX_VALID = 1 << 2


def _cmd(bus: SystemBus, idx: int, arg: int = 0) -> int:
    bus.sd.write_word(REG_ARG, arg)
    bus.sd.write_word(REG_CTRL, 1)  # EN
    bus.sd.write_word(REG_CMD, idx | 0x100)
    return bus.sd.read_word(REG_STATUS)


def main() -> None:
    img = ROOT / "examples" / "_sd_spi_test.img"
    ram = Memory()
    bus = SystemBus(ram, sd_spi=True, sd_image=img, sd_create_sectors=4)

    _cmd(bus, 0)
    _cmd(bus, 8, 0x0000_01AA)
    _cmd(bus, 55)
    _cmd(bus, 41, 0x4000_0000)
    st = _cmd(bus, 17, 0)
    if not (st & ST_READY):
        raise SystemExit(f"FAIL: card not ready status=0x{st:x}")

    bus.sd.write_word(REG_BLKIDX, 0)
    bus.sd.write_word(REG_DATAIX, 0)
    w0 = bus.sd.read_word(REG_DATARD)
    print(f"sector0 word0 = 0x{w0:08x}")
    if w0 != 0:
        print("OK (non-zero allowed if image pre-filled)")
    print("OK sd_spi_probe")


if __name__ == "__main__":
    main()
