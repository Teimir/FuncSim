#!/usr/bin/env python3
"""Build Tang Nano 9K firmware (firmware_b*.hex + firmware_rom.svh)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "gen_firmware_hex.py"
OUT = ROOT / "test" / "src"


def main() -> int:
    p = argparse.ArgumentParser(description="Regenerate TN9K BSRAM boot image")
    p.add_argument(
        "--profile",
        choices=("irq", "blink", "hello", "beacon", "smoke", "sd_spi", "demo"),
        default="blink",
        help="blink: BL\\n; irq: timer IRQ; hello: Hi!; smoke: GPIO; sd_spi: CMD0+OK; demo: UART+timer+SD",
    )
    p.add_argument(
        "--install-baseline",
        action="store_true",
        help="after hello build, copy firmware_* into test/tn9k/baseline/",
    )
    args = p.parse_args()

    if args.profile == "irq":
        cmd = [
            sys.executable,
            str(GEN),
            "--asm",
            str(ROOT / "examples" / "blink_uart_irq_main.asm"),
            "--handler",
            str(ROOT / "examples" / "blink_uart_irq_handler.asm"),
            "--handler-addr",
            "0x100",
            "--words",
            "256",
            "--skip-fetch-rom",
            "--out-dir",
            str(OUT),
        ]
    elif args.profile == "blink":
        cmd = [
            sys.executable,
            str(GEN),
            "--asm",
            str(ROOT / "examples" / "blink_uart.asm"),
            "--words",
            "512",
            "--skip-fetch-rom",
            "--out-dir",
            str(OUT),
        ]
    elif args.profile == "hello":
        cmd = [
            sys.executable,
            str(GEN),
            "--asm",
            str(ROOT / "examples" / "tn9k_uart_hello.asm"),
            "--words",
            "128",
            "--skip-fetch-rom",
            "--out-dir",
            str(OUT),
        ]
    elif args.profile == "beacon":
        cmd = [
            sys.executable,
            str(GEN),
            "--asm",
            str(ROOT / "examples" / "tn9k_uart_beacon.asm"),
            "--words",
            "64",
            "--skip-fetch-rom",
            "--out-dir",
            str(OUT),
        ]
    elif args.profile == "sd_spi":
        cmd = [
            sys.executable,
            str(GEN),
            "--asm",
            str(ROOT / "examples" / "tn9k_sd_spi_uart.asm"),
            "--words",
            "256",
            "--skip-fetch-rom",
            "--out-dir",
            str(OUT),
        ]
    elif args.profile == "demo":
        demo_main = ROOT / "examples" / "_tn9k_demo_fpga_main.asm"
        demo_src = (ROOT / "examples" / "tn9k_demo_uart_timer_sd_main.asm").read_text(
            encoding="utf-8"
        )
        demo_src = demo_src.replace(
            "MOV 10 2000\nSTR 24 10 15 8\nMOV 10 0",
            "MOV 10 640\nSTR 24 10 15 8\nMOV 10 410",
            1,
        )
        demo_main.write_text(demo_src, encoding="utf-8")
        cmd = [
            sys.executable,
            str(GEN),
            "--asm",
            str(demo_main),
            "--handler",
            str(ROOT / "examples" / "tn9k_demo_uart_timer_sd_handler.asm"),
            "--handler-addr",
            "0x200",
            "--words",
            "768",
            "--skip-fetch-rom",
            "--out-dir",
            str(OUT),
        ]
    else:
        cmd = [
            sys.executable,
            str(GEN),
            "--asm",
            str(ROOT / "examples" / "boot_smoke.asm"),
            "--words",
            "256",
            "--skip-fetch-rom",
            "--out-dir",
            str(OUT),
        ]

    print(" ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

    for stale in OUT.glob("firmware_store_b*.hex"):
        stale.unlink()
        print(f"removed stale {stale.name}")

    if args.install_baseline:
        if args.profile != "hello":
            print("warning: --install-baseline is intended for --profile hello", file=sys.stderr)
        baseline = ROOT / "test" / "tn9k" / "baseline"
        baseline.mkdir(parents=True, exist_ok=True)
        for name in (
            "firmware_rom.svh",
            "firmware_b0.hex",
            "firmware_b1.hex",
            "firmware_b2.hex",
            "firmware_b3.hex",
        ):
            src = OUT / name
            shutil.copy2(src, baseline / name)
            print(f"baseline: {baseline / name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
