"""Main debugger window: menu, toolbar, layout, CLI entrypoint."""

from __future__ import annotations

import argparse
import queue
import time
import tkinter as tk
from tkinter import messagebox, ttk

from cli.debug_common import add_sim_session_arguments, create_debug_controller, load_initial_image
from cli.debug_gui.actions_mixin import ActionsMixin
from cli.debug_gui.constants import (
    DEFAULT_WINDOW_GEOMETRY,
    FONT_MONO,
    FONT_MONO_BOLD,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)
from cli.debug_gui.fill_mixin import SnapshotFillMixin
from cli.debug_gui.tab_mixin import TabBuildMixin
from cli.debug_gui.theme import apply_density_to_app, apply_ttk_theme, configure_mono_treeview_style
from cli.debug_gui.tooltips import bind_status_tip
from core.debug_controller import DebugController
from core.memory import Memory
from core.spr_constants import VARIANT_CORE_INFO


class DebuggerApp(ActionsMixin, SnapshotFillMixin, TabBuildMixin, tk.Tk):
    def __init__(self, ctrl: DebugController) -> None:
        super().__init__()
        self.title(f"E32C debugger — core {ctrl.state.core_variant}")
        self._tip_override: str | None = None
        apply_ttk_theme(self)
        self._mono_font = FONT_MONO
        self._mono_bold_font = FONT_MONO_BOLD
        configure_mono_treeview_style(self, self._mono_font, self._mono_bold_font, row_height=20)
        self._var_density = tk.StringVar(value="default")
        self._ctrl = ctrl
        self._run_queue: queue.Queue[object] = queue.Queue()
        self._run_thread_active = False
        self._is_closing = False
        self._pending_status: str | None = None
        self._auto_after_id: str | None = None
        self._uart_win = None
        self._var_auto = tk.BooleanVar(value=False)
        self._var_auto_ms = tk.StringVar(value="1000")
        self._var_burst = tk.StringVar(value="1")
        self._var_list_radius = tk.StringVar(value=str(ctrl.listing_radius))
        self._var_fast_refresh = tk.BooleanVar(value=False)
        self._var_status_mode = tk.StringVar(value="minimal")
        self._var_core = tk.StringVar(value=ctrl.state.core_variant)
        self._perf_last_ts = time.perf_counter()
        self._perf_last_instr = 0
        self._perf_last_cycles = 0
        self._perf_active_dt = 0.0
        self._perf_active_instr = 0
        self.protocol("WM_DELETE_WINDOW", self._on_main_close)
        self._build_menu()
        self._build_toolbar()
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._tab_main = ttk.Frame(nb)
        self._tab_mmio = ttk.Frame(nb)
        self._tab_trace = ttk.Frame(nb)
        self._tab_bp = ttk.Frame(nb)
        self._tab_storage = ttk.Frame(nb)
        nb.add(self._tab_main, text="CPU / Memory")
        nb.add(self._tab_mmio, text="MMIO")
        nb.add(self._tab_storage, text="Storage")
        nb.add(self._tab_trace, text="Trace")
        nb.add(self._tab_bp, text="Breakpoints")
        self._build_main_tab(self._tab_main)
        self._build_mmio_tab(self._tab_mmio)
        self._build_storage_tab(self._tab_storage)
        self._build_trace_tab(self._tab_trace)
        self._build_bp_tab(self._tab_bp)
        self._apply_density_mode()
        self._status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self._status, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM
        )
        self.bind("<F7>", lambda e: self._on_step())
        self.bind("<F8>", lambda e: self._on_continue())
        self.bind("<F6>", lambda e: self._on_run_n())
        self.bind("<Control-r>", lambda e: self._on_reset())
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-u>", lambda e: self._open_uart_terminal())
        self.bind("<Control-a>", lambda e: self._toggle_auto_hotkey())
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.geometry(DEFAULT_WINDOW_GEOMETRY)
        self.after(100, self._poll_run_queue)
        self.refresh()

    def _on_main_close(self) -> None:
        self._is_closing = True
        self._stop_auto()
        if self._uart_win is not None:
            try:
                if self._uart_win.winfo_exists():
                    self._uart_win.destroy()
            except tk.TclError:
                pass
            self._uart_win = None
        try:
            self.destroy()
        except tk.TclError:
            pass

    def _build_menu(self) -> None:
        m = tk.Menu(self)
        self.config(menu=m)
        fm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="File", menu=fm)
        fm.add_command(label="Open binary…", command=self._open_binary, accelerator="Ctrl+B")
        fm.add_command(label="Open hex…", command=self._open_hex, accelerator="Ctrl+O")
        self.bind("<Control-b>", lambda e: self._open_binary())
        fm.add_separator()
        fm.add_command(label="Export snapshot (JSON)…", command=self._export_snapshot)
        fm.add_separator()
        fm.add_command(label="Exit", command=self._on_main_close)
        em = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Execute", menu=em)
        em.add_command(label="Step", command=self._on_step, accelerator="F7")
        em.add_command(label="Run N", command=self._on_run_n, accelerator="F6")
        em.add_command(label="Continue…", command=self._on_continue, accelerator="F8")
        em.add_separator()
        em.add_command(label="Reset CPU", command=self._on_reset, accelerator="Ctrl+R")
        vm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="View", menu=vm)
        vm.add_command(label="UART terminal…", command=self._open_uart_terminal, accelerator="Ctrl+U")
        vm.add_checkbutton(label="Fast refresh (skip trace/MMIO text)", variable=self._var_fast_refresh)
        vm.add_separator()
        vm.add_radiobutton(label="Density: default", variable=self._var_density, value="default", command=self._apply_density_mode)
        vm.add_radiobutton(label="Density: compact", variable=self._var_density, value="compact", command=self._apply_density_mode)
        vm.add_separator()
        vm.add_radiobutton(label="Status: minimal", variable=self._var_status_mode, value="minimal", command=self.refresh)
        vm.add_radiobutton(label="Status: full", variable=self._var_status_mode, value="full", command=self.refresh)
        vm.add_separator()
        cm = tk.Menu(vm, tearoff=0)
        vm.add_cascade(label="Core variant", menu=cm)
        for name in sorted(VARIANT_CORE_INFO.keys()):
            cm.add_radiobutton(
                label=name,
                variable=self._var_core,
                value=name,
                command=self._on_core_apply,
            )
        hm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Help", menu=hm)
        hm.add_command(
            label="Shortcuts",
            command=lambda: messagebox.showinfo(
                "Shortcuts",
                "F7 — Step\nF6 — Run N\nF8 — Continue (max steps field)\n"
                "Ctrl+R — Reset CPU\nCtrl+U — UART terminal\nCtrl+A — Toggle Auto\n"
                "Ctrl+O — Open hex\nCtrl+B — Open binary\n"
                "Toolbar / View → Core — switch full/tn9k/lite (resets CPU)\n\n"
                "Registers / memory: double-click to edit (RAM words only).\n"
                "Listing: right-click toggles breakpoint.",
                parent=self,
            ),
        )

    def _build_toolbar(self) -> None:
        outer = ttk.Frame(self)
        outer.pack(fill=tk.X, padx=4, pady=2)
        row_run = ttk.Frame(outer)
        row_run.pack(fill=tk.X)
        row_extra = ttk.Frame(outer)
        row_extra.pack(fill=tk.X, pady=(2, 0))

        b_step = ttk.Button(row_run, text="Step", command=self._on_step)
        b_step.pack(side=tk.LEFT, padx=2)
        bind_status_tip(b_step, "Execute one instruction (F7).", self)
        b_run = ttk.Button(row_run, text="Run N", command=self._on_run_n)
        b_run.pack(side=tk.LEFT, padx=2)
        bind_status_tip(b_run, "Run N steps; large N runs in background (F6).", self)
        ttk.Label(row_run, text="N:").pack(side=tk.LEFT)
        self._var_n = tk.StringVar(value="1")
        ttk.Entry(row_run, textvariable=self._var_n, width=8).pack(side=tk.LEFT, padx=2)
        for preset in ("1", "100", "1000", "10000"):
            ttk.Button(row_run, text=preset, command=lambda v=preset: self._set_n_preset(v)).pack(
                side=tk.LEFT, padx=1
            )
        b_cont = ttk.Button(row_run, text="Continue", command=self._on_continue)
        b_cont.pack(side=tk.LEFT, padx=2)
        bind_status_tip(b_cont, "Run up to max steps or until halt/break (F8).", self)
        ttk.Label(row_run, text="max:").pack(side=tk.LEFT)
        self._var_max = tk.StringVar(value="100000")
        ttk.Entry(row_run, textvariable=self._var_max, width=10).pack(side=tk.LEFT, padx=2)
        for preset in ("1000", "10000", "100000"):
            ttk.Button(row_run, text=preset, command=lambda v=preset: self._set_max_preset(v)).pack(
                side=tk.LEFT, padx=1
            )
        b_reset = ttk.Button(row_run, text="Reset", command=self._on_reset)
        b_reset.pack(side=tk.LEFT, padx=2)
        bind_status_tip(b_reset, "Reset CPU state; breakpoints preserved (Ctrl+R).", self)

        ttk.Label(row_extra, text="Core:").pack(side=tk.LEFT)
        cb_core = ttk.Combobox(
            row_extra,
            textvariable=self._var_core,
            values=sorted(VARIANT_CORE_INFO.keys()),
            state="readonly",
            width=7,
        )
        cb_core.pack(side=tk.LEFT, padx=2)
        cb_core.bind("<<ComboboxSelected>>", self._on_core_apply)
        bind_status_tip(
            cb_core,
            "Switch ISA profile (full / tn9k / lite). Resets CPU; keeps breakpoints.",
            self,
        )
        ttk.Separator(row_extra, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        cb_auto = ttk.Checkbutton(row_extra, text="Auto", variable=self._var_auto, command=self._toggle_auto)
        cb_auto.pack(side=tk.LEFT, padx=2)
        bind_status_tip(cb_auto, "Step or burst repeatedly at interval (Ctrl+A). burst=1 → single step.", self)
        ttk.Label(row_extra, text="ms:").pack(side=tk.LEFT)
        ttk.Entry(row_extra, textvariable=self._var_auto_ms, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(row_extra, text="burst:").pack(side=tk.LEFT)
        ttk.Entry(row_extra, textvariable=self._var_burst, width=5).pack(side=tk.LEFT, padx=2)

    def _apply_density_mode(self) -> None:
        apply_density_to_app(self)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="E32C debugger GUI")
    add_sim_session_arguments(p)
    args = p.parse_args(argv)

    ram = Memory()
    ctrl = create_debug_controller(ram, args)
    load_initial_image(ctrl, args)
    app = DebuggerApp(ctrl)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
