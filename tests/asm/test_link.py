"""Multi-file linking."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.asm import AssembleError, LinkSpec, link_programs

ROOT = Path(__file__).resolve().parents[2]


def test_link_main_and_handler() -> None:
    main = ROOT / "examples" / "blink_uart_irq_main.asm"
    handler = ROOT / "examples" / "blink_uart_irq_handler.asm"
    words = link_programs(
        [
            LinkSpec(main, origin=0),
            LinkSpec(handler, origin=0x100),
        ],
        image_size=256,
    )
    assert len(words) == 256
    assert words[0x100 // 4] != 0 or len(words) > 0x100 // 4


def test_link_overlap_raises() -> None:
    a = ROOT / "tests" / "asm" / "_overlap_a.asm"
    b = ROOT / "tests" / "asm" / "_overlap_b.asm"
    a.write_text("NOP\nHALT\n", encoding="utf-8")
    b.write_text("ADDI 0 1 1\nHALT\n", encoding="utf-8")
    try:
        with pytest.raises(AssembleError):
            link_programs(
                [
                    LinkSpec(a, origin=0),
                    LinkSpec(b, origin=0),
                ],
            )
    finally:
        a.unlink(missing_ok=True)
        b.unlink(missing_ok=True)
