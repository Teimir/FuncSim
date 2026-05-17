"""Core variant identity via read-only SPR 3–5."""

from core.spr_constants import (
    CORE_INFO_FULL,
    CORE_INFO_LITE,
    CORE_INFO_TN9K,
    FEATURES_FULL,
    FEATURES_LITE,
    FEATURES_TN9K,
    ISA_REVISION_DEFAULT,
    SPR_CORE_INFO,
    SPR_FEATURES,
    SPR_ISA_REVISION,
    TN9K_ILLEGAL_OPCODES,
    core_info_magic,
    core_info_variant,
)
from core.state import CPUState


def test_full_variant_spr_identity() -> None:
    s = CPUState()
    assert s.spr_read(SPR_CORE_INFO) == CORE_INFO_FULL
    assert s.spr_read(SPR_ISA_REVISION) == ISA_REVISION_DEFAULT
    assert s.spr_read(SPR_FEATURES) == FEATURES_FULL
    assert core_info_magic(s.spr_read(SPR_CORE_INFO)) == 0xE32C
    assert core_info_variant(s.spr_read(SPR_CORE_INFO)) == 0


def test_tn9k_variant_spr_identity() -> None:
    s = CPUState.for_variant("tn9k")
    assert s.spr_read(SPR_CORE_INFO) == CORE_INFO_TN9K
    assert core_info_variant(s.spr_read(SPR_CORE_INFO)) == 1
    assert s.spr_read(SPR_FEATURES) == FEATURES_TN9K


def test_lite_variant_spr_identity() -> None:
    s = CPUState.for_variant("lite")
    assert s.spr_read(SPR_CORE_INFO) == CORE_INFO_LITE
    assert s.spr_read(SPR_FEATURES) == FEATURES_LITE


def test_ro_spr_ignore_write() -> None:
    s = CPUState()
    s.spr_write(SPR_CORE_INFO, 0xDEADBEEF)
    assert s.spr_read(SPR_CORE_INFO) == CORE_INFO_FULL


def test_tn9k_illegal_opcodes_from_registry() -> None:
    assert "MUL" in TN9K_ILLEGAL_OPCODES
    assert len(TN9K_ILLEGAL_OPCODES) == 5
