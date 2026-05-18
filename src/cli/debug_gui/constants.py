"""Fonts and Treeview column widths for the debugger GUI."""

# Initial window size (all 32 GPR + disasm + memory page visible on typical displays)
DEFAULT_WINDOW_GEOMETRY = "1320x920"
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 720
REG_TREE_ROWS = 32
DISASM_TREE_ROWS = 13
MEM_TREE_ROWS = 14
SPR_TREE_ROWS = 6

FONT_MONO = ("Consolas", 10)
FONT_MONO_BOLD = ("Consolas", 10, "bold")
FONT_MONO_COMPACT = ("Consolas", 9)
FONT_MONO_BOLD_COMPACT = ("Consolas", 9, "bold")
DISASM_COL_WIDTHS = (100, 100, 420, 40)
MEM_COL_WIDTH_ADDR = 90
MEM_COL_WIDTH_WORD = 110
TRACE_COL_WIDTH_DEFAULT = 100
TRACE_COL_WIDTH_N = 70
TRACE_COL_WIDTH_DISASM = 320
