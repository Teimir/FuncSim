"""Toolbar / menu actions, background run queue, UART and SD handlers."""

from __future__ import annotations

import json
import queue
import re
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import Any

from cli.uart_terminal import UartTerminalWindow
from core.bus import SystemBus
from core.debug_controller import StepKind, StepResult


class ActionsMixin:
    _ctrl: Any
    _run_queue: queue.Queue[object]
    _run_thread_active: bool
    _is_closing: bool
    _pending_status: str | None
    _auto_after_id: str | None
    _uart_win: UartTerminalWindow | None
    _var_auto: Any
    _var_auto_ms: Any
    _var_burst: Any
    _var_n: Any
    _var_max: Any
    _var_fast_refresh: Any
    _var_rx: Any
    _var_sd_path: Any
    _var_sd_sectors: Any
    _var_bp: Any
    _lb_bp: Any

    def _toggle_auto(self) -> None:
        if self._var_auto.get():
            self._start_auto()
        else:
            self._stop_auto()

    def _stop_auto(self) -> None:
        self._var_auto.set(False)
        if self._auto_after_id is not None:
            try:
                self.after_cancel(self._auto_after_id)
            except tk.TclError:
                pass
            self._auto_after_id = None

    def _start_auto(self) -> None:
        self._stop_auto()
        self._var_auto.set(True)
        try:
            ms = max(10, int(self._var_auto_ms.get().strip(), 0))
        except ValueError:
            messagebox.showerror("Auto", "Invalid interval (ms)", parent=self)
            self._var_auto.set(False)
            return
        self._var_auto_ms.set(str(ms))
        self._auto_tick()

    def _auto_tick(self) -> None:
        if not self._var_auto.get():
            return
        try:
            ms = max(10, int(self._var_auto_ms.get().strip(), 0))
        except ValueError:
            ms = 1000
        if self._ctrl.state.halted:
            self._stop_auto()
            self._pending_status = "Auto stopped: CPU halted"
            self.refresh()
            return
        try:
            burst = int(self._var_burst.get().strip(), 0)
        except ValueError:
            burst = 1
        burst = max(1, min(burst, 100_000))
        self._var_burst.set(str(burst))
        if burst <= 1:
            r = self._ctrl.step()
        else:
            r = self._ctrl.run_n(burst)
        self._apply_step_result(r)
        if r.kind in (StepKind.HALTED_ALREADY, StepKind.BREAKPOINT, StepKind.ERROR):
            self._stop_auto()
        full = not self._var_fast_refresh.get()
        self.refresh(full=full)
        if self._var_auto.get():
            self._auto_after_id = self.after(ms, self._auto_tick)

    def _open_uart_terminal(self) -> None:
        if not isinstance(self._ctrl.mem, SystemBus):
            messagebox.showinfo("UART", "Start the debugger with --mmio to use the UART terminal.", parent=self)
            return
        if self._uart_win is None or not self._uart_win.winfo_exists():
            self._uart_win = UartTerminalWindow(self, self._ctrl)

    def _export_snapshot(self) -> None:
        p = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not p:
            return
        data = self._ctrl.export_snapshot_dict()
        Path(p).write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._pending_status = f"Exported {p}"
        self.refresh()

    def _on_list_radius_apply(self) -> None:
        try:
            r = int(self._var_list_radius.get().strip(), 0)
        except ValueError:
            messagebox.showerror("Listing", "Invalid radius", parent=self)
            return
        self._ctrl.listing_radius = max(2, min(r, 128))
        self._var_list_radius.set(str(self._ctrl.listing_radius))
        self.refresh()

    def _on_reg_double(self, event: tk.Event[Any]) -> None:
        row = self._tv_regs.identify_row(event.y)
        if not row:
            return
        label, val_s = self._tv_regs.item(row, "values")
        m = re.search(r"R(\d+)", str(label))
        if not m:
            return
        ri = int(m.group(1))
        if ri == 0:
            messagebox.showinfo("Register", "R0 is always zero.", parent=self)
            return
        s = simpledialog.askstring(
            "Register",
            f"New value for {label} (hex, e.g. 0x1a2b3c4d)",
            initialvalue=str(val_s),
            parent=self,
        )
        if s is None:
            return
        try:
            v = self._parse_hex_int(s)
            self._ctrl.set_gpr(ri, v)
        except (ValueError, TypeError) as e:
            messagebox.showerror("Register", str(e), parent=self)
            return
        self._pending_status = f"Set {label} = 0x{v:08x}"
        self.refresh()

    def _on_mem_double(self, event: tk.Event[Any]) -> None:
        row = self._tv_mem.identify_row(event.y)
        col = self._tv_mem.identify_column(event.x)
        if not row:
            return
        vals = self._tv_mem.item(row, "values")
        if not vals:
            return
        base = int(str(vals[0]), 16)
        if col in ("", "#1"):
            messagebox.showinfo("Memory", "Double-click a word column (w0–w3), not the address.", parent=self)
            return
        try:
            col_i = int(col.replace("#", ""), 10)
        except ValueError:
            return
        wi = col_i - 2
        if not (0 <= wi < 4):
            return
        addr = (base + wi * 4) & 0xFFFFFFFF
        sz = self._ctrl.ram_size()
        if not (0 <= addr < sz):
            messagebox.showerror("Memory", "Not in RAM — edit only backing RAM words.", parent=self)
            return
        cur_s = str(vals[1 + wi])
        if cur_s == "—":
            messagebox.showerror("Memory", "Cannot edit unreadable cell.", parent=self)
            return
        s = simpledialog.askstring(
            "Memory",
            f"New word @ 0x{addr:08x} (hex)",
            initialvalue=cur_s,
            parent=self,
        )
        if s is None:
            return
        try:
            v = self._parse_hex_int(s)
            self._ctrl.write_ram_word(addr, v)
        except (ValueError, TypeError) as e:
            messagebox.showerror("Memory", str(e), parent=self)
            return
        self._pending_status = f"RAM[0x{addr:08x}] = 0x{v:08x}"
        self.refresh()

    def _on_list_rclick(self, event: tk.Event[Any]) -> None:
        row = self._tv_list.identify_row(event.y)
        if not row:
            return
        self._tv_list.selection_set(row)
        vals = self._tv_list.item(row, "values")
        if not vals:
            return
        try:
            a = int(str(vals[0]), 16)
        except ValueError:
            return
        if a % 4:
            return
        if a in self._ctrl.runner.break_pcs:
            self._ctrl.runner.break_pcs.discard(a)
            self._pending_status = f"Cleared bp 0x{a:08x}"
        else:
            self._ctrl.runner.break_pcs.add(a)
            self._pending_status = f"Set bp 0x{a:08x}"
        self.refresh()

    def _set_n_preset(self, value: str) -> None:
        self._var_n.set(value)

    def _set_max_preset(self, value: str) -> None:
        self._var_max.set(value)

    def _toggle_auto_hotkey(self) -> None:
        self._var_auto.set(not self._var_auto.get())
        self._toggle_auto()

    def _open_file(self) -> None:
        self._open_hex()

    def _open_binary(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("Binary", "*.bin"), ("All", "*.*")])
        if p:
            self._ctrl.load_binary_file(Path(p))
            self._ctrl.reset_cpu(preserve_breakpoints=True)
            self._pending_status = f"Loaded binary {p}"
            self.refresh()

    def _open_hex(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("Hex listing", "*.hex *.txt"), ("All", "*.*")])
        if p:
            self._ctrl.load_hex_file(Path(p))
            self._ctrl.reset_cpu(preserve_breakpoints=True)
            self._pending_status = f"Loaded hex {p}"
            self.refresh()

    def _parse_hex_int(self, s: str) -> int:
        s = s.strip().replace("_", "")
        if not s:
            raise ValueError("empty")
        return int(s, 16) if s.lower().startswith("0x") else int(s, 0)

    def _on_page_apply(self) -> None:
        try:
            a = self._parse_hex_int(self._var_page.get())
            self._ctrl.mem_page_base = a
        except ValueError:
            messagebox.showerror("Memory", "Invalid base address")
            return
        self.refresh()

    def _on_page_prev(self) -> None:
        step = self._ctrl.mem_page_lines * self._ctrl.mem_words_per_line * 4
        self._ctrl.mem_page_base = (self._ctrl.mem_page_base - step) & 0xFFFFFFFF
        self._var_page.set(hex(self._ctrl.mem_page_base))
        self.refresh()

    def _on_page_next(self) -> None:
        step = self._ctrl.mem_page_lines * self._ctrl.mem_words_per_line * 4
        self._ctrl.mem_page_base = (self._ctrl.mem_page_base + step) & 0xFFFFFFFF
        self._var_page.set(hex(self._ctrl.mem_page_base))
        self.refresh()

    def _on_sync_pc_page(self) -> None:
        pc = self._ctrl.state.pc
        self._ctrl.mem_page_base = pc - (pc % 4)
        self._var_page.set(hex(self._ctrl.mem_page_base))
        self.refresh()

    def _on_step(self) -> None:
        r = self._ctrl.step()
        self._apply_step_result(r)
        self.refresh()

    def _on_run_n(self) -> None:
        try:
            n = int(self._var_n.get().strip(), 0)
        except ValueError:
            messagebox.showerror("Run N", "Invalid N")
            return
        if n <= 0:
            return
        if self._run_thread_active:
            self._pending_status = "Background run already active"
            self.refresh()
            return
        if n > 50_000:

            def go() -> None:
                try:
                    res = self._ctrl.run_n(n)
                    self._run_queue.put(("done", res))
                except Exception as e:  # noqa: BLE001
                    self._run_queue.put(("error", f"Run N failed: {e!r}"))

            self._run_thread_active = True
            threading.Thread(target=go, daemon=True).start()
            self._pending_status = f"Running {n} steps in background…"
            self.refresh()
            return
        res = self._ctrl.run_n(n)
        self._finish_run(res)

    def _on_continue(self) -> None:
        try:
            mx = int(self._var_max.get().strip(), 0)
        except ValueError:
            messagebox.showerror("Continue", "Invalid max steps")
            return
        if self._run_thread_active:
            self._pending_status = "Background run already active"
            self.refresh()
            return

        def go() -> None:
            try:
                res = self._ctrl.run_n(mx)
                self._run_queue.put(("done", res))
            except Exception as e:  # noqa: BLE001
                self._run_queue.put(("error", f"Continue failed: {e!r}"))

        self._run_thread_active = True
        self._pending_status = "Continuing…"
        self.refresh()
        threading.Thread(target=go, daemon=True).start()

    def _poll_run_queue(self) -> None:
        try:
            while True:
                item = self._run_queue.get_nowait()
                if item[0] == "done":
                    self._run_thread_active = False
                    self._finish_run(item[1])
                elif item[0] == "error":
                    self._run_thread_active = False
                    self._handle_runtime_error(str(item[1]))
        except queue.Empty:
            pass
        if not self._is_closing:
            self.after(100, self._poll_run_queue)

    def _finish_run(self, res: object) -> None:
        assert isinstance(res, StepResult)
        self._apply_step_result(res)
        self.refresh()

    def _apply_step_result(self, res: object) -> None:
        assert isinstance(res, StepResult)
        if res.kind == StepKind.OK:
            if res.message == "CPU halted":
                self._pending_status = f"Halted after {res.steps_executed} steps in this run"
            elif res.steps_executed:
                self._pending_status = f"Ran {res.steps_executed} steps"
            else:
                self._pending_status = "OK"
        elif res.kind == StepKind.HALTED_ALREADY:
            self._pending_status = res.message or "CPU halted"
        elif res.kind == StepKind.BREAKPOINT:
            self._pending_status = res.message or "Breakpoint"
        elif res.kind == StepKind.ERROR:
            self._handle_runtime_error(str(res.message))

    def _handle_runtime_error(self, message: str) -> None:
        self._pending_status = f"Error: {message}"
        try:
            if not self._is_closing:
                messagebox.showerror("Execution error", message, parent=self)
        except tk.TclError:
            pass

    def _on_reset(self) -> None:
        if self._run_thread_active:
            self._pending_status = "Wait for background run to finish before reset"
            self.refresh()
            return
        self._stop_auto()
        self._ctrl.reset_cpu(preserve_breakpoints=True)
        self._perf_last_ts = time.perf_counter()
        self._perf_last_instr = 0
        self._perf_last_cycles = 0
        self._perf_active_dt = 0.0
        self._perf_active_instr = 0
        self._pending_status = "CPU reset"
        self.refresh()

    def _on_clear_trace(self) -> None:
        self._ctrl.clear_trace()
        self.refresh()

    def _on_feed_rx(self) -> None:
        if not isinstance(self._ctrl.mem, SystemBus):
            messagebox.showinfo("UART", "MMIO not enabled")
            return
        raw = self._var_rx.get().strip()
        if not raw:
            return
        try:
            parts = raw.split()
            data = bytes(int(x, 16) & 0xFF for x in parts)
        except ValueError:
            messagebox.showerror("UART", "Invalid hex bytes")
            return
        self._ctrl.feed_uart_rx(data)
        self._pending_status = f"Fed {len(data)} bytes to UART RX"
        self.refresh()

    def _on_sd_browse(self) -> None:
        p = filedialog.askopenfilename(
            parent=self,
            title="SD image file",
            filetypes=[("Image", "*.img *.bin"), ("All", "*.*")],
        )
        if p:
            self._var_sd_path.set(p)

    def _on_sd_mount(self) -> None:
        if not isinstance(self._ctrl.mem, SystemBus):
            messagebox.showinfo("Storage", "Start with --mmio to use SD.", parent=self)
            return
        raw = self._var_sd_path.get().strip()
        if not raw:
            messagebox.showwarning("Storage", "Choose a file path first.", parent=self)
            return
        try:
            self._ctrl.attach_sd_image(Path(raw))
        except (OSError, ValueError) as e:
            messagebox.showerror("Storage", str(e), parent=self)
            return
        self._pending_status = f"SD mounted: {raw}"
        self.refresh()

    def _on_sd_umount(self) -> None:
        if not isinstance(self._ctrl.mem, SystemBus):
            return
        self._ctrl.detach_sd_image()
        self._pending_status = "SD unmounted"
        self.refresh()

    def _on_sd_create_mount(self) -> None:
        if not isinstance(self._ctrl.mem, SystemBus):
            messagebox.showinfo("Storage", "Start with --mmio.", parent=self)
            return
        raw = self._var_sd_path.get().strip()
        if not raw:
            messagebox.showwarning("Storage", "Set path for new image file.", parent=self)
            return
        try:
            n = int(self._var_sd_sectors.get().strip(), 0)
        except ValueError:
            messagebox.showerror("Storage", "Invalid sector count", parent=self)
            return
        if n < 1:
            messagebox.showerror("Storage", "Need at least 1 sector", parent=self)
            return
        try:
            self._ctrl.attach_sd_image(Path(raw), create_sectors=n)
        except (OSError, ValueError) as e:
            messagebox.showerror("Storage", str(e), parent=self)
            return
        self._pending_status = f"SD created {n} sectors: {raw}"
        self.refresh()

    def _on_bp_add(self) -> None:
        try:
            a = self._parse_hex_int(self._var_bp.get())
        except ValueError:
            messagebox.showerror("Breakpoint", "Invalid address")
            return
        if a % 4:
            messagebox.showerror("Breakpoint", "Address must be word-aligned")
            return
        self._ctrl.runner.break_pcs.add(a & 0xFFFFFFFF)
        self._var_bp.set("")
        self.refresh()
        self._refresh_bp_list()

    def _on_bp_remove(self) -> None:
        sel = self._lb_bp.curselection()
        if not sel:
            return
        text = self._lb_bp.get(sel[0])
        a = int(text.split()[0], 16)
        self._ctrl.runner.break_pcs.discard(a)
        self.refresh()
        self._refresh_bp_list()

    def _on_bp_clear(self) -> None:
        self._ctrl.runner.break_pcs.clear()
        self.refresh()
        self._refresh_bp_list()

    def _refresh_bp_list(self) -> None:
        self._lb_bp.delete(0, tk.END)
        for a in sorted(self._ctrl.runner.break_pcs):
            self._lb_bp.insert(tk.END, f"0x{a:08x}")
