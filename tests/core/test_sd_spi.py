"""SD SPI peripheral protocol (Python model)."""

from core.bus import SystemBus
from core.memory import Memory
from core.peripherals.sd_spi import REG_CMD, REG_DATAIX, REG_DATARD, REG_DATAWR, REG_STATUS


def test_cmd41_initializes_ready() -> None:
    bus = SystemBus(Memory(), sd_spi=True)
    bus.sd.write_word(0x00, 1)
    for idx, arg in ((0, 0), (8, 0x0000_01AA), (55, 0), (41, 0x4000_0000)):
        bus.sd.write_word(0x0C, arg)
        bus.sd.write_word(REG_CMD, idx | 0x100)
    st = bus.sd.read_word(REG_STATUS)
    assert st & (1 << 1)  # READY


def test_resp0_read_clears_rx_valid() -> None:
    bus = SystemBus(Memory(), sd_spi=True)
    bus.sd.write_word(0x00, 1)
    bus.sd.write_word(0x0C, 0)
    bus.sd.write_word(REG_CMD, 0x100)
    assert bus.sd.read_word(REG_STATUS) & (1 << 2)
    _ = bus.sd.read_word(0x10)
    assert not (bus.sd.read_word(REG_STATUS) & (1 << 2))


def test_sector_write_read() -> None:
    bus = SystemBus(Memory(), sd_spi=True)
    bus.sd.write_word(0x00, 1)
    for idx, arg in ((0, 0), (8, 0x1AA), (55, 0), (41, 0x4000_0000)):
        bus.sd.write_word(0x0C, arg)
        bus.sd.write_word(REG_CMD, idx | 0x100)
    bus.sd.write_word(0x18, 0)
    bus.sd.write_word(REG_DATAIX, 0)
    bus.sd.write_word(REG_DATAWR, 0xDEADBEEF)
    bus.sd.write_word(REG_DATAIX, 0)
    w = bus.sd.read_word(REG_DATARD)
    assert w == 0xDEADBEEF
