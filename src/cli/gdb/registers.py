"""GDB register numbering for E32C (custom target, no upstream XML required for MVP)."""

from __future__ import annotations

from core.debug_controller import DebugController
from core.spr_constants import SPR_IRQ_MASK, SPR_IRQ_VECTOR, SPR_SAVED_IRQ_PC

# 32 GPR + PC + FLAGS + 3 SPR
REG_COUNT = 37

REG_PC = 32
REG_FLAGS = 33
REG_SPR_SAVED_IRQ_PC = 34
REG_SPR_IRQ_VECTOR = 35
REG_SPR_IRQ_MASK = 36


def reg_to_bytes(ctrl: DebugController, regno: int) -> bytes:
    st = ctrl.state
    if regno < 0 or regno >= REG_COUNT:
        return b"\x00\x00\x00\x00"
    if regno <= 31:
        val = st.reg_read(regno)
    elif regno == REG_PC:
        val = st.pc
    elif regno == REG_FLAGS:
        val = st.flags
    elif regno == REG_SPR_SAVED_IRQ_PC:
        val = st.spr_read(SPR_SAVED_IRQ_PC)
    elif regno == REG_SPR_IRQ_VECTOR:
        val = st.spr_read(SPR_IRQ_VECTOR)
    elif regno == REG_SPR_IRQ_MASK:
        val = st.spr_read(SPR_IRQ_MASK)
    else:
        val = 0
    return int(val & 0xFFFFFFFF).to_bytes(4, "little")


def bytes_to_reg(ctrl: DebugController, regno: int, data: bytes) -> None:
    if len(data) < 4:
        data = data.ljust(4, b"\x00")
    val = int.from_bytes(data[:4], "little")
    st = ctrl.state
    if regno <= 31:
        st.reg_write(regno, val)
    elif regno == REG_PC:
        st.set_pc(val)
    elif regno == REG_FLAGS:
        st.flags = val & 0xFFFFFFFF
    elif regno == REG_SPR_SAVED_IRQ_PC:
        st.spr_write(SPR_SAVED_IRQ_PC, val)
    elif regno == REG_SPR_IRQ_VECTOR:
        st.spr_write(SPR_IRQ_VECTOR, val)
    elif regno == REG_SPR_IRQ_MASK:
        st.spr_write(SPR_IRQ_MASK, val)


def read_all_g_packet(ctrl: DebugController) -> str:
    return "".join(reg_to_bytes(ctrl, i).hex() for i in range(REG_COUNT))


def write_all_g_packet(ctrl: DebugController, hexdata: str) -> bool:
    need = REG_COUNT * 8
    if len(hexdata) < need:
        return False
    for i in range(REG_COUNT):
        chunk = hexdata[i * 8 : (i + 1) * 8]
        bytes_to_reg(ctrl, i, bytes.fromhex(chunk))
    return True
