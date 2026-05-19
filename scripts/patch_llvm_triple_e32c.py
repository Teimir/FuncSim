#!/usr/bin/env python3
"""Add Triple::e32c to llvm-project (idempotent)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIPLE_CPP = ROOT / "toolchain/llvm-project/llvm/lib/TargetParser/Triple.cpp"


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if 'case e32c:' in text and 'Triple::e32c' in text:
        return

    text = text.replace(
        '  case lanai:          return "lanai";\n',
        '  case lanai:          return "lanai";\n  case e32c:           return "e32c";\n',
        1,
    )
    text = text.replace(
        '  case lanai:       return "lanai";\n',
        '  case lanai:       return "lanai";\n  case e32c:        return "e32c";\n',
        1,
    )
    text = text.replace(
        '    .Case("lanai", lanai)\n',
        '    .Case("lanai", lanai)\n    .Case("e32c", e32c)\n',
        1,
    )
    text = text.replace(
        '          .Case("lanai", Triple::lanai)\n',
        '          .Case("lanai", Triple::lanai)\n          .Case("e32c", Triple::e32c)\n',
        1,
    )
    for pat, repl in [
        (r"(  case Triple::lanai:\n)", r"\1  case Triple::e32c:\n"),
        (r"(  case llvm::Triple::lanai:\n)", r"\1  case llvm::Triple::e32c:\n"),
    ]:
        text, n = re.subn(pat, repl, text, count=1)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    if not TRIPLE_CPP.is_file():
        sys.exit(f"missing {TRIPLE_CPP}")
    patch(TRIPLE_CPP)
    print(f"Patched {TRIPLE_CPP}")
