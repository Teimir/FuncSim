"""ttk theme selection and monospace Treeview styling."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk
from typing import Any

from cli.debug_gui.constants import (
    FONT_MONO,
    FONT_MONO_BOLD,
    FONT_MONO_BOLD_COMPACT,
    FONT_MONO_COMPACT,
)

# Listing row highlight (works on light themes; overridden in density refresh)
LISTING_TAG_PC_BG = "#ffe08a"
LISTING_TAG_PC_FG = "#111111"
LISTING_TAG_BP_BG = "#ffd9d9"


def preferred_ttk_theme(style: ttk.Style) -> str:
    names = style.theme_names()
    if sys.platform == "win32" and "vista" in names:
        return "vista"
    if "clam" in names:
        return "clam"
    return "default"


def apply_ttk_theme(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    choice = preferred_ttk_theme(style)
    try:
        style.theme_use(choice)
    except tk.TclError:
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
    return style


def configure_mono_treeview_style(
    root: tk.Misc,
    mono_font: tuple[str, ...],
    mono_bold_font: tuple[str, ...],
    row_height: int,
) -> None:
    style = ttk.Style(root)
    style.configure("Mono.Treeview", font=mono_font, rowheight=row_height)
    style.configure("Mono.Treeview.Heading", font=mono_bold_font)


def apply_density_to_app(app: Any) -> None:
    compact = app._var_density.get() == "compact"
    if compact:
        app._mono_font = FONT_MONO_COMPACT
        app._mono_bold_font = FONT_MONO_BOLD_COMPACT
        row_height = 18
    else:
        app._mono_font = FONT_MONO
        app._mono_bold_font = FONT_MONO_BOLD
        row_height = 20
    configure_mono_treeview_style(app, app._mono_font, app._mono_bold_font, row_height)
    if hasattr(app, "_tv_list"):
        app._tv_list.tag_configure(
            "pc", background=LISTING_TAG_PC_BG, foreground=LISTING_TAG_PC_FG, font=app._mono_bold_font
        )
        app._tv_list.tag_configure("bp", background=LISTING_TAG_BP_BG)
    if hasattr(app, "_lbl_fetch"):
        app._lbl_fetch.configure(font=app._mono_font)
    if hasattr(app, "_lb_bp"):
        app._lb_bp.configure(font=app._mono_font)
    if hasattr(app, "_mmio_text"):
        app._mmio_text.configure(font=app._mono_font)
    if hasattr(app, "_sd_info"):
        app._sd_info.configure(font=app._mono_font)
