#!/usr/bin/env python3
"""Start gdb_server on smoke.hex and run a short GDB batch (requires gdb in PATH)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    gdb = shutil.which("gdb")
    if gdb is None:
        print("SKIP: gdb not in PATH")
        return 0

    hex_path = ROOT / "examples" / "smoke.hex"
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "cli.gdb_server",
            "--hex",
            str(hex_path),
            "--port",
            "3333",
        ],
        cwd=ROOT,
        env={**dict(**__import__("os").environ), "PYTHONPATH": str(ROOT / "src")},
    )
    try:
        time.sleep(0.5)
        r = subprocess.run(
            [
                gdb,
                "-batch",
                "-ex",
                "target remote 127.0.0.1:3333",
                "-ex",
                "info registers r1 pc",
                "-ex",
                "stepi",
                "-ex",
                "info registers pc",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        print(r.stdout)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            return r.returncode
        print("OK launch_gdb_smoke")
        return 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
