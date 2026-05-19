"""Convert E32C ELF / bin / hex / asm images."""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

from core.asm import AssembleError, assemble_text
from core.elf import ElfImage, parse_elf32, words_to_segment, write_elf32_exec
from core.loader import words_from_hex_lines


def _read_input(path: Path, fmt: str, load_addr: int) -> ElfImage:
    if fmt == "elf":
        return parse_elf32(path)
    if fmt == "bin":
        data = path.read_bytes()
        words = [struct.unpack_from("<I", data, i)[0] & 0xFFFFFFFF for i in range(0, len(data), 4)]
        return ElfImage(entry=load_addr, segments=[words_to_segment(words, vaddr=load_addr)])
    if fmt == "hex":
        words = words_from_hex_lines(path.read_text(encoding="utf-8"))
        return ElfImage(entry=load_addr, segments=[words_to_segment(words, vaddr=load_addr)])
    if fmt == "asm":
        words = assemble_text(path.read_text(encoding="utf-8"))
        return ElfImage(entry=load_addr, segments=[words_to_segment(words, vaddr=load_addr)])
    raise ValueError(f"unsupported input format {fmt!r}")


def _format_from_suffix(path: Path) -> str | None:
    return {
        ".elf": "elf",
        ".bin": "bin",
        ".hex": "hex",
        ".asm": "asm",
    }.get(path.suffix.lower())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="E32C objcopy (ELF / bin / hex)")
    p.add_argument("input", type=Path, help="Input file")
    p.add_argument("output", type=Path, nargs="?", help="Output file (default: stdout for ihex)")
    p.add_argument(
        "-O",
        "--output-target",
        dest="out_format",
        choices=("elf", "binary", "ihex"),
        default=None,
        help="Output format",
    )
    p.add_argument(
        "-I",
        "--input-target",
        dest="in_format",
        choices=("elf", "bin", "hex", "asm"),
        default=None,
        help="Input format (default: from suffix)",
    )
    p.add_argument("--load-addr", type=lambda s: int(s, 0), default=0, help="Base for bin/hex/asm input")
    args = p.parse_args(argv)

    fmt_in = args.in_format or _format_from_suffix(args.input)
    if fmt_in is None:
        print("error: specify -I or use .elf/.bin/.hex/.asm input", file=sys.stderr)
        return 1

    out_fmt = args.out_format
    if out_fmt is None and args.output is not None:
        out_fmt = {
            ".elf": "elf",
            ".bin": "binary",
            ".hex": "ihex",
        }.get(args.output.suffix.lower())
    if out_fmt is None:
        out_fmt = "ihex"

    try:
        image = _read_input(args.input, fmt_in, args.load_addr)
    except (AssembleError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    _, words = image.words_at()

    if out_fmt == "elf":
        out_path = args.output or Path("a.out")
        write_elf32_exec(out_path, image.segments, entry=image.entry, symbols=image.symbols or None)
    elif out_fmt == "binary":
        _, blob = image.loadable_blob()
        out_path = args.output or Path("a.out")
        out_path.write_bytes(blob)
    else:
        lines = "\n".join(f"0x{w:08x}" for w in words) + ("\n" if words else "")
        if args.output is None:
            sys.stdout.write(lines)
        else:
            args.output.write_text(lines, encoding="utf-8")

    if args.output is not None:
        print(f"wrote {args.output} ({out_fmt})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
