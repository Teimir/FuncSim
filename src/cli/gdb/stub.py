"""GDB stub session over one connected stream (TCP socket file object)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import BinaryIO

from cli.gdb import registers as reg
from cli.gdb.rsp import RSP_ACK, encode_packet, read_packet_from_stream
from core.debug_controller import DebugController, StepKind

_FEATURES_PATH = Path(__file__).resolve().parents[3] / "docs" / "gdb" / "e32c.xml"


class GdbStub:
    def __init__(self, ctrl: DebugController) -> None:
        self.ctrl = ctrl
        self._stop_reason = "S05"  # SIGTRAP
        self._attached = True

    def _reply(self, stream: BinaryIO, payload: str) -> None:
        stream.write(encode_packet(payload))
        stream.flush()

    def handle_packet(self, stream: BinaryIO, packet: str) -> bool:
        """Handle one RSP packet. Return False to close connection."""
        if packet == "?":
            self._reply(stream, self._stop_reason)
            return True
        if packet == "g":
            self._reply(stream, reg.read_all_g_packet(self.ctrl))
            return True
        if packet.startswith("G"):
            ok = reg.write_all_g_packet(self.ctrl, packet[1:])
            self._reply(stream, "OK" if ok else "E01")
            return True
        if packet.startswith("p"):
            m = re.fullmatch(r"p([0-9a-fA-F]+)(?:;thread:[0-9a-fA-F]+)?", packet)
            if not m:
                self._reply(stream, "E01")
                return True
            rno = int(m.group(1), 16)
            self._reply(stream, reg.reg_to_bytes(self.ctrl, rno).hex())
            return True
        if packet.startswith("P"):
            m = re.fullmatch(r"P([0-9a-fA-F]+)=([0-9a-fA-F]+)", packet)
            if not m:
                self._reply(stream, "E01")
                return True
            rno = int(m.group(1), 16)
            reg.bytes_to_reg(self.ctrl, rno, bytes.fromhex(m.group(2)))
            self._reply(stream, "OK")
            return True
        if packet.startswith("m"):
            m = re.fullmatch(r"m([0-9a-fA-F]+),([0-9a-fA-F]+)", packet)
            if not m:
                self._reply(stream, "E01")
                return True
            addr = int(m.group(1), 16)
            length = int(m.group(2), 16)
            self._reply(stream, self._read_mem_hex(addr, length))
            return True
        if packet.startswith("M"):
            m = re.fullmatch(r"M([0-9a-fA-F]+),([0-9a-fA-F]+):([0-9a-fA-F]*)", packet)
            if not m:
                self._reply(stream, "E01")
                return True
            addr = int(m.group(1), 16)
            length = int(m.group(2), 16)
            data = bytes.fromhex(m.group(3))
            if not self._write_mem(addr, data[:length]):
                self._reply(stream, "E03")
                return True
            self._reply(stream, "OK")
            return True
        if packet == "c" or packet.startswith("c;"):
            self._continue(stream)
            return True
        if packet == "s" or packet.startswith("s;"):
            self._step(stream)
            return True
        if packet.startswith("Z") or packet.startswith("z"):
            return self._handle_breakpoint(stream, packet)
        if packet == "k" or packet.startswith("k"):
            return False
        if packet.startswith("qSupported"):
            self._reply(stream, "PacketSize=1024;qXfer:features:read+")
            return True
        if packet.startswith("qXfer:features:read"):
            self._reply(stream, self._qxfer_features(packet))
            return True
        if packet.startswith("qfThreadInfo") or packet.startswith("qsThreadInfo"):
            self._reply(stream, "l")
            return True
        if packet == "Hg0" or packet.startswith("Hc"):
            self._reply(stream, "OK")
            return True
        if packet == "qAttached":
            self._reply(stream, "1")
            return True
        if packet.startswith("qC") or packet.startswith("qOffsets"):
            self._reply(stream, "")
            return True
        if packet == "":
            return True
        self._reply(stream, "")
        return True

    def _qxfer_features(self, packet: str) -> str:
        if not _FEATURES_PATH.is_file():
            return "l"
        text = _FEATURES_PATH.read_text(encoding="utf-8")
        offset = 0
        length = len(text)
        parts = packet.split(":")
        if len(parts) >= 4 and "," in parts[3]:
            try:
                off_s, len_s = parts[3].split(",", 1)
                offset = int(off_s, 16)
                length = int(len_s, 16)
            except ValueError:
                pass
        chunk = text[offset : offset + length]
        if offset + len(chunk) >= len(text):
            return "l" + chunk
        return "m" + chunk

    def _read_mem_hex(self, addr: int, length: int) -> str:
        mem = self.ctrl.mem
        out = bytearray()
        i = 0
        while i < length:
            if length - i >= 4 and addr % 4 == 0:
                try:
                    w = mem.read_word(addr)
                    out.extend(w.to_bytes(4, "little"))
                    addr += 4
                    i += 4
                    continue
                except Exception:
                    pass
            try:
                base = addr & ~3
                shift = (addr & 3) * 8
                w = mem.read_word(base)
                out.append((w >> shift) & 0xFF)
            except Exception:
                out.append(0)
            addr += 1
            i += 1
        return out.hex()

    def _write_mem(self, addr: int, data: bytes) -> bool:
        mem = self.ctrl.mem
        try:
            if addr % 4 == 0 and len(data) % 4 == 0:
                for i in range(0, len(data), 4):
                    w = int.from_bytes(data[i : i + 4], "little")
                    mem.write_word(addr + i, w)
                return True
            for i, b in enumerate(data):
                a = addr + i
                base = a & ~3
                shift = (a & 3) * 8
                try:
                    w = mem.read_word(base)
                except Exception:
                    w = 0
                mask = 0xFF << shift
                w = (w & ~mask) | ((b & 0xFF) << shift)
                mem.write_word(base, w)
            return True
        except Exception:
            return False

    def _step(self, stream: BinaryIO) -> None:
        if self.ctrl.state.halted:
            self._stop_reason = "S05"
            self._reply(stream, self._stop_reason)
            return
        r = self.ctrl.step()
        self._set_stop_from_result(r.kind)
        self._reply(stream, self._stop_reason)

    def _continue(self, stream: BinaryIO) -> None:
        if self.ctrl.state.halted:
            self._stop_reason = "S05"
            self._reply(stream, self._stop_reason)
            return
        while not self.ctrl.state.halted:
            r = self.ctrl.step()
            if r.kind != StepKind.OK:
                self._set_stop_from_result(r.kind)
                self._reply(stream, self._stop_reason)
                return
        self._stop_reason = "S05"
        self._reply(stream, self._stop_reason)

    def _set_stop_from_result(self, kind: StepKind) -> None:
        if kind == StepKind.ERROR:
            self._stop_reason = "S06"
        else:
            self._stop_reason = "S05"

    def _handle_breakpoint(self, stream: BinaryIO, packet: str) -> bool:
        m = re.fullmatch(r"([Zz])([0-9]),([0-9a-fA-F]+),([0-9a-fA-F]+)", packet)
        if not m or m.group(2) != "1":
            self._reply(stream, "")
            return True
        addr = int(m.group(3), 16)
        if m.group(1) == "Z":
            self.ctrl.runner.break_pcs.add(addr)
            self._reply(stream, "OK")
        else:
            self.ctrl.runner.break_pcs.discard(addr)
            self._reply(stream, "OK")
        return True

    def serve(self, stream: BinaryIO) -> None:
        while self._attached:
            pkt = read_packet_from_stream(stream.read)
            if pkt is None:
                break
            stream.write(RSP_ACK)
            stream.flush()
            if not self.handle_packet(stream, pkt):
                break
