"""Include and initial line gathering."""

from __future__ import annotations

import re
from pathlib import Path

from core.asm.errors import AssembleError
from core.asm.macro import collect_macros

_INCLUDE_RE = re.compile(r'^\.include\s+["\']([^"\']+)["\']\s*$', re.IGNORECASE)


def read_lines(path: Path, *, include_stack: list[Path] | None = None) -> list[tuple[str, int, str]]:
    """Return (filename, line_no, raw_line) with .include expanded."""
    stack = list(include_stack or [])
    path = path.resolve()
    if path in stack:
        raise AssembleError(f"include cycle: {path}")
    stack.append(path)
    out: list[tuple[str, int, str]] = []
    text = path.read_text(encoding="utf-8")
    base = path.parent
    for i, raw in enumerate(text.splitlines(), start=1):
        frag = raw.split("#", 1)[0].strip()
        m = _INCLUDE_RE.match(frag)
        if m:
            inc = (base / m.group(1)).resolve()
            if not inc.is_file():
                raise AssembleError(f"{path}:{i}: cannot open include {inc}")
            out.extend(read_lines(inc, include_stack=stack))
            continue
        out.append((str(path), i, raw))
    return out


def preprocess_file(path: Path) -> tuple[list[tuple[str, int, str]], dict]:
    from core.asm.macro import MacroDef

    lines = read_lines(path)
    lines, macro_defs = collect_macros(lines)
    return lines, macro_defs


def _expand_includes_in_lines(
    lines: list[tuple[str, int, str]],
    base: Path | None,
) -> list[tuple[str, int, str]]:
    if base is None:
        return lines
    out: list[tuple[str, int, str]] = []
    for file, ln, raw in lines:
        frag = raw.split("#", 1)[0].strip()
        m = _INCLUDE_RE.match(frag)
        if m:
            inc = (base / m.group(1)).resolve()
            if not inc.is_file():
                raise AssembleError(f"{file}:{ln}: cannot open include {inc}")
            out.extend(read_lines(inc, include_stack=[base.resolve()]))
            continue
        out.append((file, ln, raw))
    return out


def preprocess_text(text: str, *, source_name: str = "<stdin>") -> tuple[list[tuple[str, int, str]], dict]:
    raw_lines = [(source_name, i, line) for i, line in enumerate(text.splitlines(), start=1)]
    base: Path | None = None
    if source_name != "<stdin>":
        p = Path(source_name)
        if p.is_file():
            base = p.parent
    raw_lines = _expand_includes_in_lines(raw_lines, base)
    return collect_macros(raw_lines)
