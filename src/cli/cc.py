"""E32C compile driver: assemble, link, optional bin/hex output."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.ld import _parse_segment
from core.asm import AssembleError, LinkSpec, link_programs
from core.elf import words_to_segment, write_elf32_exec


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="E32C compiler driver (asm -> ELF)")
    p.add_argument("-o", "--output", type=Path, default=Path("a.out"), help="Output file")
    p.add_argument(
        "-O",
        dest="out_kind",
        choices=("elf", "binary", "ihex"),
        default=None,
        help="Output kind (default: from -o suffix or elf)",
    )
    p.add_argument("sources", nargs="+", type=Path, help="Assembler sources")
    p.add_argument(
        "--link",
        action="append",
        metavar="PATH@ADDR",
        type=_parse_segment,
        help="Extra linked segment (repeatable)",
    )
    p.add_argument("--image-size", type=int, default=None, help="Pad linked image (words)")
    p.add_argument("--entry", type=lambda s: int(s, 0), default=0, help="Entry PC")
    p.add_argument("--base", type=lambda s: int(s, 0), default=0, help="Load address of first source")
    args = p.parse_args(argv)

    specs = [LinkSpec(args.sources[0], origin=args.base)]
    for extra in args.sources[1:]:
        specs.append(LinkSpec(extra, origin=args.base))
    if args.link:
        for path, addr in args.link:
            specs.append(LinkSpec(path, origin=addr))

    try:
        words = link_programs(specs, image_size=args.image_size, fill=0)
    except AssembleError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    base = min(s.origin for s in specs)
    entry = args.entry if args.entry else base
    segment = words_to_segment(words, vaddr=base)

    out_kind = args.out_kind
    if out_kind is None:
        out_kind = {".elf": "elf", ".bin": "binary", ".hex": "ihex"}.get(args.output.suffix.lower(), "elf")

    if out_kind == "elf":
        write_elf32_exec(args.output, [segment], entry=entry)
        print(f"Wrote ELF {args.output} ({len(words)} words, entry 0x{entry:x})")
        return 0

    elf_tmp = args.output.with_suffix(".elf") if out_kind != "elf" else args.output
    write_elf32_exec(elf_tmp, [segment], entry=entry)

    from cli.objcopy import main as objcopy_main

    fmt = "binary" if out_kind == "binary" else "ihex"
    return objcopy_main([str(elf_tmp), str(args.output), "-O", fmt, "-I", "elf"])


if __name__ == "__main__":
    raise SystemExit(main())
