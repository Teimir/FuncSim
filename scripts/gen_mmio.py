#!/usr/bin/env python3
"""Generate mmio_generated.svh, mmio_sd_regs.svh, mmio_constants.py from docs/isa/mmio_map.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "docs" / "isa" / "mmio_map.yaml"
SVH_OUT = ROOT / "test" / "src" / "mmio_generated.svh"
SD_REGS_SVH = ROOT / "test" / "src" / "mmio_sd_regs.svh"
PY_OUT = ROOT / "src" / "core" / "mmio_constants.py"
SD_REGS_PY = ROOT / "src" / "core" / "mmio_sd_regs.py"

HEADER_SVH = """// GENERATED FILE — do not edit by hand.
// Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py
// Included from RTL as: `include "mmio_generated.svh" (add -Itest/src to iverilog)

"""
HEADER_PY = '''"""GENERATED FILE — do not edit by hand."""
# Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py

from __future__ import annotations

'''


def _u32(x: int) -> int:
    return x & 0xFFFFFFFF


def _hex_py(n: int) -> str:
    if n >= 0x10:
        return hex(n)
    return repr(n)


def _emit_sd_regs_svh(sd_modes: dict) -> str:
    lines = [
        HEADER_SVH.rstrip() + "\n\n",
        "`ifndef E32C_MMIO_SD_REGS_SVH\n",
        "`define E32C_MMIO_SD_REGS_SVH\n\n",
    ]
    for mode_name, mode in sd_modes.items():
        prefix = "SD_BLOCK" if mode_name == "block" else "SD_SPI"
        lines.append(f"// SD {mode_name} mode @ +0x3000\n")
        for reg in mode.get("registers", []):
            name = reg["name"].upper()
            off = int(reg["offset"])
            word_ix = off // 4
            lines.append(f"`define E32C_{prefix}_REG_{name} 5'h{word_ix:x}\n")
        if mode_name == "block":
            lines.append(f"`define E32C_{prefix}_DATA_BYTES 512\n")
        lines.append("\n")
    lines.append("`endif // E32C_MMIO_SD_REGS_SVH\n")
    return "".join(lines)


def _emit_sd_regs_py(sd_modes: dict) -> str:
    lines = [HEADER_PY, "# SD MMIO register offsets (relative to SD_OFFSET)\n\n"]
    for mode_name, mode in sd_modes.items():
        cls = "SdBlockRegs" if mode_name == "block" else "SdSpiRegs"
        lines.append(f"class {cls}:\n")
        for reg in mode.get("registers", []):
            name = reg["name"].upper()
            off = int(reg["offset"])
            lines.append(f"    REG_{name} = {_hex_py(off)}\n")
        if mode_name == "block":
            lines.append(f"    DATA_BASE = REG_DATA\n")
            lines.append(f"    REGION_SIZE = {_hex_py(int(mode['python_region_bytes']))}\n")
        else:
            lines.append(f"    REGION_SIZE = {_hex_py(int(mode['python_region_bytes']))}\n")
        lines.append("\n\n")
    lines.append('__all__ = ["SdBlockRegs", "SdSpiRegs"]\n')
    return "".join(lines)


def main() -> int:
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    mmio_base = _u32(int(data["mmio_base"]))
    window = _u32(int(data["window_size"]))
    axi_high = (mmio_base >> 16) & 0xFFFF
    devices: dict = data["devices"]

    order = ["gpio", "uart", "timer", "sd"]
    for k in order:
        if k not in devices:
            print(f"gen_mmio: missing device {k!r} in mmio_map.yaml", file=sys.stderr)
            return 1

    rtl_names = {"gpio": "GPIO", "uart": "UART", "timer": "TIMER", "sd": "SD_SPI"}
    py_prefix = {"gpio": "GPIO", "uart": "UART", "timer": "TIMER", "sd": "SD"}

    svh = [
        HEADER_SVH.rstrip() + "\n\n",
        "`ifndef E32C_MMIO_GENERATED_SVH\n",
        "`define E32C_MMIO_GENERATED_SVH\n\n",
        f"`define E32C_MMIO_BASE 32'h{mmio_base:08x}\n",
        f"`define E32C_MMIO_AXI_HIGH 16'h{axi_high:04x}\n\n",
    ]

    for key in order:
        ent = devices[key]
        off = _u32(int(ent["offset"]))
        full = _u32(mmio_base + off)
        rtl = rtl_names[key]
        page = (full >> 12) & ((1 << 20) - 1)
        svh.append(f"// {rtl}: full 32-bit base + 4 KiB decode page (paddr[31:12])\n")
        svh.append(f"`define E32C_{rtl}_BASE 32'h{full:08x}\n")
        svh.append(f"`define E32C_{rtl}_PAGE 20'h{page:x}\n\n")

    svh.append("`endif // E32C_MMIO_GENERATED_SVH\n")

    sd_ent = devices["sd"]
    sd_modes = sd_ent.get("modes", {})
    block_bytes = int(sd_modes.get("block", {}).get("python_region_bytes", 0x210))
    spi_bytes = int(sd_modes.get("spi", {}).get("python_region_bytes", 0x28))
    sd_region = max(block_bytes, spi_bytes)

    py_lines = [
        HEADER_PY,
        f"MMIO_BASE_DEFAULT = {_hex_py(mmio_base)}\n",
        f"MMIO_WINDOW_SIZE = {_hex_py(window)}\n",
        "\n",
    ]

    for key in order:
        ent = devices[key]
        off = _u32(int(ent["offset"]))
        if key == "sd":
            rsz = sd_region
        else:
            rsz = int(ent["python_region_bytes"])
        pfx = py_prefix[key]
        py_lines.append(f"{pfx}_OFFSET = {_hex_py(off)}\n")
        py_lines.append(f"{pfx}_REGION_SIZE = {_hex_py(rsz)}\n")

    py_lines.extend(
        [
            "\n__all__ = [\n",
            '    "MMIO_BASE_DEFAULT",\n',
            '    "MMIO_WINDOW_SIZE",\n',
            '    "GPIO_OFFSET",\n',
            '    "GPIO_REGION_SIZE",\n',
            '    "UART_OFFSET",\n',
            '    "UART_REGION_SIZE",\n',
            '    "TIMER_OFFSET",\n',
            '    "TIMER_REGION_SIZE",\n',
            '    "SD_OFFSET",\n',
            '    "SD_REGION_SIZE",\n',
            "]\n",
        ]
    )

    SVH_OUT.write_text("".join(svh), encoding="utf-8", newline="\n")
    SD_REGS_SVH.write_text(_emit_sd_regs_svh(sd_modes), encoding="utf-8", newline="\n")
    PY_OUT.write_text("".join(py_lines), encoding="utf-8", newline="\n")
    SD_REGS_PY.write_text(_emit_sd_regs_py(sd_modes), encoding="utf-8", newline="\n")
    print(f"Wrote {SVH_OUT.relative_to(ROOT)}")
    print(f"Wrote {SD_REGS_SVH.relative_to(ROOT)}")
    print(f"Wrote {PY_OUT.relative_to(ROOT)}")
    print(f"Wrote {SD_REGS_PY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
