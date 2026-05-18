"""CLI e32c-asm / python -m cli.asm integration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.asm.conftest import ROOT


def _run_asm_cli(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "cli.asm", *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), check=False)


def test_cli_stdout_hex() -> None:
    r = _run_asm_cli(str(ROOT / "examples" / "boot_smoke.asm"))
    assert r.returncode == 0, r.stderr
    assert "0x" in r.stdout
    assert len(r.stdout.strip().splitlines()) >= 2


def test_cli_output_hex_file(tmp_path: Path) -> None:
    out = tmp_path / "out.hex"
    r = _run_asm_cli(str(ROOT / "examples" / "boot_smoke.asm"), "-o", str(out))
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "0x" in text


def test_cli_output_bin_file(tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    r = _run_asm_cli(
        str(ROOT / "examples" / "boot_smoke.asm"),
        "-o",
        str(out),
        "--format",
        "bin",
    )
    assert r.returncode == 0, r.stderr
    assert out.stat().st_size >= 4


def test_cli_link_handler(tmp_path: Path) -> None:
    out = tmp_path / "fw.hex"
    main = ROOT / "examples" / "blink_uart_irq_main.asm"
    handler = ROOT / "examples" / "blink_uart_irq_handler.asm"
    r = _run_asm_cli(
        str(main),
        "--link",
        f"{handler}@0x100",
        "-o",
        str(out),
    )
    assert r.returncode == 0, r.stderr
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 0x100 // 4


def test_cli_invalid_asm_exits_nonzero() -> None:
    bad = ROOT / "tests" / "asm" / "_bad_cli.asm"
    bad.write_text("NOTVALID 0\n", encoding="utf-8")
    try:
        r = _run_asm_cli(str(bad))
        assert r.returncode != 0
        assert "error" in r.stderr.lower()
    finally:
        bad.unlink(missing_ok=True)
