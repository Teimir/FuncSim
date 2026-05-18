"""Assemble .asm sources to hex/bin with optional listing and linking."""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

from core.asm import (
    AssembleError,
    LinkSpec,
    assemble_text_with_listing,
    format_listing,
    link_programs,
)


def _parse_link(s: str) -> tuple[Path, int]:
    if "@" not in s:
        raise argparse.ArgumentTypeError("link spec must be path@address")
    path_s, addr_s = s.rsplit("@", 1)
    return Path(path_s), int(addr_s, 0)


def main() -> None:
    p = argparse.ArgumentParser(description="E32C assembler")
    p.add_argument("input", type=Path, nargs="?", default=None, help="Main source file")
    p.add_argument("extra", type=Path, nargs="*", help="Additional sources (legacy)")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output file (hex or bin)")
    p.add_argument(
        "--format",
        choices=("hex", "bin"),
        default=None,
        help="Output format (default: hex if -o ends with .hex else bin)",
    )
    p.add_argument("-l", "--listing", type=Path, default=None, help="Write listing file")
    p.add_argument("--base", type=lambda s: int(s, 0), default=0, help="Load address / origin")
    p.add_argument(
        "--link",
        action="append",
        metavar="PATH@ADDR",
        type=_parse_link,
        help="Link extra segment (repeatable), e.g. handler.asm@0x100",
    )
    args = p.parse_args()

    try:
        if args.input is None:
            text = sys.stdin.read()
            result = assemble_text_with_listing(text, origin=args.base, source_name="<stdin>")
        elif args.link:
            specs = [LinkSpec(args.input, origin=args.base)]
            for path, addr in args.link:
                specs.append(LinkSpec(path, origin=addr))
            words = link_programs(specs)
            result = assemble_text_with_listing(
                args.input.read_text(encoding="utf-8"),
                origin=args.base,
                source_name=str(args.input),
            )
            result.words = words
        else:
            result = assemble_text_with_listing(
                args.input.read_text(encoding="utf-8"),
                origin=args.base,
                source_name=str(args.input),
            )
    except AssembleError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    words = result.words
    fmt = args.format
    if fmt is None and args.output is not None:
        fmt = "bin" if args.output.suffix.lower() == ".bin" else "hex"

    if args.listing is not None:
        args.listing.write_text(format_listing(result, base=args.base), encoding="utf-8")

    out_data: str | bytes
    if fmt == "bin":
        out_data = b"".join(struct.pack("<I", w) for w in words)
    else:
        out_data = "\n".join(f"0x{w:08x}" for w in words) + ("\n" if words else "")

    if args.output is None:
        if isinstance(out_data, bytes):
            sys.stdout.buffer.write(out_data)
        else:
            sys.stdout.write(out_data)
    else:
        if isinstance(out_data, bytes):
            args.output.write_bytes(out_data)
        else:
            args.output.write_text(out_data, encoding="utf-8")


if __name__ == "__main__":
    main()
