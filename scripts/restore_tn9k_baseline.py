#!/usr/bin/env python3
"""Copy frozen hello firmware from test/tn9k/baseline/ into test/src/."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "test" / "tn9k" / "baseline"
DST = ROOT / "test" / "src"

FILES = (
    "firmware_rom.svh",
    "firmware_b0.hex",
    "firmware_b1.hex",
    "firmware_b2.hex",
    "firmware_b3.hex",
)


def main() -> int:
    missing = [name for name in FILES if not (BASE / name).is_file()]
    if missing:
        print(f"baseline missing: {missing}", file=sys.stderr)
        print("Run: python scripts/build_tn9k_firmware.py --profile hello --install-baseline", file=sys.stderr)
        return 1
    for name in FILES:
        shutil.copy2(BASE / name, DST / name)
        print(f"installed {DST / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
