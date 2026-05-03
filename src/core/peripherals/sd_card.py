"""Functional SD-like block device: MMIO + host file, 512-byte sectors (no SPI protocol)."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import BinaryIO


SECTOR_SIZE = 512
WORD_COUNT = SECTOR_SIZE // 4

# MMIO layout relative to SD region base
REG_CTRL = 0x00
REG_STATUS = 0x04
REG_LBA = 0x08
DATA_BASE = 0x10
REGION_SIZE = DATA_BASE + SECTOR_SIZE  # 0x210

# CTRL command (low byte of written word)
CMD_READ = 1
CMD_WRITE = 2
CMD_FLUSH = 3

# STATUS bits
ST_READY = 1 << 0
ST_ERROR = 1 << 2
ST_NO_MEDIUM = 1 << 3

ERR_NONE = 0
ERR_BAD_LBA = 1
ERR_IO = 2
ERR_BAD_IMAGE = 3


class SdCardMmio:
    """Word-aligned MMIO region; mount a file for persistent storage."""

    __slots__ = (
        "_path",
        "_fp",
        "_lba",
        "_buf",
        "_status",
        "_err_code",
    )

    def __init__(self) -> None:
        self._path: Path | None = None
        self._fp: BinaryIO | None = None
        self._lba = 0
        self._buf = bytearray(SECTOR_SIZE)
        self._status = ST_NO_MEDIUM
        self._err_code = ERR_NONE

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def is_mounted(self) -> bool:
        return self._fp is not None

    def snapshot_info(self) -> dict[str, object]:
        sectors = 0
        if self._fp is not None:
            try:
                pos = self._fp.tell()
                self._fp.seek(0, 2)
                n = self._fp.tell()
                self._fp.seek(pos, 0)
                sectors = n // SECTOR_SIZE
            except OSError:
                sectors = 0
        return {
            "path": str(self._path) if self._path else None,
            "mounted": self.is_mounted,
            "lba_reg": self._lba,
            "status": self._status,
            "err_code": self._err_code,
            "sectors": sectors,
            "buffer_preview": bytes(self._buf[:16]).hex(" "),
        }

    def mount(self, path: Path, *, create_sectors: int | None = None) -> None:
        self.unmount()
        path = path.resolve()
        if create_sectors is not None and create_sectors > 0:
            path.parent.mkdir(parents=True, exist_ok=True)
            size = create_sectors * SECTOR_SIZE
            if path.exists():
                path.unlink()
            path.write_bytes(b"\x00" * size)
        if not path.exists():
            raise FileNotFoundError(path)
        size = path.stat().st_size
        if size % SECTOR_SIZE != 0:
            raise ValueError(f"SD image size {size} is not a multiple of {SECTOR_SIZE}")
        self._path = path
        self._fp = path.open("r+b")
        self._status = ST_READY
        self._err_code = ERR_NONE

    def unmount(self) -> None:
        if self._fp is not None:
            try:
                self._fp.flush()
            except OSError:
                pass
            try:
                self._fp.close()
            except OSError:
                pass
        self._fp = None
        self._path = None
        self._status = ST_NO_MEDIUM
        self._err_code = ERR_NONE

    def _set_error(self, code: int) -> None:
        self._err_code = code & 0xFF
        self._status = (self._status | ST_ERROR) & ~ST_READY

    def _clear_error(self) -> None:
        self._err_code = ERR_NONE
        self._status &= ~ST_ERROR

    def _sector_count(self) -> int:
        if self._fp is None:
            return 0
        pos = self._fp.tell()
        self._fp.seek(0, 2)
        n = self._fp.tell()
        self._fp.seek(pos, 0)
        return n // SECTOR_SIZE

    def _do_cmd(self, cmd: int) -> None:
        cmd &= 0xFF
        if cmd == 0:
            return
        self._clear_error()
        if self._fp is None:
            self._status = ST_NO_MEDIUM | ST_ERROR
            self._err_code = ERR_BAD_IMAGE
            return
        if cmd == CMD_FLUSH:
            try:
                self._fp.flush()
            except OSError:
                self._set_error(ERR_IO)
                return
            self._status |= ST_READY
            return
        nsec = self._sector_count()
        if self._lba >= nsec or self._lba < 0:
            self._set_error(ERR_BAD_LBA)
            return
        pos = self._lba * SECTOR_SIZE
        try:
            if cmd == CMD_READ:
                self._fp.seek(pos)
                data = self._fp.read(SECTOR_SIZE)
                if len(data) != SECTOR_SIZE:
                    self._set_error(ERR_IO)
                    return
                self._buf[:] = data
                self._status = ST_READY
            elif cmd == CMD_WRITE:
                self._fp.seek(pos)
                self._fp.write(self._buf)
                self._fp.flush()
                self._status = ST_READY
            else:
                self._set_error(ERR_BAD_LBA)
        except OSError:
            self._set_error(ERR_IO)

    def read_word(self, rel_off: int) -> int:
        if rel_off == REG_CTRL:
            return 0
        if rel_off == REG_STATUS:
            return (self._status & 0xFFFF) | (self._err_code << 16)
        if rel_off == REG_LBA:
            return self._lba & 0xFFFFFFFF
        if DATA_BASE <= rel_off < DATA_BASE + SECTOR_SIZE:
            if rel_off % 4 != 0:
                return 0
            bi = rel_off - DATA_BASE
            return struct.unpack_from("<I", self._buf, bi)[0]
        raise IndexError(f"SD MMIO read bad offset 0x{rel_off:x}")

    def write_word(self, rel_off: int, value: int) -> None:
        v = value & 0xFFFFFFFF
        if rel_off == REG_CTRL:
            self._do_cmd(v & 0xFF)
            return
        if rel_off == REG_STATUS:
            return
        if rel_off == REG_LBA:
            self._lba = v
            return
        if DATA_BASE <= rel_off < DATA_BASE + SECTOR_SIZE:
            if rel_off % 4 != 0:
                return
            bi = rel_off - DATA_BASE
            struct.pack_into("<I", self._buf, bi, v)
            return
        raise IndexError(f"SD MMIO write bad offset 0x{rel_off:x}")
