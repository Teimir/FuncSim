"""Golden strings for format_instruction / disassemble_word per ISA format."""

from core.decode import decode_word
from core.disasm import disassemble_word, format_instruction
from core.exceptions import IllegalInstruction


def test_format_special_nop() -> None:
    ins = decode_word(0)
    assert format_instruction(ins) == "NOP"


def test_format_special_halt() -> None:
    ins = decode_word(0xFFFFFFFF)
    assert format_instruction(ins) == "HALT"


def test_format_rrr() -> None:
    ins = decode_word(0x84221800)
    assert format_instruction(ins) == "ADD r1 r2 r3"


def test_format_mul() -> None:
    ins = decode_word(0xB0221900)
    assert format_instruction(ins) == "MUL r1 r2 r3 r4"


def test_format_imm16_addi() -> None:
    ins = decode_word(0xC0204005)
    assert format_instruction(ins) == "ADDI r1 r8 5"


def test_format_imm16_subi() -> None:
    # SUBI opcode 0b110001 = 0x31 << 26, r1=2, immh=0, res=3, imm11=1 -> imm32=1
    w = (0x31 << 26) | (2 << 21) | (0 << 16) | (3 << 11) | 1
    ins = decode_word(w)
    assert ins.mnemonic == "SUBI"
    assert format_instruction(ins) == "SUBI r2 r3 1"


def test_format_branch() -> None:
    ins = decode_word(0x40A00004)
    assert format_instruction(ins) == "JMP r5 4"


def test_format_load_store() -> None:
    ins = decode_word(0x0422A800)
    assert format_instruction(ins) == "LDR r1 r2 21 0"


def test_format_store() -> None:
    ins = decode_word(0x08221800)
    assert format_instruction(ins) == "STR r1 r2 3 0"


def test_format_bare_ei_di_iret() -> None:
    assert format_instruction(decode_word(0xC8000000)) == "EI"
    assert format_instruction(decode_word(0xCC000000)) == "DI"
    assert format_instruction(decode_word(0xF8000000)) == "IRET"


def test_format_spr() -> None:
    ins = decode_word(0xD0202800)
    assert format_instruction(ins) == "READSPR r1 5"


def test_format_branch_cond_beq() -> None:
    ins = decode_word(0x600A0200)
    assert ins.mnemonic == "BJ"
    assert format_instruction(ins) == "BEQ r5 8"


def test_format_writespr() -> None:
    ins = decode_word(0x64202800)
    assert ins.mnemonic == "WRITESPR"
    assert format_instruction(ins) == "WRITESPR r1 5"


def test_disassemble_illegal_word() -> None:
    s = disassemble_word(0x00000001)
    assert "0x00000001" in s
    assert "illegal" in s


def test_disassemble_word_roundtrip_known() -> None:
    assert disassemble_word(0) == "NOP"


def test_decode_illegal_raises() -> None:
    try:
        decode_word(0x00000001)
    except IllegalInstruction:
        return
    raise AssertionError("expected IllegalInstruction")
