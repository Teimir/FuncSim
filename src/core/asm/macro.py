"""Macro definition and expansion."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.asm.errors import AssembleError

MAX_MACRO_DEPTH = 32

_MACRO_START = re.compile(r"^\.macro\s+(\w+)\s*(.*)$", re.IGNORECASE)
_MACRO_END = re.compile(r"^\.endm\s*$", re.IGNORECASE)
_LOCAL_LABEL = re.compile(r"^(\d+)([fb])$")


@dataclass
class MacroDef:
    name: str
    params: list[str]
    defaults: dict[str, str]
    body: list[str]


@dataclass
class MacroState:
    defs: dict[str, MacroDef] = field(default_factory=dict)
    local_label_counter: int = 0
    local_labels: dict[tuple[int, str], str] = field(default_factory=dict)


def _parse_macro_header(rest: str) -> tuple[list[str], dict[str, str]]:
    params: list[str] = []
    defaults: dict[str, str] = {}
    for part in rest.replace(",", " ").split():
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            name, val = part.split("=", 1)
            name = name.strip()
            defaults[name] = val.strip()
            params.append(name)
        else:
            params.append(part)
    return params, defaults


def collect_macros(lines: list[tuple[str, int, str]]) -> tuple[list[tuple[str, int, str]], dict[str, MacroDef]]:
    """Strip .macro/.endm blocks into defs; return remaining lines."""
    out: list[tuple[str, int, str]] = []
    defs: dict[str, MacroDef] = {}
    i = 0
    while i < len(lines):
        file, ln, text = lines[i]
        frag = text.split("#", 1)[0].strip()
        m = _MACRO_START.match(frag)
        if not m:
            out.append((file, ln, text))
            i += 1
            continue
        name = m.group(1)
        params, defaults = _parse_macro_header(m.group(2))
        body: list[str] = []
        i += 1
        while i < len(lines):
            _, _, t = lines[i]
            f2 = t.split("#", 1)[0].strip()
            if _MACRO_END.match(f2):
                i += 1
                break
            body.append(t)
            i += 1
        else:
            raise AssembleError(f"{file}:{ln}: unclosed .macro {name}")
        defs[name.upper()] = MacroDef(name=name.upper(), params=params, defaults=defaults, body=body)
    return out, defs


def _subst_params(line: str, positional: dict[str, str], named: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key in named:
            return named[key]
        if key in positional:
            return positional[key]
        raise AssembleError(f"macro parameter {key!r} not bound")

    return re.sub(r"\{(\w+)\}", repl, line)


def expand_macro_invocation(
    name: str,
    args: list[str],
    macro: MacroDef,
    state: MacroState,
    depth: int,
) -> list[tuple[str, int, str]]:
    if depth >= MAX_MACRO_DEPTH:
        raise AssembleError(f"macro expansion depth exceeded ({MAX_MACRO_DEPTH})")
    positional: dict[str, str] = {}
    named = dict(macro.defaults)
    pos_idx = 0
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            named[k.strip()] = v.strip()
            continue
        if pos_idx < len(macro.params):
            p = macro.params[pos_idx]
            positional[p] = arg
            named[p] = arg
            pos_idx += 1

    state.local_label_counter += 1
    lid = state.local_label_counter
    expanded: list[tuple[str, int, str]] = []
    for body_line in macro.body:
        text = _subst_params(body_line, positional, named)
        frag = text.split("#", 1)[0].strip()
        lm = _LOCAL_LABEL.match(frag.rstrip(":"))
        if lm and frag.endswith(":"):
            num, direction = lm.group(1), lm.group(2)
            if direction == "f":
                label_name = f".__L{lid}_{num}_f"
                state.local_labels[(lid, num, "f")] = label_name
                text = f"{label_name}:"
            else:
                label_name = f".__L{lid}_{num}_b"
                state.local_labels[(lid, num, "b")] = label_name
                text = f"{label_name}:"
        expanded.append(("<macro>", 0, text))
    return expanded
