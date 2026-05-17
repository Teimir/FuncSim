from core.asm import AssembleError, assemble_text


def test_branch_forward_label() -> None:
    words = assemble_text(
        """
        BEQ 31 8
        ADDI 0 1 1
        HALT
    target:
        ADDI 0 1 9
        HALT
        """
    )
    assert len(words) == 5


def test_equ_substitution() -> None:
    words = assemble_text(
        """
        .equ BASE 0x100
        ADDI 0 1 BASE
        HALT
        """
    )
    assert len(words) == 2


def test_push_pop_expand() -> None:
    words = assemble_text(
        """
        PUSH 2
        POP 2
        HALT
        """
    )
    assert len(words) == 5


def test_undefined_label_raises() -> None:
    try:
        assemble_text("B nowhere\nHALT\n")
        raise AssertionError("expected AssembleError")
    except AssembleError:
        pass
