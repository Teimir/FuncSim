#!/usr/bin/env python3
"""Create a small SD image, write sector 0 from Python via MMIO, read it back (regression helper).

Run from repo root:
  python examples/sd_probe.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.bus import MMIO_BASE_DEFAULT, SD_OFFSET, SystemBus
from core.memory import Memory
from core.peripherals.sd_card import CMD_READ, CMD_WRITE, DATA_BASE, REG_CTRL, REG_LBA, ST_ERROR


def main() -> None:
    img = ROOT / "examples" / "_sd_probe_tmp.img"
    ram = Memory(256)
    bus = SystemBus(ram, sd_image=img, sd_create_sectors=2)
    base = MMIO_BASE_DEFAULT + SD_OFFSET

    bus.write_word(base + DATA_BASE, 0xAABBCCDD)
    bus.write_word(base + REG_LBA, 0)
    bus.write_word(base + REG_CTRL, CMD_WRITE)
    if bus.read_word(base + REG_STATUS) & ST_ERROR:
        print("FAIL: write command error")
        sys.exit(1)

    bus.write_word(base + DATA_BASE, 0)
    bus.write_word(base + REG_CTRL, CMD_READ)
    if bus.read_word(base + REG_STATUS) & ST_ERROR:
        print("FAIL: read command error")
        sys.exit(1)
    w = bus.read_word(base + DATA_BASE)
    if w != 0xAABBCCDD:
        print(f"FAIL: expected 0xAABBCCDD got 0x{w:08x}")
        sys.exit(1)
    print("OK: SD MMIO read/write sector 0")
    bus.sd.unmount()
    img.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
