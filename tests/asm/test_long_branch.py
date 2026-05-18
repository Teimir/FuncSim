"""Long-branch veneers beyond imm11 range."""

from __future__ import annotations

from core.asm import assemble_text


def test_long_branch_unconditional() -> None:
    lines = ["B target\n"]
    lines.extend(["NOP\n"] * 300)
    lines.append("target:\n")
    lines.append("HALT\n")
    words = assemble_text("".join(lines))
    assert len(words) > 302
