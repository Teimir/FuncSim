#!/usr/bin/env python3
"""Generate spr_constants.py and cores_generated.svh from docs/isa/cores.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "docs" / "isa" / "cores.yaml"
PY_OUT = ROOT / "src" / "core" / "spr_constants.py"
SVH_OUT = ROOT / "test" / "src" / "cores_generated.svh"

HEADER_SVH = """// GENERATED FILE — do not edit by hand.
// Source: docs/isa/cores.yaml  |  Regenerate: python scripts/gen_cores.py
// Included from RTL as: `include "cores_generated.svh" (add -Itest/src to iverilog)

"""
HEADER_PY = '''"""GENERATED FILE — do not edit by hand."""
# Source: docs/isa/cores.yaml  |  Regenerate: python scripts/gen_cores.py

from __future__ import annotations

'''

MUL_OPCODES = frozenset({"SMUL", "MUL", "UMULL", "SMULL", "MLA"})
LDREX_OPCODES = frozenset({"LDREX", "STREX"})


def _u32(x: int) -> int:
    return x & 0xFFFFFFFF


def _hex_py(n: int) -> str:
    if n >= 0x10:
        return hex(n)
    return repr(n)


def _parse_int(v: object) -> int:
    if isinstance(v, int):
        return _u32(v)
    s = str(v).strip().lower()
    return _u32(int(s, 0))


def _core_info(magic: int, family_id: int, variant_id: int, core_impl: int) -> int:
    return _u32((magic << 16) | (family_id << 8) | (variant_id << 4) | core_impl)


def _features_mask(features: dict, feature_bits: dict[str, int]) -> int:
    mask = 0
    for name, bit in feature_bits.items():
        if features.get(name, False):
            mask |= 1 << bit
    return _u32(mask)


def _illegal_opcodes(features: dict, feature_opcode_sets: dict[str, list[str]]) -> frozenset[str]:
    illegal: set[str] = set()
    for feat, opcodes in feature_opcode_sets.items():
        if not features.get(feat, False):
            illegal.update(opcodes)
    return frozenset(illegal)


def main() -> int:
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    magic = _parse_int(data["isa"]["magic"])
    isa_revision = _parse_int(data["isa"]["revision"])
    family_id = int(data["family"]["id"])
    variants: dict = data["variants"]
    spr: dict = data["spr"]
    feature_bits: dict[str, int] = {k: int(v) for k, v in data["feature_bits"].items()}
    feature_opcode_sets: dict[str, list[str]] = data.get("feature_opcode_sets", {})

    variant_ids: list[int] = []
    for key, ent in variants.items():
        vid = int(ent["id"])
        if vid in variant_ids:
            print(f"gen_cores: duplicate variant id {vid}", file=sys.stderr)
            return 1
        variant_ids.append(vid)

    spr_upper = {k.upper(): int(v) for k, v in spr.items()}

    svh = [
        HEADER_SVH.rstrip() + "\n\n",
        "`ifndef E32C_CORES_GENERATED_SVH\n",
        "`define E32C_CORES_GENERATED_SVH\n\n",
        f"`define E32C_MAGIC 16'h{magic:04x}\n",
        f"`define E32C_FAMILY_ID 8'd{family_id}\n",
        f"localparam logic [31:0] E32C_ISA_REVISION = 32'h{isa_revision:08x};\n\n",
    ]
    for sname, sidx in spr_upper.items():
        svh.append(f"`define E32C_SPR_{sname} 5'd{sidx}\n")
    svh.append("\n")

    py = [HEADER_PY]
    py.append(f"E32C_MAGIC = {_hex_py(magic)}\n")
    py.append(f"E32C_FAMILY_ID = {family_id}\n")
    py.append(f"ISA_REVISION_DEFAULT = {_hex_py(isa_revision)}\n\n")

    for sname, sidx in spr_upper.items():
        py_name = f"SPR_{sname}" if sname != "CORE_INFO" else "SPR_CORE_INFO"
        if sname == "ISA_REVISION":
            py_name = "SPR_ISA_REVISION"
        elif sname == "FEATURES":
            py_name = "SPR_FEATURES"
        elif sname == "SAVED_IRQ_PC":
            py_name = "SPR_SAVED_IRQ_PC"
        elif sname == "IRQ_VECTOR":
            py_name = "SPR_IRQ_VECTOR"
        elif sname == "IRQ_MASK":
            py_name = "SPR_IRQ_MASK"
        py.append(f"{py_name} = {sidx}\n")

    py.append("\n")
    for feat, bit in sorted(feature_bits.items(), key=lambda x: x[1]):
        const = feat.upper()
        if feat == "pipeline_3":
            const = "PIPELINE_3"
        elif feat == "full_isa":
            const = "FULL_ISA"
        py.append(f"FEAT_{const} = 1 << {bit}\n")
        svh.append(f"`define E32C_FEAT_{const} 32'd{1 << bit}\n")
    py.append("\n")

    variant_rows: list[tuple[str, int, int, int, frozenset[str]]] = []
    for key in sorted(variants.keys(), key=lambda k: int(variants[k]["id"])):
        ent = variants[key]
        vid = int(ent["id"])
        impl = int(ent.get("core_impl", 0))
        feats = ent["features"]
        core_info = _core_info(magic, family_id, vid, impl)
        feat_mask = _features_mask(feats, feature_bits)
        illegal = _illegal_opcodes(feats, feature_opcode_sets)
        variant_rows.append((key, core_info, feat_mask, vid, illegal))

        ukey = key.upper()
        svh.append(f"localparam logic [3:0] E32C_VARIANT_{ukey} = 4'd{vid};\n")
        svh.append(f"localparam logic [31:0] E32C_CORE_INFO_{ukey} = 32'h{core_info:08x};\n")
        svh.append(f"localparam logic [31:0] E32C_FEATURES_{ukey} = 32'h{feat_mask:08x};\n\n")

        py.append(f"CORE_VARIANT_{ukey} = {vid}\n")
        py.append(f"CORE_INFO_{ukey} = {_hex_py(core_info)}\n")
        py.append(f"FEATURES_{ukey} = {_hex_py(feat_mask)}\n\n")

    py.append("VARIANT_CORE_INFO: dict[str, int] = {\n")
    for key, core_info, _fm, _vid, _ill in variant_rows:
        py.append(f'    "{key}": {_hex_py(core_info)},\n')
    py.append("}\n\n")

    py.append("VARIANT_ISA_REVISION: dict[str, int] = {\n")
    for key, *_ in variant_rows:
        py.append(f'    "{key}": {_hex_py(isa_revision)},\n')
    py.append("}\n\n")

    py.append("VARIANT_FEATURES: dict[str, int] = {\n")
    for key, _ci, feat_mask, _vid, _ill in variant_rows:
        py.append(f'    "{key}": {_hex_py(feat_mask)},\n')
    py.append("}\n\n")

    py.append("VARIANT_ILLEGAL_OPCODES: dict[str, frozenset[str]] = {\n")
    for key, *_rest, illegal in variant_rows:
        items = ", ".join(repr(x) for x in sorted(illegal))
        py.append(f'    "{key}": frozenset({{{items}}})')
        py.append(",\n")
    py.append("}\n\n")

    py.append(
        "def core_info_magic(v: int) -> int:\n"
        "    return (v >> 16) & 0xFFFF\n\n"
        "def core_info_family(v: int) -> int:\n"
        "    return (v >> 8) & 0xFF\n\n"
        "def core_info_variant(v: int) -> int:\n"
        "    return (v >> 4) & 0x0F\n\n"
        "def core_info_impl(v: int) -> int:\n"
        "    return v & 0x0F\n\n"
    )

    py.append("TN9K_ILLEGAL_OPCODES = VARIANT_ILLEGAL_OPCODES[\"tn9k\"]\n\n")

    all_names = [
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
    py.append("__all__ = [\n")
    for n in all_names:
        py.append(f'    "{n}",\n')
    py.append("]\n")

    svh.append("`endif // E32C_CORES_GENERATED_SVH\n")

    PY_OUT.write_text("".join(py), encoding="utf-8", newline="\n")
    SVH_OUT.write_text("".join(svh), encoding="utf-8", newline="\n")
    print(f"Wrote {PY_OUT.relative_to(ROOT)}")
    print(f"Wrote {SVH_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
