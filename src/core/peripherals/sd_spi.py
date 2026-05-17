"""Functional SD SPI MMIO model (apb_sd_spi register map, no bit-banged wires)."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from core.mmio_sd_regs import SdSpiRegs

REG_CTRL = SdSpiRegs.REG_CTRL
REG_DIV = SdSpiRegs.REG_DIV
REG_CMD = SdSpiRegs.REG_CMD
REG_ARG = SdSpiRegs.REG_ARG
REG_RESP0 = SdSpiRegs.REG_RESP0
REG_STATUS = SdSpiRegs.REG_STATUS
REG_BLKIDX = SdSpiRegs.REG_BLKIDX
REG_DATAIX = SdSpiRegs.REG_DATAIX
REG_DATARD = SdSpiRegs.REG_DATARD
REG_DATAWR = SdSpiRegs.REG_DATAWR
REGION_SIZE = SdSpiRegs.REGION_SIZE

ST_BUSY = 1 << 0
ST_READY = 1 << 1
ST_RX_VALID = 1 << 2
ST_IRQ_PENDING = 1 << 3
ST_ERROR = 1 << 4

MAX_SECTORS = 16
WORDS_PER_SECTOR = 128


class SdSpiMmio:
    """SPI command register block backed by in-memory card (optional host file sync)."""

    __slots__ = (
        "_en",
        "_cs_n",
        "_irq_en",
        "_irq_pending",
        "_busy",
        "_ready",
        "_rx_valid",
        "_error",
        "_clk_div",
        "_cmd_idx",
        "_cmd_arg",
        "_resp0",
        "_blkidx",
        "_dataix",
        "_app_cmd_seen",
        "_card",
        "_path",
        "_fp",
    )

    def __init__(self) -> None:
        self._en = False
        self._cs_n = True
        self._irq_en = False
        self._irq_pending = False
        self._busy = False
        self._ready = False
        self._rx_valid = False
        self._error = False
        self._clk_div = 8
        self._cmd_idx = 0
        self._cmd_arg = 0
        self._resp0 = 0xFFFFFFFF
        self._blkidx = 0
        self._dataix = 0
        self._app_cmd_seen = False
        self._card: list[int] = [0] * (MAX_SECTORS * WORDS_PER_SECTOR)
        self._path: Path | None = None
        self._fp: BinaryIO | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    def mount(self, path: Path, *, create_sectors: int | None = None) -> None:
        self.unmount()
        path = path.resolve()
        if create_sectors is not None and create_sectors > 0:
            path.parent.mkdir(parents=True, exist_ok=True)
            size = min(create_sectors, MAX_SECTORS) * 512
            if path.exists():
                path.unlink()
            path.write_bytes(b"\x00" * size)
        if path.exists():
            self._load_file(path)
        self._path = path

    def _load_file(self, path: Path) -> None:
        data = path.read_bytes()
        if len(data) % 512 != 0:
            raise ValueError("SD image must be multiple of 512 bytes")
        sectors = min(len(data) // 512, MAX_SECTORS)
        self._card = [0] * (MAX_SECTORS * WORDS_PER_SECTOR)
        for s in range(sectors):
            off = s * 512
            for w in range(WORDS_PER_SECTOR):
                self._card[s * WORDS_PER_SECTOR + w] = int.from_bytes(
                    data[off + w * 4 : off + w * 4 + 4],
                    "little",
                )
        self._fp = path.open("r+b")

    def unmount(self) -> None:
        if self._fp is not None:
            try:
                self._flush_to_file()
                self._fp.close()
            except OSError:
                pass
        self._fp = None
        self._path = None
        self._ready = False

    def _flush_to_file(self) -> None:
        if self._fp is None:
            return
        out = bytearray()
        for s in range(MAX_SECTORS):
            for w in range(WORDS_PER_SECTOR):
                out.extend(self._card[s * WORDS_PER_SECTOR + w].to_bytes(4, "little"))
        self._fp.seek(0)
        self._fp.write(bytes(out))
        self._fp.truncate(len(out))
        self._fp.flush()

    def _card_word_idx(self) -> int:
        return ((self._blkidx & 0xF) << 7) | (self._dataix & 0x7F)

    def _run_cmd(self) -> None:
        idx = self._cmd_idx & 0x3F
        self._busy = False
        self._rx_valid = True
        self._irq_pending = True
        self._error = False
        if idx == 0:
            self._resp0 = 0x0000_0001
            self._ready = False
            self._app_cmd_seen = False
        elif idx == 8:
            self._resp0 = 0x0000_01AA
        elif idx == 55:
            self._resp0 = 0x0000_0001
            self._app_cmd_seen = True
        elif idx == 41:
            if self._app_cmd_seen:
                self._ready = True
                self._resp0 = 0
                self._app_cmd_seen = False
            else:
                self._resp0 = 0x0000_0005
                self._error = True
        elif idx in (17, 24):
            if idx == 17 or idx == 24:
                self._blkidx = self._cmd_arg
            if self._ready and (self._blkidx & 0xFFFFFFFF) < MAX_SECTORS:
                self._resp0 = 0
            else:
                self._resp0 = 0x0000_0004
                self._error = True
        else:
            self._resp0 = 0x0000_0004
            self._error = True

    def read_word(self, rel_off: int) -> int:
        if rel_off == REG_CTRL:
            return (
                (1 if self._en else 0)
                | ((1 if self._cs_n else 0) << 1)
                | ((1 if self._irq_en else 0) << 2)
            )
        if rel_off == REG_DIV:
            return self._clk_div & 0xFFFF
        if rel_off == REG_CMD:
            return self._cmd_idx & 0x3F
        if rel_off == REG_ARG:
            return self._cmd_arg & 0xFFFFFFFF
        if rel_off == REG_RESP0:
            self._rx_valid = False
            return self._resp0 & 0xFFFFFFFF
        if rel_off == REG_STATUS:
            return (
                (ST_BUSY if self._busy else 0)
                | (ST_READY if self._ready else 0)
                | (ST_RX_VALID if self._rx_valid else 0)
                | (ST_IRQ_PENDING if self._irq_pending else 0)
                | (ST_ERROR if self._error else 0)
            )
        if rel_off == REG_BLKIDX:
            return self._blkidx & 0xFFFFFFFF
        if rel_off == REG_DATAIX:
            return self._dataix & 0x7F
        if rel_off in (REG_DATARD, REG_DATAWR):
            wi = self._card_word_idx()
            if wi < len(self._card):
                return self._card[wi] & 0xFFFFFFFF
            return 0
        raise IndexError(f"SD SPI read bad offset 0x{rel_off:x}")

    def write_word(self, rel_off: int, value: int) -> None:
        v = value & 0xFFFFFFFF
        if rel_off == REG_CTRL:
            self._en = bool(v & 1)
            self._cs_n = bool(v & 2)
            self._irq_en = bool(v & 4)
            if v & 8:
                self._irq_pending = False
            return
        if rel_off == REG_DIV:
            self._clk_div = v & 0xFFFF
            return
        if rel_off == REG_CMD:
            self._cmd_idx = v & 0x3F
            if v & 0x100 and self._en and not self._busy:
                self._busy = True
                self._rx_valid = False
                self._run_cmd()
            return
        if rel_off == REG_ARG:
            self._cmd_arg = v
            return
        if rel_off == REG_BLKIDX:
            self._blkidx = v
            return
        if rel_off == REG_DATAIX:
            self._dataix = v & 0x7F
            return
        if rel_off == REG_DATAWR:
            wi = self._card_word_idx()
            if wi < len(self._card):
                self._card[wi] = v
            return
        raise IndexError(f"SD SPI write bad offset 0x{rel_off:x}")

    def snapshot_info(self) -> dict[str, object]:
        return {
            "mode": "spi",
            "path": str(self._path) if self._path else None,
            "ready": self._ready,
            "blkidx": self._blkidx,
            "dataix": self._dataix,
            "last_resp": self._resp0,
        }
