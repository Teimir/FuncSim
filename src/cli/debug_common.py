"""Shared CLI helpers for debugger entry points (REPL and GUI)."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.bus import MMIO_BASE_DEFAULT, SystemBus
from core.debug_controller import DebugController
from core.loader import load_binary, load_words, words_from_hex_lines
from core.memory import Memory
from core.peripherals.uart import Uart


def add_sim_session_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--load-addr", type=lambda x: int(x, 0), default=0)
    parser.add_argument("--hex", type=Path, help="Hex words file")
    parser.add_argument("--bin", type=Path, help="Binary image")
    parser.add_argument("--mmio", action="store_true", help="SystemBus with GPIO/UART/Timer/SD")
    parser.add_argument("--mmio-base", type=lambda x: int(x, 0), default=MMIO_BASE_DEFAULT)
    parser.add_argument(
        "--sd-image",
        type=Path,
        default=None,
        help="SD image file (implies MMIO / SystemBus)",
    )
    parser.add_argument(
        "--sd-create-sectors",
        type=int,
        default=None,
        help="With --sd-image: create/truncate image with N sectors (512 bytes each)",
    )


def use_mmio_from_args(args: argparse.Namespace) -> bool:
    return bool(args.mmio or args.sd_image is not None)


def build_repl_memory(args: argparse.Namespace) -> tuple[Memory, Memory | SystemBus]:
    """Backing RAM and execution memory view (plain RAM or SystemBus)."""
    ram = Memory()
    if use_mmio_from_args(args):
        uart = Uart()
        mem: Memory | SystemBus = SystemBus(
            ram,
            mmio_base=args.mmio_base,
            uart=uart,
            sd_image=args.sd_image,
            sd_create_sectors=args.sd_create_sectors,
        )
    else:
        mem = ram
    return ram, mem


def load_program_into_memory(mem: Memory | SystemBus, load_addr: int, args: argparse.Namespace) -> None:
    if args.bin:
        load_binary(mem, load_addr, args.bin)
    elif args.hex:
        ws = words_from_hex_lines(args.hex.read_text(encoding="utf-8"))
        load_words(mem, load_addr, ws)
    else:
        raise ValueError("no program source")


def create_debug_controller(ram: Memory, args: argparse.Namespace) -> DebugController:
    return DebugController.create(
        ram=ram,
        use_mmio=use_mmio_from_args(args),
        mmio_base=args.mmio_base,
        load_addr=args.load_addr,
        sd_image=args.sd_image,
        sd_create_sectors=args.sd_create_sectors,
    )


def load_initial_image(ctrl: DebugController, args: argparse.Namespace) -> None:
    if args.bin:
        ctrl.load_binary_file(args.bin)
        ctrl.reset_cpu(preserve_breakpoints=True)
    elif args.hex:
        ctrl.load_hex_file(args.hex)
        ctrl.reset_cpu(preserve_breakpoints=True)
