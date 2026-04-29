"""Tkinter GUI debugger for the E32C simulator."""

from __future__ import annotations

import argparse
import json
import queue
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from cli.uart_terminal import UartTerminalWindow
from core.bus import MMIO_BASE_DEFAULT, SystemBus
from core.debug_controller import DebugController, ListingLine, MmioSnapshot, StepKind, StepResult, UiSnapshot
from core.memory import Memory
from core.trace import StepTrace


class DebuggerApp(tk.Tk):
    def __init__(self, ctrl: DebugController) -> None:
        super().__init__()
        self.title("E32C debugger")
        self._ctrl = ctrl
        self._run_queue: queue.Queue[object] = queue.Queue()
        self._pending_status: str | None = None
        self._auto_after_id: str | None = None
        self._uart_win: UartTerminalWindow | None = None
        self._var_auto = tk.BooleanVar(value=False)
        self._var_auto_ms = tk.StringVar(value="1000")
        self._var_burst = tk.StringVar(value="1")
        self._var_list_radius = tk.StringVar(value=str(ctrl.listing_radius))
        self._var_fast_refresh = tk.BooleanVar(value=False)
        self.protocol("WM_DELETE_WINDOW", self._on_main_close)
        self._build_menu()
        self._build_toolbar()
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._tab_main = ttk.Frame(nb)
        self._tab_mmio = ttk.Frame(nb)
        self._tab_trace = ttk.Frame(nb)
        self._tab_bp = ttk.Frame(nb)
        nb.add(self._tab_main, text="CPU / Memory")
        nb.add(self._tab_mmio, text="MMIO")
        nb.add(self._tab_trace, text="Trace")
        nb.add(self._tab_bp, text="Breakpoints")
        self._build_main_tab(self._tab_main)
        self._build_mmio_tab(self._tab_mmio)
        self._build_trace_tab(self._tab_trace)
        self._build_bp_tab(self._tab_bp)
        self._status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self._status, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM
        )
        self.bind("<F7>", lambda e: self._on_step())
        self.bind("<F8>", lambda e: self._on_continue())
        self.bind("<Control-o>", lambda e: self._open_file())
        self.after(100, self._poll_run_queue)
        self.refresh()

    def _on_main_close(self) -> None:
        self._stop_auto()
        if self._uart_win is not None:
            try:
                if self._uart_win.winfo_exists():
                    self._uart_win.destroy()
            except tk.TclError:
                pass
            self._uart_win = None
        self.destroy()

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

    def _build_menu(self) -> None:
        m = tk.Menu(self)
        self.config(menu=m)
        fm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="File", menu=fm)
        fm.add_command(label="Open binary…", command=self._open_binary)
        fm.add_command(label="Open hex…", command=self._open_hex)
        fm.add_separator()
        fm.add_command(label="Export snapshot (JSON)…", command=self._export_snapshot)
        fm.add_separator()
        fm.add_command(label="Exit", command=self._on_main_close)
        em = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Execute", menu=em)
        em.add_command(label="Step", command=self._on_step, accelerator="F7")
        em.add_command(label="Continue", command=self._on_continue, accelerator="F8")
        em.add_command(label="Reset CPU", command=self._on_reset)
        vm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="View", menu=vm)
        vm.add_command(label="UART terminal…", command=self._open_uart_terminal)
        vm.add_checkbutton(label="Fast refresh (skip trace/MMIO text)", variable=self._var_fast_refresh)
        hm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Help", menu=hm)
        hm.add_command(
            label="Shortcuts",
            command=lambda: messagebox.showinfo(
                "Shortcuts",
                "F7 — Step\nF8 — Continue (max steps field)\nCtrl+O — Open hex\n\n"
                "Registers / memory table: double-click to edit (RAM words only).\n"
                "Listing: right-click toggles breakpoint.",
                parent=self,
            ),
        )

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(bar, text="Step", command=self._on_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="Run N", command=self._on_run_n).pack(side=tk.LEFT, padx=2)
        ttk.Label(bar, text="N:").pack(side=tk.LEFT)
        self._var_n = tk.StringVar(value="1")
        ttk.Entry(bar, textvariable=self._var_n, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="Continue…", command=self._on_continue).pack(side=tk.LEFT, padx=2)
        ttk.Label(bar, text="max:").pack(side=tk.LEFT)
        self._var_max = tk.StringVar(value="100000")
        ttk.Entry(bar, textvariable=self._var_max, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="Reset", command=self._on_reset).pack(side=tk.LEFT, padx=2)
        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Checkbutton(bar, text="Auto", variable=self._var_auto, command=self._toggle_auto).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Label(bar, text="ms:").pack(side=tk.LEFT)
        ttk.Entry(bar, textvariable=self._var_auto_ms, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(bar, text="burst:").pack(side=tk.LEFT)
        ttk.Entry(bar, textvariable=self._var_burst, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(bar, text="(1=single step)").pack(side=tk.LEFT, padx=2)

    def _build_main_tab(self, parent: ttk.Frame) -> None:
        top = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        top.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(top)
        right = ttk.Frame(top)
        top.add(left, weight=1)
        top.add(right, weight=2)
        ttk.Label(left, text="Registers (R31 = PC)").pack(anchor=tk.W)
        cols = ("i", "val")
        self._tv_regs = ttk.Treeview(left, columns=cols, show="headings", height=18)
        self._tv_regs.heading("i", text="#")
        self._tv_regs.heading("val", text="Value")
        self._tv_regs.column("i", width=36)
        self._tv_regs.column("val", width=100)
        reg_scroll = ttk.Scrollbar(left, command=self._tv_regs.yview)
        self._tv_regs.configure(yscrollcommand=reg_scroll.set)
        self._tv_regs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reg_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._tv_regs.bind("<Double-1>", self._on_reg_double)
        flf = ttk.LabelFrame(left, text="Flags")
        flf.pack(fill=tk.X, pady=4)
        self._var_flags_hex = tk.StringVar()
        ttk.Label(flf, textvariable=self._var_flags_hex).pack(anchor=tk.W)
        self._flag_vars = {}
        for name in ("IE", "Z", "C", "V", "S"):
            v = tk.BooleanVar(value=False)
            self._flag_vars[name] = v
            ttk.Checkbutton(flf, text=name, variable=v, state="disabled").pack(anchor=tk.W)
        spf = ttk.LabelFrame(left, text="SPR")
        spf.pack(fill=tk.BOTH, expand=True, pady=4)
        self._tv_spr = ttk.Treeview(spf, columns=("idx", "val", "name"), show="headings", height=6)
        for c, t in zip(("idx", "val", "name"), ("#", "Value", "Name"), strict=True):
            self._tv_spr.heading(c, text=t)
        self._tv_spr.pack(fill=tk.BOTH, expand=True)
        fetchf = ttk.LabelFrame(right, text="Next instruction @ PC")
        fetchf.pack(fill=tk.X)
        self._var_fetch = tk.StringVar()
        ttk.Label(fetchf, textvariable=self._var_fetch, font=("Consolas", 10)).pack(anchor=tk.W)
        lhead = ttk.Frame(right)
        lhead.pack(fill=tk.X)
        ttk.Label(lhead, text="Disassembly (⇒ = PC, ● = breakpoint)").pack(side=tk.LEFT)
        ttk.Label(lhead, text="  ±lines:").pack(side=tk.LEFT)
        ttk.Entry(lhead, textvariable=self._var_list_radius, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(lhead, text="Apply", command=self._on_list_radius_apply).pack(side=tk.LEFT)
        lcols = ("addr", "word", "dis", "mk")
        self._tv_list = ttk.Treeview(right, columns=lcols, show="headings", height=14)
        for c, w in zip(lcols, (90, 90, 320, 40), strict=True):
            self._tv_list.column(c, width=w)
        self._tv_list.heading("addr", text="Address")
        self._tv_list.heading("word", text="Word")
        self._tv_list.heading("dis", text="Disasm")
        self._tv_list.heading("mk", text="")
        self._tv_list.pack(fill=tk.BOTH, expand=True)
        self._tv_list.bind("<Button-3>", self._on_list_rclick)
        memf = ttk.LabelFrame(right, text="Memory page")
        memf.pack(fill=tk.BOTH, expand=True, pady=4)
        mf = ttk.Frame(memf)
        mf.pack(fill=tk.X)
        ttk.Label(mf, text="Base:").pack(side=tk.LEFT)
        self._var_page = tk.StringVar(value="0")
        ttk.Entry(mf, textvariable=self._var_page, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(mf, text="Apply", command=self._on_page_apply).pack(side=tk.LEFT, padx=2)
        ttk.Button(mf, text="◀", command=self._on_page_prev).pack(side=tk.LEFT, padx=2)
        ttk.Button(mf, text="▶", command=self._on_page_next).pack(side=tk.LEFT, padx=2)
        ttk.Button(mf, text="Sync PC", command=self._on_sync_pc_page).pack(side=tk.LEFT, padx=2)
        mcols = ("addr", "w0", "w1", "w2", "w3")
        self._tv_mem = ttk.Treeview(memf, columns=mcols, show="headings", height=10)
        for c, title in zip(mcols, ("Addr", "w0", "w1", "w2", "w3"), strict=True):
            self._tv_mem.heading(c, text=title)
            self._tv_mem.column(c, width=100 if c != "addr" else 80)
        self._tv_mem.pack(fill=tk.BOTH, expand=True)
        self._tv_mem.bind("<Double-1>", self._on_mem_double)

    def _build_mmio_tab(self, parent: ttk.Frame) -> None:
        self._mmio_text = tk.Text(parent, height=24, width=80, font=("Consolas", 10), state=tk.DISABLED)
        self._mmio_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        rx_f = ttk.Frame(parent)
        rx_f.pack(fill=tk.X, padx=4)
        ttk.Label(rx_f, text="Feed UART RX (hex bytes, e.g. 0a 4b):").pack(side=tk.LEFT)
        self._var_rx = tk.StringVar()
        ttk.Entry(rx_f, textvariable=self._var_rx, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(rx_f, text="Send to RX queue", command=self._on_feed_rx).pack(side=tk.LEFT)

    def _build_trace_tab(self, parent: ttk.Frame) -> None:
        bf = ttk.Frame(parent)
        bf.pack(fill=tk.X)
        ttk.Button(bf, text="Clear trace", command=self._on_clear_trace).pack(side=tk.LEFT, padx=2)
        cols = ("n", "pc", "word", "dis", "cyc", "h")
        self._tv_trace = ttk.Treeview(parent, columns=cols, show="headings", height=22)
        for c, t in zip(cols, ("#", "PC", "Word", "Disasm", "Cycles", "H"), strict=True):
            self._tv_trace.heading(c, text=t)
            self._tv_trace.column(c, width=70 if c == "n" else 90)
        self._tv_trace.column("dis", width=260)
        self._tv_trace.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _build_bp_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Breakpoint addresses (word-aligned, hex):").pack(anchor=tk.W, padx=4)
        lf = ttk.Frame(parent)
        lf.pack(fill=tk.X, padx=4, pady=4)
        self._var_bp = tk.StringVar()
        ttk.Entry(lf, textvariable=self._var_bp, width=16).pack(side=tk.LEFT)
        ttk.Button(lf, text="Add", command=self._on_bp_add).pack(side=tk.LEFT, padx=4)
        ttk.Button(lf, text="Remove selected", command=self._on_bp_remove).pack(side=tk.LEFT, padx=4)
        ttk.Button(lf, text="Clear all", command=self._on_bp_clear).pack(side=tk.LEFT, padx=4)
        self._lb_bp = tk.Listbox(parent, height=16, font=("Consolas", 10))
        self._lb_bp.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

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
        if n > 50_000:

            def go() -> None:
                res = self._ctrl.run_n(n)
                self.after(0, lambda: self._finish_run(res))

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

        def go() -> None:
            res = self._ctrl.run_n(mx)
            self._run_queue.put(("done", res))

        self._pending_status = "Continuing…"
        self.refresh()
        threading.Thread(target=go, daemon=True).start()

    def _poll_run_queue(self) -> None:
        try:
            while True:
                item = self._run_queue.get_nowait()
                if item[0] == "done":
                    self._finish_run(item[1])
        except queue.Empty:
            pass
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
            self._pending_status = f"Error: {res.message}"

    def _on_reset(self) -> None:
        self._stop_auto()
        self._ctrl.reset_cpu(preserve_breakpoints=True)
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
        self._refresh_bp_list()
        self._var_page.set(hex(self._ctrl.mem_page_base))
        parts = [
            f"instr={snap.instruction_count}",
            f"cycles={snap.cycles}",
            f"halted={snap.halted}",
        ]
        if self._pending_status:
            parts.append(self._pending_status)
            self._pending_status = None
        if snap.last_error:
            parts.append(snap.last_error)
        self._status.set("  |  ".join(parts))

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
            self._tv_list.insert("", tk.END, values=(f"0x{ln.addr:08x}", w, ln.disasm, mk))

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
            ]
            self._mmio_text.insert(tk.END, "\n".join(lines))
        self._mmio_text.configure(state=tk.DISABLED)

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


def main() -> None:
    p = argparse.ArgumentParser(description="E32C debugger GUI")
    p.add_argument("--load-addr", type=lambda x: int(x, 0), default=0)
    p.add_argument("--hex", type=Path, help="Hex words file")
    p.add_argument("--bin", type=Path, help="Binary image")
    p.add_argument("--mmio", action="store_true", help="SystemBus with GPIO/UART/Timer")
    p.add_argument("--mmio-base", type=lambda x: int(x, 0), default=MMIO_BASE_DEFAULT)
    args = p.parse_args()

    ram = Memory()
    ctrl = DebugController.create(ram=ram, use_mmio=args.mmio, mmio_base=args.mmio_base, load_addr=args.load_addr)
    if args.bin:
        ctrl.load_binary_file(args.bin)
        ctrl.reset_cpu(preserve_breakpoints=True)
    elif args.hex:
        ctrl.load_hex_file(args.hex)
        ctrl.reset_cpu(preserve_breakpoints=True)
    app = DebuggerApp(ctrl)
    app.mainloop()


if __name__ == "__main__":
    main()
