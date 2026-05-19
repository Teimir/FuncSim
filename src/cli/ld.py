"""E32C linker: combine .asm segments and emit ELF32 (EM_E32C)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.asm import AssembleError, LinkSpec, link_programs
from core.elf import ElfSymbol, words_to_segment, write_elf32_exec


def _parse_segment(s: str) -> tuple[Path, int]:
    if "@" not in s:
        raise argparse.ArgumentTypeError("segment must be path@address")
    path_s, addr_s = s.rsplit("@", 1)
    return Path(path_s), int(addr_s, 0)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="E32C linker (ELF32 output)")
    p.add_argument("-o", "--output", type=Path, required=True, help="Output .elf file")
    p.add_argument(
        "segments",
        nargs="+",
        metavar="FILE@ADDR",
        type=_parse_segment,
        help="Assembler source and load address (byte address)",
    )
    p.add_argument(
        "--image-size",
        type=int,
        default=None,
        help="Minimum image size in 32-bit words (padding with zero)",
    )
    p.add_argument(
        "--entry",
        type=lambda s: int(s, 0),
        default=None,
        help="Entry PC (default: lowest segment origin)",
    )
    p.add_argument(
        "--symbol",
        action="append",
        metavar="NAME=ADDR",
        default=[],
        help="Add global symbol (repeatable)",
    )
    args = p.parse_args(argv)

    specs = [LinkSpec(path, origin=addr) for path, addr in args.segments]
    try:
        words = link_programs(specs, image_size=args.image_size, fill=0)
    except AssembleError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    base = min(addr for _, addr in args.segments)
    entry = args.entry if args.entry is not None else base
    segment = words_to_segment(words, vaddr=base)
    symbols: list[ElfSymbol] = []
    for item in args.symbol:
        if "=" not in item:
            print(f"error: bad --symbol {item!r}", file=sys.stderr)
            return 1
        name, addr_s = item.split("=", 1)
        symbols.append(ElfSymbol(name=name.strip(), value=int(addr_s, 0)))

    try:
        write_elf32_exec(args.output, [segment], entry=entry, symbols=symbols or None)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"linked {len(words)} words -> {args.output} (entry 0x{entry:x}, base 0x{base:x})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
