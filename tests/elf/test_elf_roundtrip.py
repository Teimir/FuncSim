"""ELF32 EM_E32C write/read roundtrip."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.asm import LinkSpec, assemble_text, link_programs
from core.elf import EM_E32C, parse_elf32, words_to_segment, write_elf32_exec
from core.loader import load_elf

ROOT = Path(__file__).resolve().parents[2]


def test_elf_machine_constant() -> None:
    assert EM_E32C == 0xE32C


def test_elf_roundtrip_smoke() -> None:
    asm = (ROOT / "examples" / "boot_smoke.asm").read_text(encoding="utf-8")
    words = assemble_text(asm)
    seg = words_to_segment(words, vaddr=0)
    path = ROOT / "tests" / "elf" / "_roundtrip.elf"
    try:
        write_elf32_exec(path, [seg], entry=0)
        back = parse_elf32(path)
        assert back.entry == 0
        _, got = back.words_at()
        assert got == words
    finally:
        path.unlink(missing_ok=True)


def test_elf_link_roundtrip() -> None:
    main = ROOT / "examples" / "blink_uart_irq_main.asm"
    handler = ROOT / "examples" / "blink_uart_irq_handler.asm"
    words = link_programs([LinkSpec(main, 0), LinkSpec(handler, 0x100)], image_size=64)
    path = ROOT / "tests" / "elf" / "_link.elf"
    try:
        write_elf32_exec(path, [words_to_segment(words, vaddr=0)], entry=0)
        from core.memory import Memory

        mem = Memory()
        base, entry = load_elf(mem, path)
        assert base == 0
        assert mem.read_word(0x100) == words[0x100 // 4]
    finally:
        path.unlink(missing_ok=True)


def test_e32c_ld_cli(tmp_path: Path) -> None:
    out = tmp_path / "out.elf"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.ld",
            "-o",
            str(out),
            f"{ROOT / 'examples' / 'boot_smoke.asm'}@0",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src")},
    )
    assert r.returncode == 0, r.stderr
    img = parse_elf32(out)
    assert len(img.segments) >= 1


def test_gen_firmware_hex_elf_path(tmp_path: Path) -> None:
    out_elf = tmp_path / "smoke.elf"
    words = assemble_text((ROOT / "examples" / "boot_smoke.asm").read_text(encoding="utf-8"))
    write_elf32_exec(out_elf, [words_to_segment(words, vaddr=0)], entry=0)
    out_hex = tmp_path / "hexout"
    out_hex.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "gen_firmware_hex.py"),
            "--elf",
            str(out_elf),
            "--words",
            "32",
            "--out-dir",
            str(out_hex),
            "--skip-fetch-rom",
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src")},
    )
    assert r.returncode == 0, r.stderr
    b0 = out_hex / "firmware_b0.hex"
    assert b0.is_file()
    back = parse_elf32(out_elf)
    _, got = back.words_at()
    assert got[: len(words)] == words[: len(got)]
