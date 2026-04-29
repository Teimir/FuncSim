"""Load program images into memory."""

from __future__ import annotations

from pathlib import Path

from core.memory import Memory


def load_binary(mem: Memory, addr: int, path: Path) -> None:
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


def load_words(mem: Memory, addr: int, words: list[int]) -> None:
    a = addr
    for w in words:
        mem.write_word(a, w)
        a += 4
