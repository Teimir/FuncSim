#!/usr/bin/env python3
"""Build smoke.elf and run GDB remote smoke test."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    gdb = shutil.which("gdb")
    if gdb is None:
        print("SKIP: gdb not in PATH")
        return 0

    with tempfile.TemporaryDirectory() as td:
        elf = Path(td) / "boot_smoke.elf"
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.ld",
                "-o",
                str(elf),
                f"{ROOT / 'examples' / 'boot_smoke.asm'}@0",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src")},
        )
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            return r.returncode

        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "cli.gdb_server",
                "--elf",
                str(elf),
                "--port",
                "3334",
            ],
            cwd=ROOT,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src")},
        )
        try:
            time.sleep(0.5)
            batch = subprocess.run(
                [
                    gdb,
                    "-batch",
                    "-ex",
                    "target remote 127.0.0.1:3334",
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
            print(batch.stdout)
            if batch.returncode != 0:
                print(batch.stderr, file=sys.stderr)
                return batch.returncode
            print("OK launch_gdb_elf")
            return 0
        finally:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
