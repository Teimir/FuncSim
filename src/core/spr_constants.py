"""GENERATED FILE — do not edit by hand."""
# Source: docs/isa/cores.yaml  |  Regenerate: python scripts/gen_cores.py

from __future__ import annotations

E32C_MAGIC = 0xe32c
E32C_FAMILY_ID = 1
ISA_REVISION_DEFAULT = 0x10005

SPR_SAVED_IRQ_PC = 0
SPR_IRQ_VECTOR = 1
SPR_IRQ_MASK = 2
SPR_CORE_INFO = 3
SPR_ISA_REVISION = 4
SPR_FEATURES = 5

FEAT_MUL = 1 << 0
FEAT_LDREX = 1 << 1
FEAT_PIPELINE_3 = 1 << 2
FEAT_FULL_ISA = 1 << 3

CORE_VARIANT_FULL = 0
CORE_INFO_FULL = 0xe32c0100
FEATURES_FULL = 11

CORE_VARIANT_TN9K = 1
CORE_INFO_TN9K = 0xe32c0110
FEATURES_TN9K = 2

CORE_VARIANT_LITE = 2
CORE_INFO_LITE = 0xe32c0120
FEATURES_LITE = 0

VARIANT_CORE_INFO: dict[str, int] = {
    "full": 0xe32c0100,
    "tn9k": 0xe32c0110,
    "lite": 0xe32c0120,
}

VARIANT_ISA_REVISION: dict[str, int] = {
    "full": 0x10005,
    "tn9k": 0x10005,
    "lite": 0x10005,
}

VARIANT_FEATURES: dict[str, int] = {
    "full": 11,
    "tn9k": 2,
    "lite": 0,
}

VARIANT_ILLEGAL_OPCODES: dict[str, frozenset[str]] = {
    "full": frozenset({}),
    "tn9k": frozenset({'MLA', 'MUL', 'SMUL', 'SMULL', 'UMULL'}),
    "lite": frozenset({'LDREX', 'MLA', 'MUL', 'SMUL', 'SMULL', 'STREX', 'UMULL'}),
}

def core_info_magic(v: int) -> int:
    return (v >> 16) & 0xFFFF

def core_info_family(v: int) -> int:
    return (v >> 8) & 0xFF

def core_info_variant(v: int) -> int:
    return (v >> 4) & 0x0F

def core_info_impl(v: int) -> int:
    return v & 0x0F

TN9K_ILLEGAL_OPCODES = VARIANT_ILLEGAL_OPCODES["tn9k"]

__all__ = [
    "E32C_MAGIC",
    "E32C_FAMILY_ID",
    "ISA_REVISION_DEFAULT",
    "SPR_SAVED_IRQ_PC",
    "SPR_IRQ_VECTOR",
    "SPR_IRQ_MASK",
    "SPR_CORE_INFO",
    "SPR_ISA_REVISION",
    "SPR_FEATURES",
    "FEAT_MUL",
    "FEAT_LDREX",
    "FEAT_PIPELINE_3",
    "FEAT_FULL_ISA",
    "VARIANT_CORE_INFO",
    "VARIANT_ISA_REVISION",
    "VARIANT_FEATURES",
    "VARIANT_ILLEGAL_OPCODES",
    "TN9K_ILLEGAL_OPCODES",
    "CORE_VARIANT_FULL",
    "CORE_VARIANT_TN9K",
    "CORE_VARIANT_LITE",
    "CORE_INFO_FULL",
    "CORE_INFO_TN9K",
    "CORE_INFO_LITE",
    "FEATURES_FULL",
    "FEATURES_TN9K",
    "FEATURES_LITE",
    "core_info_magic",
    "core_info_family",
    "core_info_variant",
    "core_info_impl",
]
