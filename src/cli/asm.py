"""Assemble .asm (one instruction per line) to hex words on stdout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.asm import AssembleError, assemble_text


def main() -> None:
    p = argparse.ArgumentParser(description="E32C assembler (minimal)")
    p.add_argument("input", type=Path, nargs="?", default=None, help="Source file (default: stdin)")
    args = p.parse_args()
    if args.input is None:
        text = sys.stdin.read()
    else:
        text = args.input.read_text(encoding="utf-8")
    try:
        words = assemble_text(text)
    except AssembleError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    for w in words:
        print(f"0x{w:08x}")


if __name__ == "__main__":
    main()
