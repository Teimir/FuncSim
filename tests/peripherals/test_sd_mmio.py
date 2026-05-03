"""SD / block MMIO (file-backed sectors)."""

from pathlib import Path

import pytest

from core.bus import MMIO_BASE_DEFAULT, SD_OFFSET, SystemBus
from core.memory import Memory
from core.peripherals.sd_card import (
    CMD_FLUSH,
    CMD_READ,
    CMD_WRITE,
    DATA_BASE,
    REG_CTRL,
    REG_LBA,
    REG_STATUS,
    ST_ERROR,
    ST_READY,
)


def test_sd_mount_read_write_roundtrip(tmp_path: Path) -> None:
    img = tmp_path / "disk.img"
    nsec = 4
    img.write_bytes(b"\x00" * (512 * nsec))
    ram = Memory(256)
    bus = SystemBus(ram, sd_image=img)
    base = MMIO_BASE_DEFAULT + SD_OFFSET

    bus.write_word(base + REG_LBA, 1)
    bus.write_word(base + REG_CTRL, CMD_READ)
    st = bus.read_word(base + REG_STATUS)
    assert st & ST_READY
    assert not (st & ST_ERROR)
    assert bus.read_word(base + DATA_BASE) == 0

    bus.write_word(base + DATA_BASE, 0x11223344)
    bus.write_word(base + REG_CTRL, CMD_WRITE)
    bus.write_word(base + REG_CTRL, CMD_FLUSH)

    bus2 = SystemBus(Memory(256), sd_image=img)
    b2 = MMIO_BASE_DEFAULT + SD_OFFSET
    bus2.write_word(b2 + REG_LBA, 1)
    bus2.write_word(b2 + REG_CTRL, CMD_READ)
    assert bus2.read_word(b2 + DATA_BASE) == 0x11223344


def test_sd_bad_lba(tmp_path: Path) -> None:
    img = tmp_path / "d.img"
    img.write_bytes(b"\x00" * 512)
    ram = Memory(256)
    bus = SystemBus(ram, sd_image=img)
    base = MMIO_BASE_DEFAULT + SD_OFFSET
    bus.write_word(base + REG_LBA, 99)
    bus.write_word(base + REG_CTRL, CMD_READ)
    assert bus.read_word(base + REG_STATUS) & ST_ERROR


def test_sd_no_medium() -> None:
    ram = Memory(256)
    bus = SystemBus(ram)
    base = MMIO_BASE_DEFAULT + SD_OFFSET
    bus.write_word(base + REG_LBA, 0)
    bus.write_word(base + REG_CTRL, CMD_READ)
    assert bus.read_word(base + REG_STATUS) & ST_ERROR


def test_sd_create_sectors(tmp_path: Path) -> None:
    img = tmp_path / "new.img"
    ram = Memory(256)
    bus = SystemBus(ram, sd_image=img, sd_create_sectors=2)
    assert img.stat().st_size == 1024
    base = MMIO_BASE_DEFAULT + SD_OFFSET
    bus.write_word(base + REG_LBA, 0)
    bus.write_word(base + REG_CTRL, CMD_READ)
    assert bus.read_word(base + REG_STATUS) & ST_READY


def test_sd_bad_image_size(tmp_path: Path) -> None:
    img = tmp_path / "bad.img"
    img.write_bytes(b"\x00" * 511)
    ram = Memory(256)
    with pytest.raises(ValueError, match="multiple"):
        SystemBus(ram, sd_image=img)
