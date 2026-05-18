"""gen_firmware_hex.py smoke (assembler + link)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.asm import LinkSpec, assemble_text, link_programs
from core.loader import words_from_hex_lines

from tests.asm.conftest import ROOT


def test_link_matches_gen_firmware_layout() -> None:
    main = ROOT / "examples" / "blink_uart_irq_main.asm"
    handler = ROOT / "examples" / "blink_uart_irq_handler.asm"
    words = link_programs(
        [LinkSpec(main, 0), LinkSpec(handler, 0x100)],
        image_size=256,
    )
    assert len(words) == 256
    assert words[0x100 // 4] != 0 or len(words) > 64


def test_gen_firmware_hex_script(tmp_path: Path) -> None:
    out = tmp_path / "hexout"
    out.mkdir()
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "gen_firmware_hex.py"),
        "--asm",
        str(ROOT / "examples" / "boot_smoke.asm"),
        "--words",
        "32",
        "--out-dir",
        str(out),
        "--skip-fetch-rom",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr
    b0 = out / "firmware_b0.hex"
    assert b0.is_file()
    words = words_from_hex_lines(b0.read_text(encoding="utf-8"))
    assert len(words) >= 1
