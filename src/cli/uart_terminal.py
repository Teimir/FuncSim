"""Separate Toplevel: UART TX as terminal + text/hex RX feed (MMIO only)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.debug_controller import DebugController


class UartTerminalWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc, ctrl: DebugController) -> None:
        super().__init__(master)
        self.title("E32C UART")
        self._ctrl = ctrl
        self._shown_len = 0
        self._poll_after: str | None = None
        self._history: list[str] = []
        self._history_index: int = -1

        ttk.Label(self, text="TX (from CPU, read-only)").pack(anchor=tk.W, padx=4, pady=2)
        self._tx = tk.Text(self, height=16, width=72, font=("Consolas", 10), state=tk.DISABLED, wrap=tk.CHAR)
        self._tx.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        bf = ttk.Frame(self)
        bf.pack(fill=tk.X, padx=4)
        ttk.Button(bf, text="Clear view", command=self._clear_view).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Clear TX buffer", command=self._clear_hw_tx).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Sync from buffer", command=self._full_resync).pack(side=tk.LEFT, padx=2)

        ttk.Label(
            self,
            text="RX → CPU. Mode: line/raw/hex. For calculator send expressions like 12*12 or HALT.",
        ).pack(anchor=tk.W, padx=4)
        rx_row = ttk.Frame(self)
        rx_row.pack(fill=tk.X, padx=4, pady=4)
        self._var_line = tk.StringVar()
        self._var_append_newline = tk.BooleanVar(value=True)
        self._var_mode = tk.StringVar(value="line")
        ttk.Combobox(
            rx_row,
            textvariable=self._var_mode,
            values=("line", "raw", "hex"),
            width=8,
            state="readonly",
        ).pack(side=tk.LEFT, padx=4)
        self._entry = ttk.Entry(rx_row, textvariable=self._var_line, width=60)
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(rx_row, text="Send", command=self._send_text).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(rx_row, text="append \\n", variable=self._var_append_newline).pack(side=tk.LEFT, padx=4)

        hist = ttk.LabelFrame(self, text="RX history")
        hist.pack(fill=tk.BOTH, expand=False, padx=4, pady=4)
        self._lb_hist = tk.Listbox(hist, height=5, font=("Consolas", 10))
        self._lb_hist.pack(fill=tk.BOTH, expand=True)
        hist_row = ttk.Frame(hist)
        hist_row.pack(fill=tk.X)
        ttk.Button(hist_row, text="Reuse selected", command=self._reuse_selected_history).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(hist_row, text="Clear history", command=self._clear_history).pack(side=tk.LEFT, padx=2, pady=2)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Return>", lambda _e: self._send_text())
        self.bind("<Up>", lambda _e: self._history_prev())
        self.bind("<Down>", lambda _e: self._history_next())
        self._schedule_poll()

    def _schedule_poll(self) -> None:
        self._poll_tx()
        self._poll_after = self.after(80, self._schedule_poll)

    def _poll_tx(self) -> None:
        from core.bus import SystemBus

        if not isinstance(self._ctrl.mem, SystemBus):
            return
        buf = bytes(self._ctrl.mem.uart.tx_buffer)
        if len(buf) > self._shown_len:
            chunk = buf[self._shown_len :]
            self._shown_len = len(buf)
            self._tx.configure(state=tk.NORMAL)
            self._tx.insert(tk.END, chunk.decode("latin-1", errors="replace"))
            self._tx.see(tk.END)
            self._tx.configure(state=tk.DISABLED)

    def _clear_view(self) -> None:
        from core.bus import SystemBus

        self._tx.configure(state=tk.NORMAL)
        self._tx.delete("1.0", tk.END)
        self._tx.configure(state=tk.DISABLED)
        if isinstance(self._ctrl.mem, SystemBus):
            self._shown_len = len(self._ctrl.mem.uart.tx_buffer)
        else:
            self._shown_len = 0

    def _clear_hw_tx(self) -> None:
        from core.bus import SystemBus

        if not isinstance(self._ctrl.mem, SystemBus):
            messagebox.showinfo("UART", "MMIO not enabled", parent=self)
            return
        self._ctrl.mem.uart.clear_tx()
        self._clear_view()

    def _full_resync(self) -> None:
        from core.bus import SystemBus

        if not isinstance(self._ctrl.mem, SystemBus):
            return
        self._tx.configure(state=tk.NORMAL)
        self._tx.delete("1.0", tk.END)
        self._tx.insert(tk.END, bytes(self._ctrl.mem.uart.tx_buffer).decode("latin-1", errors="replace"))
        self._tx.see(tk.END)
        self._tx.configure(state=tk.DISABLED)
        self._shown_len = len(self._ctrl.mem.uart.tx_buffer)

    def _send_text(self) -> None:
        from core.bus import SystemBus

        if not isinstance(self._ctrl.mem, SystemBus):
            messagebox.showinfo("UART", "MMIO not enabled", parent=self)
            return
        line = self._var_line.get().strip() if self._var_mode.get() == "hex" else self._var_line.get()
        mode = self._var_mode.get()
        if mode == "line":
            if self._var_append_newline.get():
                line += "\n"
            payload = line.encode("utf-8", errors="replace")
        elif mode == "raw":
            payload = line.encode("utf-8", errors="replace")
        elif mode == "hex":
            if not line:
                return
            try:
                payload = bytes(int(x, 16) & 0xFF for x in line.split())
            except ValueError:
                messagebox.showerror("UART", "Invalid hex", parent=self)
                return
        else:
            payload = line.encode("utf-8", errors="replace")
        if not payload:
            return
        self._ctrl.feed_uart_rx(payload)
        self._add_history(f"{mode}: {line!r}")
        self._var_line.set("")

    def _add_history(self, value: str) -> None:
        if not value:
            return
        if self._history and self._history[-1] == value:
            self._history_index = len(self._history)
            return
        self._history.append(value)
        if len(self._history) > 50:
            self._history.pop(0)
        self._history_index = len(self._history)
        self._refresh_history_view()

    def _refresh_history_view(self) -> None:
        self._lb_hist.delete(0, tk.END)
        for item in self._history:
            self._lb_hist.insert(tk.END, item)

    def _reuse_selected_history(self) -> None:
        sel = self._lb_hist.curselection()
        if not sel:
            return
        item = self._lb_hist.get(sel[0])
        mode, _, payload = item.partition(":")
        mode = mode.strip()
        if mode in ("line", "raw", "hex"):
            self._var_mode.set(mode)
        self._var_line.set(payload.strip().strip("'"))
        self._entry.focus_set()

    def _clear_history(self) -> None:
        self._history.clear()
        self._history_index = -1
        self._refresh_history_view()

    def _history_prev(self) -> None:
        if not self._history:
            return
        if self._history_index == -1:
            self._history_index = len(self._history) - 1
        else:
            self._history_index = max(0, self._history_index - 1)
        self._load_history_entry()

    def _history_next(self) -> None:
        if not self._history:
            return
        if self._history_index == -1:
            return
        self._history_index += 1
        if self._history_index >= len(self._history):
            self._history_index = len(self._history)
            self._var_line.set("")
            return
        self._load_history_entry()

    def _load_history_entry(self) -> None:
        if self._history_index < 0 or self._history_index >= len(self._history):
            return
        item = self._history[self._history_index]
        mode, _, payload = item.partition(":")
        mode = mode.strip()
        if mode in ("line", "raw", "hex"):
            self._var_mode.set(mode)
        self._var_line.set(payload.strip().strip("'"))

    def _on_close(self) -> None:
        if self._poll_after is not None:
            try:
                self.after_cancel(self._poll_after)
            except tk.TclError:
                pass
            self._poll_after = None
        self.destroy()
