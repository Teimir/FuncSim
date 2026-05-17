"""Build notebook tabs (CPU, MMIO, storage, trace, breakpoints)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from cli.debug_gui.constants import (
    DISASM_COL_WIDTHS,
    FONT_MONO,
    MEM_COL_WIDTH_ADDR,
    MEM_COL_WIDTH_WORD,
    TRACE_COL_WIDTH_DEFAULT,
    TRACE_COL_WIDTH_DISASM,
    TRACE_COL_WIDTH_N,
)
from cli.debug_gui.theme import LISTING_TAG_BP_BG, LISTING_TAG_PC_BG, LISTING_TAG_PC_FG


class TabBuildMixin:
    _ctrl: Any
    _mono_font: Any
    _mono_bold_font: Any
    _var_list_radius: Any

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
        self._tv_regs.configure(style="Mono.Treeview")
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
        self._tv_spr.configure(style="Mono.Treeview")
        fetchf = ttk.LabelFrame(right, text="Next instruction @ PC")
        fetchf.pack(fill=tk.X)
        self._var_fetch = tk.StringVar()
        self._lbl_fetch = ttk.Label(fetchf, textvariable=self._var_fetch, font=self._mono_font)
        self._lbl_fetch.pack(anchor=tk.W)
        lhead = ttk.Frame(right)
        lhead.pack(fill=tk.X)
        ttk.Label(lhead, text="Disassembly (⇒ = PC, ● = breakpoint)").pack(side=tk.LEFT)
        ttk.Label(lhead, text="  ±lines:").pack(side=tk.LEFT)
        ttk.Entry(lhead, textvariable=self._var_list_radius, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(lhead, text="Apply", command=self._on_list_radius_apply).pack(side=tk.LEFT)
        lcols = ("addr", "word", "dis", "mk")
        self._tv_list = ttk.Treeview(right, columns=lcols, show="headings", height=14)
        for c, w in zip(lcols, DISASM_COL_WIDTHS, strict=True):
            self._tv_list.column(c, width=w)
        self._tv_list.heading("addr", text="Address")
        self._tv_list.heading("word", text="Word")
        self._tv_list.heading("dis", text="Disasm")
        self._tv_list.heading("mk", text="")
        self._tv_list.pack(fill=tk.BOTH, expand=True)
        self._tv_list.configure(style="Mono.Treeview")
        self._tv_list.tag_configure("pc", background=LISTING_TAG_PC_BG, foreground=LISTING_TAG_PC_FG, font=self._mono_bold_font)
        self._tv_list.tag_configure("bp", background=LISTING_TAG_BP_BG)
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
            self._tv_mem.column(c, width=MEM_COL_WIDTH_WORD if c != "addr" else MEM_COL_WIDTH_ADDR)
        self._tv_mem.pack(fill=tk.BOTH, expand=True)
        self._tv_mem.configure(style="Mono.Treeview")
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

    def _build_storage_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="SD / block device (see docs/mmio.md). Requires session with MMIO (--mmio).",
        ).pack(anchor=tk.W, padx=4, pady=2)
        self._var_sd_path = tk.StringVar()
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=4, pady=4)
        ttk.Entry(row, textvariable=self._var_sd_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="Browse…", command=self._on_sd_browse).pack(side=tk.LEFT, padx=4)
        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.X, padx=4)
        ttk.Button(row2, text="Mount", command=self._on_sd_mount).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="Unmount", command=self._on_sd_umount).pack(side=tk.LEFT, padx=2)
        ttk.Label(row2, text="Create empty (sectors):").pack(side=tk.LEFT, padx=(16, 0))
        self._var_sd_sectors = tk.StringVar(value="8")
        ttk.Entry(row2, textvariable=self._var_sd_sectors, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="Create & mount", command=self._on_sd_create_mount).pack(side=tk.LEFT, padx=4)
        self._sd_info = tk.Text(parent, height=14, width=80, font=FONT_MONO, state=tk.DISABLED)
        self._sd_info.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _build_trace_tab(self, parent: ttk.Frame) -> None:
        bf = ttk.Frame(parent)
        bf.pack(fill=tk.X)
        ttk.Button(bf, text="Clear trace", command=self._on_clear_trace).pack(side=tk.LEFT, padx=2)
        cols = ("n", "pc", "word", "dis", "cyc", "h")
        self._tv_trace = ttk.Treeview(parent, columns=cols, show="headings", height=22)
        for c, t in zip(cols, ("#", "PC", "Word", "Disasm", "Cycles", "H"), strict=True):
            self._tv_trace.heading(c, text=t)
            self._tv_trace.column(c, width=TRACE_COL_WIDTH_N if c == "n" else TRACE_COL_WIDTH_DEFAULT)
        self._tv_trace.column("dis", width=TRACE_COL_WIDTH_DISASM)
        self._tv_trace.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._tv_trace.configure(style="Mono.Treeview")

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
