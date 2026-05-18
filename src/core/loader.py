"""Load program images into memory."""

from __future__ import annotations

from pathlib import Path

from core.bus import SystemBus
from core.elf import ElfImage, parse_elf32
from core.memory import Memory


def load_binary(mem: Memory | SystemBus, addr: int, path: Path) -> None:
    data = path.read_bytes()
    mem.write_bytes(addr, data)


def words_from_hex_lines(text: str) -> list[int]:
    out: list[int] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(int(s, 16) & 0xFFFFFFFF)
    return out


def load_words(mem: Memory | SystemBus, addr: int, words: list[int]) -> None:
    a = addr
    for w in words:
        mem.write_word(a, w)
        a += 4


def load_elf(mem: Memory | SystemBus, path: Path, *, base: int | None = None) -> tuple[int, int]:
    """Load PT_LOAD segments from an E32C ELF. Returns (load_addr, entry_pc)."""
    image = parse_elf32(path)
    load_base, blob = image.loadable_blob()
    addr = load_base if base is None else base
    mem.write_bytes(addr, blob)
    return addr, image.entry


def load_elf_image(mem: Memory | SystemBus, image: ElfImage, *, base: int | None = None) -> tuple[int, int]:
    load_base, blob = image.loadable_blob()
    addr = load_base if base is None else base
    mem.write_bytes(addr, blob)
    return addr, image.entry
