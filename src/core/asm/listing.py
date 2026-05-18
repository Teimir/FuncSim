"""Listing file generation."""

from __future__ import annotations

from core.asm.driver import AsmResult, ListingRow


def format_listing(result: AsmResult, *, base: int = 0) -> str:
    from core.disasm import disassemble_word
    lines: list[str] = []
    for row in result.listing:
        addr = row.addr
        if row.word is None:
            lines.append(f"{addr:08x}          ; {row.source.strip()}")
            continue
        dis = disassemble_word(row.word)
        lines.append(f"{addr:08x}  {row.word:08x}  {dis:<32}  ; {row.source.strip()}")
    return "\n".join(lines) + "\n"
