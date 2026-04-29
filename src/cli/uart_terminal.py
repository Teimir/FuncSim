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

        ttk.Label(self, text="TX (from CPU, read-only)").pack(anchor=tk.W, padx=4, pady=2)
        self._tx = tk.Text(self, height=16, width=72, font=("Consolas", 10), state=tk.DISABLED, wrap=tk.CHAR)
        self._tx.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        bf = ttk.Frame(self)
        bf.pack(fill=tk.X, padx=4)
        ttk.Button(bf, text="Clear view", command=self._clear_view).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Clear TX buffer", command=self._clear_hw_tx).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Sync from buffer", command=self._full_resync).pack(side=tk.LEFT, padx=2)

        ttk.Label(self, text="RX → CPU (plain text; sent as UTF-8 bytes)").pack(anchor=tk.W, padx=4)
        rx_row = ttk.Frame(self)
        rx_row.pack(fill=tk.X, padx=4, pady=4)
        self._var_line = tk.StringVar()
        ttk.Entry(rx_row, textvariable=self._var_line, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(rx_row, text="Send", command=self._send_text).pack(side=tk.LEFT, padx=4)

        ttk.Label(self, text="Or hex bytes (e.g. 58 0a):").pack(anchor=tk.W, padx=4)
        hx_row = ttk.Frame(self)
        hx_row.pack(fill=tk.X, padx=4, pady=2)
        self._var_hex = tk.StringVar()
        ttk.Entry(hx_row, textvariable=self._var_hex, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(hx_row, text="Send hex", command=self._send_hex).pack(side=tk.LEFT, padx=4)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
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
        line = self._var_line.get()
        self._ctrl.feed_uart_rx(line.encode("utf-8", errors="replace"))
        self._var_line.set("")

    def _send_hex(self) -> None:
        from core.bus import SystemBus

        if not isinstance(self._ctrl.mem, SystemBus):
            messagebox.showinfo("UART", "MMIO not enabled", parent=self)
            return
        raw = self._var_hex.get().strip()
        if not raw:
            return
        try:
            data = bytes(int(x, 16) & 0xFF for x in raw.split())
        except ValueError:
            messagebox.showerror("UART", "Invalid hex", parent=self)
            return
        self._ctrl.feed_uart_rx(data)
        self._var_hex.set("")

    def _on_close(self) -> None:
        if self._poll_after is not None:
            try:
                self.after_cancel(self._poll_after)
            except tk.TclError:
                pass
            self._poll_after = None
        self.destroy()
