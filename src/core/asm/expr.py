"""Expression evaluator for .equ and operands."""

from __future__ import annotations

import re

from core.asm.errors import AssembleError

_TOKEN_RE = re.compile(
    r"\s*("
    r"0[xX][0-9a-fA-F]+|"
    r"0[bB][01]+|"
    r"0[oO][0-7]+|"
    r"\d+|"
    r"[A-Za-z_][A-Za-z0-9_]*|"
    r"<<|>>|"
    r"[()+\-*/&|^~]"
    r")",
)


def _parse_int(tok: str) -> int:
    if tok.startswith(("0x", "0X")):
        return int(tok, 16)
    if tok.startswith(("0b", "0B")):
        return int(tok, 2)
    if tok.startswith(("0o", "0O")):
        return int(tok, 8)
    return int(tok, 10)


class _Parser:
    def __init__(self, text: str, symbols: dict[str, int]) -> None:
        self._text = text.strip()
        self._symbols = symbols
        self._pos = 0
        self._cur: str | None = None
        self._advance()

    def _advance(self) -> None:
        while self._pos < len(self._text):
            m = _TOKEN_RE.match(self._text, self._pos)
            if not m:
                raise AssembleError(f"bad expression at: {self._text[self._pos :]}")
            self._pos = m.end()
            tok = m.group(1)
            if tok.strip():
                self._cur = tok
                return
        self._cur = None

    def parse(self) -> int:
        val = self._parse_or()
        if self._cur is not None:
            raise AssembleError(f"trailing tokens in expression: {self._cur}")
        return val & 0xFFFFFFFF

    def _parse_or(self) -> int:
        val = self._parse_xor()
        while self._cur == "|":
            self._advance()
            val |= self._parse_xor()
        return val

    def _parse_xor(self) -> int:
        val = self._parse_and()
        while self._cur == "^":
            self._advance()
            val ^= self._parse_and()
        return val

    def _parse_and(self) -> int:
        val = self._parse_shift()
        while self._cur == "&":
            self._advance()
            val &= self._parse_shift()
        return val

    def _parse_shift(self) -> int:
        val = self._parse_add()
        while self._cur in ("<<", ">>"):
            op = self._cur
            self._advance()
            rhs = self._parse_add()
            if op == "<<":
                val = (val << rhs) & 0xFFFFFFFF
            else:
                val = (val >> rhs) & 0xFFFFFFFF
        return val

    def _parse_add(self) -> int:
        val = self._parse_mul()
        while self._cur in ("+", "-"):
            op = self._cur
            self._advance()
            rhs = self._parse_mul()
            if op == "+":
                val = (val + rhs) & 0xFFFFFFFF
            else:
                val = (val - rhs) & 0xFFFFFFFF
        return val

    def _parse_mul(self) -> int:
        val = self._parse_unary()
        while self._cur == "*":
            self._advance()
            val = (val * self._parse_unary()) & 0xFFFFFFFF
        return val

    def _parse_unary(self) -> int:
        if self._cur == "-":
            self._advance()
            return (-self._parse_unary()) & 0xFFFFFFFF
        if self._cur == "~":
            self._advance()
            return (~self._parse_unary()) & 0xFFFFFFFF
        if self._cur == "+":
            self._advance()
            return self._parse_unary()
        return self._parse_atom()

    def _parse_atom(self) -> int:
        if self._cur == "(":
            self._advance()
            val = self._parse_or()
            if self._cur != ")":
                raise AssembleError("expected ')'")
            self._advance()
            return val
        if self._cur is None:
            raise AssembleError("empty expression")
        tok = self._cur
        if re.match(r"^-?\d+$", tok) or re.match(r"^0[xXbBoO]", tok):
            self._advance()
            return _parse_int(tok) & 0xFFFFFFFF
        if tok[0].isdigit() or tok.startswith("0x"):
            self._advance()
            return _parse_int(tok) & 0xFFFFFFFF
        if tok in self._symbols:
            self._advance()
            return self._symbols[tok] & 0xFFFFFFFF
        raise AssembleError(f"undefined symbol {tok!r}")


def eval_expr(text: str, symbols: dict[str, int]) -> int:
    return _Parser(text, symbols).parse()
