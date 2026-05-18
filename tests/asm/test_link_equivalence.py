"""link_programs matches manual padding + handler glue."""

from __future__ import annotations

from pathlib import Path

from core.asm import LinkSpec, assemble_text, link_programs

from tests.asm.conftest import ROOT


def _manual_glue(main: str, handler: str, handler_addr: int) -> list[int]:
    words = assemble_text(main)
    idx = handler_addr // 4
    while len(words) < idx:
        words.append(0)
    words.extend(assemble_text(handler))
    return words


def test_irq_pair_matches_manual() -> None:
    main_path = ROOT / "examples" / "blink_uart_irq_main.asm"
    handler_path = ROOT / "examples" / "blink_uart_irq_handler.asm"
    main = main_path.read_text(encoding="utf-8")
    handler = handler_path.read_text(encoding="utf-8")
    manual = _manual_glue(main, handler, 0x100)
    linked = link_programs(
        [
            LinkSpec(main_path, origin=0),
            LinkSpec(handler_path, origin=0x100),
        ],
    )
    assert len(linked) >= len(manual)
    for i, (a, b) in enumerate(zip(manual, linked[: len(manual)])):
        assert a == b, f"word index {i}: manual={a:#x} linked={b:#x}"


def test_link_with_image_size_padding() -> None:
    main_path = ROOT / "examples" / "boot_smoke.asm"
    words = link_programs([LinkSpec(main_path, origin=0)], image_size=32)
    assert len(words) == 32
    assert any(w == 0xFFFFFFFF for w in words) or words[0] != 0
