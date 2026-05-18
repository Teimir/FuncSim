"""GDB RSP stub unit tests (in-process, no TCP)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from cli.debug_common import create_debug_controller, load_initial_image
from cli.gdb.rsp import read_packet_from_stream
from cli.gdb.stub import GdbStub
from core.memory import Memory

ROOT = Path(__file__).resolve().parents[2]


def _args(**kw):
    defaults = {
        "hex": ROOT / "examples" / "smoke.hex",
        "bin": None,
        "core": "full",
        "mmio": False,
        "mmio_base": 0xFFFF_0000,
        "sd_image": None,
        "sd_create_sectors": None,
        "sd_spi": False,
        "load_addr": 0,
    }
    defaults.update(kw)
    return type("Args", (), defaults)()


def _parse_reply(stub: GdbStub, packet: str) -> str:
    out = BytesIO()
    assert stub.handle_packet(out, packet)
    raw = out.getvalue()
    idx = 0

    def rb():
        nonlocal idx
        if idx >= len(raw):
            return b""
        b = raw[idx : idx + 1]
        idx += 1
        return b

    return read_packet_from_stream(rb) or ""


def test_stop_reason_and_read_registers() -> None:
    ram = Memory()
    ctrl = create_debug_controller(ram, _args())
    load_initial_image(ctrl, _args())
    stub = GdbStub(ctrl)
    assert _parse_reply(stub, "?").startswith("S")
    gregs = _parse_reply(stub, "g")
    assert len(gregs) == 37 * 8
    r2 = int.from_bytes(bytes.fromhex(gregs[16:24]), "little")
    assert r2 == 0


def test_step_updates_register() -> None:
    ram = Memory()
    ctrl = create_debug_controller(ram, _args())
    load_initial_image(ctrl, _args())
    stub = GdbStub(ctrl)
    _parse_reply(stub, "s")
    gregs = _parse_reply(stub, "g")
    r2 = int.from_bytes(bytes.fromhex(gregs[16:24]), "little")
    assert r2 == 10


def test_memory_read() -> None:
    ram = Memory()
    ctrl = create_debug_controller(ram, _args())
    load_initial_image(ctrl, _args())
    stub = GdbStub(ctrl)
    mem = _parse_reply(stub, "m0,4")
    assert len(mem) == 8
    w = int.from_bytes(bytes.fromhex(mem), "little")
    assert w == 0xC020100A


def test_breakpoint_packet() -> None:
    ram = Memory()
    ctrl = create_debug_controller(ram, _args())
    stub = GdbStub(ctrl)
    assert _parse_reply(stub, "Z1,8,0") == "OK"
    assert 8 in ctrl.runner.break_pcs
