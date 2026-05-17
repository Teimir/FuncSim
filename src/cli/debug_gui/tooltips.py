"""Lightweight status-bar hints on widget hover (no extra windows)."""

from __future__ import annotations

import tkinter as tk
from typing import Any


def bind_status_tip(widget: tk.Widget, text: str, host: Any) -> None:
    """While the pointer is over ``widget``, replace the status line with ``text``."""

    def on_enter(_event: tk.Event[Any]) -> None:
        host._tip_override = text
        host.refresh(full=False)

    def on_leave(_event: tk.Event[Any]) -> None:
        host._tip_override = None
        host.refresh(full=False)

    widget.bind("<Enter>", on_enter, add=True)
    widget.bind("<Leave>", on_leave, add=True)
