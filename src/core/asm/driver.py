"""Two-pass assembler driver."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from core.asm.encode import COND_ALIAS, assemble_line
from core.asm.errors import AssembleError
from core.asm.expr import eval_expr
from core.asm.macro import MacroDef, MacroState, expand_macro_invocation
from core.asm.parse import line_to_encoded_text, parse_line_body, split_operands
from core.asm.preprocess import _INCLUDE_RE, preprocess_file, preprocess_text
from core.asm.pseudo import BRANCH_MNEMONICS, expand_pseudo_line, resolve_branch_to_lines

_EQU_RE = re.compile(r"^\.equ\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$", re.IGNORECASE)
_ORG_RE = re.compile(r"^\.org\s+(.+)$", re.IGNORECASE)
_ALIGN_RE = re.compile(r"^\.align\s*(\d*)$", re.IGNORECASE)
_WORD_RE = re.compile(r"^\.word\s+(.+)$", re.IGNORECASE)
_SKIP_RE = re.compile(r"^\.skip\s+(.+)$", re.IGNORECASE)
_LABEL_RE = re.compile(r"^([A-Za-z_.][A-Za-z0-9_.]*)\s*:\s*(.*)$")


@dataclass
class ListingRow:
    addr: int
    word: int | None
    source: str
    file: str
    line_no: int


@dataclass
class AsmResult:
    words: list[int]
    listing: list[ListingRow] = field(default_factory=list)
    symbols: dict[str, int] = field(default_factory=dict)


@dataclass
class _Item:
    file: str
    line_no: int
    raw: str
    kind: str
    mnemonic: str = ""
    args: list[str] = field(default_factory=list)
    addr: int = 0
    size: int = 4


def _align_lc(lc: int, align: int) -> int:
    if align <= 0:
        align = 4
    mask = align - 1
    return (lc + mask) & ~mask


def _expand_macros_in_lines(
    lines: list[tuple[str, int, str]],
    macro_defs: dict[str, MacroDef],
) -> list[tuple[str, int, str]]:
    state = MacroState(defs=macro_defs)
    out: list[tuple[str, int, str]] = []

    def emit_expanded(exp: list[tuple[str, int, str]], d: int) -> None:
        for file, ln, t in exp:
            frag = t.split("#", 1)[0].strip()
            if not frag:
                continue
            parts = frag.split(None, 1)
            name = parts[0].upper()
            if name in macro_defs:
                args = split_operands(parts[1]) if len(parts) > 1 else []
                sub = expand_macro_invocation(name, args, macro_defs[name], state, d)
                emit_expanded(sub, d + 1)
            else:
                out.append((file, ln, t))

    for file, ln, text in lines:
        frag = text.split("#", 1)[0].strip()
        if not frag:
            continue
        parts = frag.split(None, 1)
        name = parts[0].upper()
        if name in macro_defs:
            args = split_operands(parts[1]) if len(parts) > 1 else []
            sub = expand_macro_invocation(name, args, macro_defs[name], state, 0)
            emit_expanded(sub, 1)
        else:
            out.append((file, ln, text))
    return out


def _branch_size(mnemonic: str, args: list[str], labels: dict[str, int], pc: int) -> int:
    if len(args) == 1 and args[0] not in labels:
        return 4
    try:
        lines = resolve_branch_to_lines(mnemonic, args, labels, pc)
        return 4 * len(lines) if lines else 4
    except AssembleError:
        return 4


def _collect_label_addresses(
    items: list[_Item],
    equ: dict[str, int],
    origin: int,
) -> dict[str, int]:
    """First-pass label addresses (4 bytes per instruction) for forward references."""
    labels: dict[str, int] = {}
    lc = origin
    for item in items:
        if item.kind == "label":
            labels[item.mnemonic] = lc
            if item.args and item.args[0]:
                lc += 4
            continue
        if item.kind == "org":
            lc = eval_expr(item.args[0], {**equ, **labels})
            continue
        if item.kind == "align":
            lc = _align_lc(lc, int(item.args[0], 0))
            continue
        if item.kind == "skip":
            lc += eval_expr(item.args[0], {**equ, **labels})
            continue
        if item.kind == "word":
            lc += 4
            continue
        if item.kind == "line":
            lc += 4
            continue
        lc += 4
    return labels


def _parse_logical_items(
    lines: list[tuple[str, int, str]],
) -> tuple[list[_Item], dict[str, int]]:
    equ: dict[str, int] = {}
    items: list[_Item] = []

    def symbols() -> dict[str, int]:
        return dict(equ)

    for file, line_no, raw in lines:
        frag = raw.split("#", 1)[0].strip()
        if not frag:
            continue

        if _INCLUDE_RE.match(frag):
            raise AssembleError(
                f"{file}:{line_no}: .include only valid in a file (use assemble_file), not bare text"
            )

        m_equ = _EQU_RE.match(frag)
        if m_equ:
            equ[m_equ.group(1)] = eval_expr(m_equ.group(2).strip(), symbols())
            continue

        m_org = _ORG_RE.match(frag)
        if m_org:
            items.append(_Item(file, line_no, raw, "org", args=[m_org.group(1).strip()]))
            continue

        m_align = _ALIGN_RE.match(frag)
        if m_align:
            n = m_align.group(1)
            items.append(_Item(file, line_no, raw, "align", args=[n or "4"]))
            continue

        m_word = _WORD_RE.match(frag)
        if m_word:
            for part in split_operands(m_word.group(1)):
                items.append(_Item(file, line_no, raw, "word", args=[part]))
            continue

        m_skip = _SKIP_RE.match(frag)
        if m_skip:
            items.append(_Item(file, line_no, raw, "skip", args=split_operands(m_skip.group(1))))
            continue

        m_label = _LABEL_RE.match(frag)
        if m_label:
            items.append(_Item(file, line_no, raw, "label", mnemonic=m_label.group(1), args=[m_label.group(2).strip()]))
            frag = m_label.group(2).strip()
            if not frag:
                continue

        parts = split_operands(frag)
        mnemonic = parts[0].upper()
        args = parts[1:]

        for expanded in expand_pseudo_line(mnemonic, args):
            items.append(_Item(file, line_no, raw, "line", args=[expanded]))

        if mnemonic in ("PUSH", "POP"):
            continue

        deferred = (
            (mnemonic in COND_ALIAS and len(args) == 1)
            or (mnemonic == "B" and len(args) == 1)
            or (mnemonic == "JMP" and len(args) == 1)
            or (mnemonic in BRANCH_MNEMONICS and len(args) in (1, 2))
        )
        if deferred:
            items.append(_Item(file, line_no, raw, "branch", mnemonic=mnemonic, args=args))
            continue

        items.append(_Item(file, line_no, raw, "insn", mnemonic=mnemonic, args=args))

    return items, equ


def _assign_addresses(
    items: list[_Item],
    equ: dict[str, int],
    origin: int,
) -> dict[str, int]:
    labels = _collect_label_addresses(items, equ, origin)

    for _ in range(16):
        new_labels: dict[str, int] = {}
        lc = origin
        for item in items:
            if item.kind == "label":
                new_labels[item.mnemonic] = lc
                frag = item.args[0] if item.args else ""
                if not frag:
                    continue
                parts = split_operands(frag)
                mnemonic = parts[0].upper()
                args = parts[1:]
                for expanded in expand_pseudo_line(mnemonic, args):
                    item.addr = lc
                    lc += 4
                if mnemonic in ("PUSH", "POP"):
                    continue
                deferred = (
                    (mnemonic in COND_ALIAS and len(args) == 1)
                    or (mnemonic == "B" and len(args) == 1)
                    or (mnemonic in BRANCH_MNEMONICS and len(args) in (1, 2))
                )
                if deferred:
                    sz = _branch_size(mnemonic, args, labels, lc)
                    item.addr = lc
                    item.size = sz
                    lc += sz
                else:
                    item.addr = lc
                    item.size = 4
                    lc += 4
                continue

            sym = {**equ, **labels}
            if item.kind == "org":
                lc = eval_expr(item.args[0], sym)
                continue
            if item.kind == "align":
                lc = _align_lc(lc, int(item.args[0], 0))
                continue
            if item.kind == "skip":
                item.addr = lc
                item.size = eval_expr(item.args[0], sym)
                lc += item.size
                continue
            if item.kind == "word":
                item.addr = lc
                item.size = 4
                lc += 4
                continue
            if item.kind == "branch":
                sz = _branch_size(item.mnemonic, item.args, {**labels, **new_labels}, lc)
                item.addr = lc
                item.size = sz
                lc += sz
                continue
            item.addr = lc
            item.size = 4
            lc += 4
        labels = new_labels

    return labels


def _emit_items(
    items: list[_Item],
    labels: dict[str, int],
    equ: dict[str, int],
    origin: int,
) -> AsmResult:
    symbols = {**equ, **labels}
    image: dict[int, int] = {}
    listing: list[ListingRow] = []

    for item in items:
        if item.kind in ("org", "align", "label"):
            if item.kind == "label" and not (item.args and item.args[0]):
                continue
            if item.kind == "label":
                pass
            else:
                continue

        sym = symbols
        if item.kind == "skip":
            count = item.size
            for off in range(0, count, 4):
                image[item.addr + off] = 0
            listing.append(ListingRow(item.addr, None, item.raw, item.file, item.line_no))
            continue
        if item.kind == "word":
            val = eval_expr(item.args[0], sym) & 0xFFFFFFFF
            image[item.addr] = val
            listing.append(ListingRow(item.addr, val, item.raw, item.file, item.line_no))
            continue

        lines_to_emit: list[str] = []
        if item.kind == "branch":
            lines_to_emit = resolve_branch_to_lines(item.mnemonic, item.args, labels, item.addr)
            if not lines_to_emit:
                frag = item.mnemonic + (" " + " ".join(item.args) if item.args else "")
                mnemonic, args = parse_line_body(frag, sym)
                lines_to_emit = [line_to_encoded_text(mnemonic, args)]
        elif item.kind == "line":
            lines_to_emit = item.args
        else:
            frag = item.mnemonic + (" " + " ".join(item.args) if item.args else "")
            mnemonic, args = parse_line_body(frag, sym)
            lines_to_emit = [line_to_encoded_text(mnemonic, args)]

        addr = item.addr
        for line in lines_to_emit:
            try:
                word = assemble_line(line)
            except AssembleError as e:
                raise AssembleError(f"{item.file}:{item.line_no}: {e}") from e
            image[addr] = word
            listing.append(ListingRow(addr, word, line, item.file, item.line_no))
            addr += 4

    if not image:
        return AsmResult(words=[], listing=listing, symbols=labels)

    max_addr = max(image.keys())
    size = max_addr - origin + 4
    words = [image.get(origin + off, 0) for off in range(0, size, 4)]
    return AsmResult(words=words, listing=listing, symbols=labels)


def assemble_text(
    text: str,
    *,
    origin: int = 0,
    source_name: str = "<stdin>",
) -> list[int]:
    lines, macro_defs = preprocess_text(text, source_name=source_name)
    lines = _expand_macros_in_lines(lines, macro_defs)
    items, equ = _parse_logical_items(lines)
    labels = _assign_addresses(items, equ, origin)
    return _emit_items(items, labels, equ, origin).words


def assemble_text_with_listing(
    text: str,
    *,
    origin: int = 0,
    source_name: str = "<stdin>",
) -> AsmResult:
    lines, macro_defs = preprocess_text(text, source_name=source_name)
    lines = _expand_macros_in_lines(lines, macro_defs)
    items, equ = _parse_logical_items(lines)
    labels = _assign_addresses(items, equ, origin)
    return _emit_items(items, labels, equ, origin)


def assemble_file(path: Path | str, *, origin: int = 0, includes: bool = True) -> list[int]:
    p = Path(path)
    if includes:
        lines, macro_defs = preprocess_file(p)
    else:
        lines, macro_defs = preprocess_text(p.read_text(encoding="utf-8"), source_name=str(p))
    lines = _expand_macros_in_lines(lines, macro_defs)
    items, equ = _parse_logical_items(lines)
    labels = _assign_addresses(items, equ, origin)
    return _emit_items(items, labels, equ, origin).words
