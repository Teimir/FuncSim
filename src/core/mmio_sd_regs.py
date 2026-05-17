"""GENERATED FILE — do not edit by hand."""
# Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py

from __future__ import annotations

# SD MMIO register offsets (relative to SD_OFFSET)

class SdBlockRegs:
    REG_CTRL = 0
    REG_STATUS = 4
    REG_LBA = 8
    REG_DATA = 0x10
    DATA_BASE = REG_DATA
    REGION_SIZE = 0x210


class SdSpiRegs:
    REG_CTRL = 0
    REG_DIV = 4
    REG_CMD = 8
    REG_ARG = 12
    REG_RESP0 = 0x10
    REG_STATUS = 0x14
    REG_BLKIDX = 0x18
    REG_DATAIX = 0x1c
    REG_DATARD = 0x20
    REG_DATAWR = 0x24
    REGION_SIZE = 0x28


__all__ = ["SdBlockRegs", "SdSpiRegs"]
