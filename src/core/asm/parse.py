"""Parse instruction lines and operands."""

from __future__ import annotations

import re

from core.asm.expr import eval_expr
from core.asm.errors import AssembleError

_REG_RE = re.compile(r"^[rR](\d+)$")
_LABEL_DEF_RE = re.compile(r"^([A-Za-z_.][A-Za-z0-9_.]*)\s*:\s*(.*)$")
_LOCAL_LABEL_RE = re.compile(r"^(\d+)([fb])$")


def normalize_reg(tok: str) -> str:
    m = _REG_RE.match(tok)
    if m:
        n = int(m.group(1))
        if n < 0 or n > 31:
            raise AssembleError(f"register out of range: {tok}")
        return str(n)
    return tok


def split_operands(s: str) -> list[str]:
    s = s.strip()
    if not s:
        return []
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    i = 0
    while i < len(s):
        c = s[i]
        if c in "([{":
            depth += 1
            cur.append(c)
        elif c in ")]}":
            depth -= 1
            cur.append(c)
        elif c in ", \t" and depth == 0:
            if cur:
                parts.append("".join(cur).strip())
                cur = []
            while i < len(s) and s[i] in ", \t":
                i += 1
            continue
        else:
            cur.append(c)
        i += 1
    if cur:
        parts.append("".join(cur).strip())
    return parts


def parse_line_body(frag: str, symbols: dict[str, int]) -> tuple[str, list[int]]:
    """Return mnemonic and numeric operand list."""
    parts = split_operands(frag)
    if not parts:
        raise AssembleError("empty line")
    mnemonic = parts[0].upper()
    args: list[int] = []
    for raw in parts[1:]:
        tok = normalize_reg(raw)
        if re.match(r"^-?(0[xX]|0[bB]|0[oO]|\d)", tok):
            args.append(int(tok, 0))
        elif tok in symbols:
            args.append(symbols[tok] & 0xFFFFFFFF)
        else:
            try:
                args.append(eval_expr(tok, symbols))
            except AssembleError:
                raise AssembleError(f"cannot parse operand {raw!r}") from None
    return mnemonic, args


def line_to_encoded_text(mnemonic: str, args: list[int]) -> str:
    if not args:
        return mnemonic
    return mnemonic + " " + " ".join(str(a) for a in args)
