"""Populate widgets from controller snapshots."""

from __future__ import annotations

import time
import tkinter as tk
from typing import Any

from core.bus import SystemBus
from core.debug_controller import ListingLine, MmioSnapshot, UiSnapshot
from core.trace import StepTrace


class SnapshotFillMixin:
    _ctrl: Any
    _status: Any
    _var_status_mode: Any
    _perf_last_ts: float
    _perf_last_instr: int
    _perf_last_cycles: int
    _perf_active_dt: float
    _perf_active_instr: int
    _pending_status: str | None
    _tip_override: str | None

    def _fmt_rate(self, value: float) -> str:
        if value >= 1_000_000.0:
            return f"{value / 1_000_000.0:.2f}M"
        if value >= 1_000.0:
            return f"{value / 1_000.0:.2f}k"
        return f"{value:.0f}"

    def _fmt_fetch(self, s: UiSnapshot) -> str:
        if s.fetch_word is None:
            return f"0x{s.fetch_addr:08x}: <{s.fetch_disasm}>"
        return f"0x{s.fetch_addr:08x}: 0x{s.fetch_word:08x}  {s.fetch_disasm}"

    def _fill_regs(self, s: UiSnapshot) -> None:
        for x in self._tv_regs.get_children():
            self._tv_regs.delete(x)
        for i in range(32):
            label = f"R{i}" + (" (PC)" if i == 31 else "")
            self._tv_regs.insert("", tk.END, values=(label, f"0x{s.regs[i]:08x}"))

    def _fill_flags(self, s: UiSnapshot) -> None:
        self._var_flags_hex.set(f"0x{s.flags:08x}")
        self._flag_vars["IE"].set(s.flag_ie)
        self._flag_vars["Z"].set(s.flag_z)
        self._flag_vars["C"].set(s.flag_c)
        self._flag_vars["V"].set(s.flag_v)
        self._flag_vars["S"].set(s.flag_s)

    def _fill_spr(self, s: UiSnapshot) -> None:
        for x in self._tv_spr.get_children():
            self._tv_spr.delete(x)
        for idx, val, name in s.spr_rows:
            self._tv_spr.insert("", tk.END, values=(idx, f"0x{val:08x}", name or ""))

    def _fill_listing(self, lines: list[ListingLine]) -> None:
        for x in self._tv_list.get_children():
            self._tv_list.delete(x)
        for ln in lines:
            mk = ""
            if ln.is_pc:
                mk = "=>"
            elif ln.is_breakpoint:
                mk = "●"
            w = "" if ln.word is None else f"0x{ln.word:08x}"
            tags: tuple[str, ...] = ()
            if ln.is_pc:
                tags = ("pc",)
            elif ln.is_breakpoint:
                tags = ("bp",)
            self._tv_list.insert("", tk.END, values=(f"0x{ln.addr:08x}", w, ln.disasm, mk), tags=tags)

    def _fill_mem(self, rows: list[tuple[int, list[int | None]]]) -> None:
        for x in self._tv_mem.get_children():
            self._tv_mem.delete(x)
        for addr, words in rows:
            vals = [f"0x{addr:08x}"]
            for w in words:
                vals.append("—" if w is None else f"0x{w:08x}")
            self._tv_mem.insert("", tk.END, values=tuple(vals))

    def _fill_mmio(self, mm: MmioSnapshot | None) -> None:
        self._mmio_text.configure(state=tk.NORMAL)
        self._mmio_text.delete("1.0", tk.END)
        if mm is None:
            self._mmio_text.insert(tk.END, "MMIO not in use (start with --mmio).\n")
        else:
            t = self._ctrl.mem
            assert isinstance(t, SystemBus)
            lines = [
                f"MMIO base: 0x{mm.mmio_base:08x}",
                "",
                f"GPIO @ 0x{mm.mmio_base + 0:08x}  out = 0x{mm.gpio_out:08x}",
                "",
                f"UART @ 0x{mm.mmio_base + 0x1000:08x}",
                f"  STATUS = 0x{mm.uart_status:02x}  (RX queued: {mm.uart_rx_queue_len})",
                f"  TX last bytes (hex): {mm.uart_tx_hex or '(empty)'}",
                f"  TX ASCII: {mm.uart_tx_ascii!r}",
                "",
                f"Timer @ 0x{mm.mmio_base + 0x2000:08x}",
                f"  counter = 0x{mm.timer_counter_hi:08x}{mm.timer_counter_lo:08x}",
                f"  compare = 0x{mm.timer_compare_hi:08x}{mm.timer_compare_lo:08x}",
                f"  ctrl    = 0x{mm.timer_ctrl:08x}",
                "",
                f"SD / block @ 0x{mm.mmio_base + 0x3000:08x}",
                f"  path: {mm.sd.path or '(none)'}  mounted={mm.sd.mounted}",
                f"  LBA=0x{mm.sd.lba:08x}  STATUS=0x{mm.sd.status:04x}  err={mm.sd.err_code}  sectors={mm.sd.sectors}",
                f"  buf[0..15]: {mm.sd.buffer_preview}",
                "",
            ]
            self._mmio_text.insert(tk.END, "\n".join(lines))
        self._mmio_text.configure(state=tk.DISABLED)

    def _fill_storage(self, mm: MmioSnapshot | None) -> None:
        self._sd_info.configure(state=tk.NORMAL)
        self._sd_info.delete("1.0", tk.END)
        if mm is None:
            self._sd_info.insert(tk.END, "No MMIO — use --mmio to enable GPIO/UART/Timer/SD.\n")
        else:
            sd = mm.sd
            lines = [
                f"path: {sd.path or '(none)'}",
                f"mounted: {sd.mounted}",
                f"LBA register: 0x{sd.lba:08x}",
                f"STATUS word: 0x{sd.status:04x}  error code: {sd.err_code}",
                f"sectors (file): {sd.sectors}",
                f"sector buffer preview (first 16 bytes, hex): {sd.buffer_preview}",
                "",
                "Mount replaces the current backing file; Unmount closes it.",
                "See docs/mmio.md for CTRL (1=read sector, 2=write, 3=flush) and DATA aperture.",
            ]
            self._sd_info.insert(tk.END, "\n".join(lines))
        self._sd_info.configure(state=tk.DISABLED)

    def _fill_trace(self, trace: list[object]) -> None:
        for x in self._tv_trace.get_children():
            self._tv_trace.delete(x)
        for i, tr in enumerate(trace):
            assert isinstance(tr, StepTrace)
            self._tv_trace.insert(
                "",
                tk.END,
                values=(
                    i,
                    f"0x{tr.pc:08x}",
                    f"0x{tr.word:08x}",
                    tr.disasm,
                    tr.cycles_after,
                    "Y" if tr.halted_after else "",
                ),
            )

    def refresh(self, *, full: bool = True) -> None:
        snap = self._ctrl.snapshot()
        self._fill_regs(snap)
        self._fill_flags(snap)
        self._fill_spr(snap)
        self._var_fetch.set(self._fmt_fetch(snap))
        self._fill_listing(snap.listing)
        self._fill_mem(snap.memory_rows)
        if full:
            self._fill_mmio(snap.mmio)
            self._fill_trace(snap.trace)
        self._fill_storage(snap.mmio)
        self._refresh_bp_list()
        self._var_page.set(hex(self._ctrl.mem_page_base))
        parts = [
            f"instr={snap.instruction_count}",
            f"cyc={snap.cycles}",
            f"halt={'Y' if snap.halted else 'N'}",
        ]
        now = time.perf_counter()
        dt = max(0.0, now - self._perf_last_ts)
        dinstr = max(0, snap.instruction_count - self._perf_last_instr)
        dcycles = max(0, snap.cycles - self._perf_last_cycles)
        burst_ips = (dinstr / dt) if dt > 1e-9 else 0.0
        burst_cps = (dcycles / dt) if dt > 1e-9 else 0.0
        if dinstr > 0 and dt > 1e-9:
            self._perf_active_dt += dt
            self._perf_active_instr += dinstr
        avg_ips = (self._perf_active_instr / self._perf_active_dt) if self._perf_active_dt > 1e-9 else 0.0
        avg_cps = (snap.cycles / self._perf_active_dt) if self._perf_active_dt > 1e-9 else 0.0
        run_state = "idle" if (dinstr == 0 and dcycles == 0) else "running"
        if self._var_status_mode.get() == "full":
            parts.extend(
                [
                    f"{run_state}",
                    f"ips(avg/burst)={self._fmt_rate(avg_ips)}/{self._fmt_rate(burst_ips)}",
                    f"cps(avg/burst)={self._fmt_rate(avg_cps)}/{self._fmt_rate(burst_cps)}",
                    f"ms={dt*1000.0:.1f}",
                ]
            )
        else:
            parts.extend(
                [
                    f"{run_state}",
                    f"ips(avg/burst)={self._fmt_rate(avg_ips)}/{self._fmt_rate(burst_ips)}",
                ]
            )
        self._perf_last_ts = now
        self._perf_last_instr = snap.instruction_count
        self._perf_last_cycles = snap.cycles
        if self._pending_status:
            parts.append(self._pending_status)
            self._pending_status = None
        if snap.last_error:
            parts.append(snap.last_error)
        line = "  |  ".join(parts)
        if self._tip_override:
            line = self._tip_override
        self._status.set(line)
