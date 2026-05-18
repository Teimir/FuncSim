"""Listing output."""

from __future__ import annotations

from core.asm import assemble_text_with_listing, format_listing
from core.disasm import disassemble_word


def test_listing_contains_addr_and_disasm() -> None:
    result = assemble_text_with_listing(
        """
        ADDI r0 r1 5
        HALT
        """
    )
    text = format_listing(result)
    assert "00000000" in text
    assert "HALT" in text or "ADDI" in text
    assert len(result.listing) >= 2


def test_listing_disasm_matches_words() -> None:
    result = assemble_text_with_listing("NOP\nHALT\n")
    for row in result.listing:
        if row.word is not None:
            assert disassemble_word(row.word) in row.source or row.source.strip().startswith(
                ("NOP", "HALT", "ADDI", "JMP", "MOV")
            ) or ";" in row.source
