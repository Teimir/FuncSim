#!/usr/bin/env python3
"""Run full repository verification (Python + RTL)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    label = " ".join(cmd)
    print(f"\n==> {label}")
    r = subprocess.run(cmd, cwd=cwd or ROOT, check=False)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def run_vvp_expect(pass_marker: str, out_vvp: str, *, cwd: Path | None = None) -> None:
    label = f"vvp {out_vvp} (expect {pass_marker})"
    print(f"\n==> {label}")
    r = subprocess.run(
        ["vvp", out_vvp],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if pass_marker not in (r.stdout or ""):
        print(r.stdout or "", file=sys.stderr)
        print(r.stderr or "", file=sys.stderr)
        raise SystemExit(r.returncode or 1)


def _require_iverilog() -> None:
    r = subprocess.run(["iverilog", "-V"], capture_output=True, text=True, check=False)
    if r.returncode != 0:
        print("iverilog not found; install Icarus Verilog for RTL steps", file=sys.stderr)
        raise SystemExit(1)


def main() -> int:
    p = argparse.ArgumentParser(description="E32C full verification")
    p.add_argument(
        "--quick",
        action="store_true",
        help="PR-tier: pytest (excl. slow), RTL smoke, compare_rtl without --full",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="Nightly-tier: all pytest, extended RTL, compare_rtl --full",
    )
    p.add_argument(
        "--coverage",
        action="store_true",
        help="Run pytest with coverage (quick: core only; full: same)",
    )
    args = p.parse_args()
    if args.quick and args.full:
        print("use either --quick or --full, not both", file=sys.stderr)
        return 2
    full = bool(args.full)

    run([sys.executable, "scripts/gen_mmio.py"])
    run(["git", "diff", "--exit-code", "test/src/mmio_generated.svh", "src/core/mmio_constants.py"])
    run(["ruff", "check", "src", "tests", "examples"])

    pytest_cmd = [sys.executable, "-m", "pytest", "-q"]
    if not full:
        pytest_cmd.extend(["-m", "not slow"])
    if args.coverage:
        pytest_cmd.extend(["--cov=core", "--cov-report=term-missing", "--cov-fail-under=85"])
    run(pytest_cmd)

    equiv_cmd = [sys.executable, "-m", "test.equiv", "--all"]
    run(equiv_cmd)

    _require_iverilog()

    rtl: list[tuple[str, str, str, bool]] = [
        ("tb_ram", "test/out_tb_ram.vvp", "test/src/tb_ram.sv test/src/ram.sv", False),
        ("tb_icache", "test/out_tb_icache.vvp", "test/src/tb_icache.sv test/src/icache.sv", False),
        (
            "tb_axi_apb_uart",
            "test/out_tb_axi_apb_uart.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_axi_apb_uart.sv",
            True,
        ),
        (
            "tb_uart_loopback",
            "test/out_tb_uart_loopback.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_uart_loopback.sv",
            True,
        ),
        (
            "tb_psram_boot",
            "test/out_tb_psram_boot.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_psram_boot.sv",
            True,
        ),
        (
            "tb_boot_smoke",
            "test/out_tb_boot_smoke.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_boot_smoke.sv",
            True,
        ),
        (
            "tb_core_irq",
            "test/out_tb_core_irq.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_core_irq.sv",
            True,
        ),
        (
            "tb_core_isa",
            "test/out_tb_core_isa.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_core_isa.sv",
            full,
        ),
        (
            "tb_soc_longrun",
            "test/out_tb_soc_longrun.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_soc_longrun.sv",
            full,
        ),
        (
            "tb_irq_flow",
            "test/out_tb_irq_flow.vvp",
            "test/src/tb_irq_flow.sv test/src/csr_irq.sv",
            full,
        ),
        (
            "tb_timer_gpio",
            "test/out_tb_timer_gpio.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_timer_gpio.sv",
            full,
        ),
        (
            "tb_sd_spi",
            "test/out_tb_sd_spi.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_sd_spi.sv",
            True,
        ),
        (
            "tb_sd_spi_protocol",
            "test/out_tb_sd_spi_protocol.vvp",
            "-f test/iverilog_soc_psram.f test/src/tb_sd_spi_protocol.sv",
            True,
        ),
    ]

    for name, out_vvp, srcs, psram_cwd in rtl:
        if not full and name in {
            "tb_core_isa",
            "tb_soc_longrun",
            "tb_irq_flow",
            "tb_timer_gpio",
        }:
            continue
        iverilog_cmd = ["iverilog", "-g2012", "-o", out_vvp]
        if srcs.startswith("-f"):
            iverilog_cmd.extend(srcs.split())
        else:
            iverilog_cmd.extend(srcs.split())
        run(iverilog_cmd)
        vvp_path = out_vvp
        pass_marker = f"{name} PASS"
        if psram_cwd:
            run_vvp_expect(pass_marker, f"../{Path(out_vvp).name}", cwd=ROOT / "test" / "src")
        else:
            run_vvp_expect(pass_marker, str(ROOT / out_vvp))

    cosim_cmd = [sys.executable, "test/compare_rtl_python.py"]
    if full:
        cosim_cmd.append("--full")
    run(cosim_cmd)

    print("\nverify_all: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
