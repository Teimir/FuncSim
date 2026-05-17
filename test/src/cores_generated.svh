// GENERATED FILE — do not edit by hand.
// Source: docs/isa/cores.yaml  |  Regenerate: python scripts/gen_cores.py
// Included from RTL as: `include "cores_generated.svh" (add -Itest/src to iverilog)

`ifndef E32C_CORES_GENERATED_SVH
`define E32C_CORES_GENERATED_SVH

`define E32C_MAGIC 16'he32c
`define E32C_FAMILY_ID 8'd1
localparam logic [31:0] E32C_ISA_REVISION = 32'h00010005;

`define E32C_SPR_SAVED_IRQ_PC 5'd0
`define E32C_SPR_IRQ_VECTOR 5'd1
`define E32C_SPR_IRQ_MASK 5'd2
`define E32C_SPR_CORE_INFO 5'd3
`define E32C_SPR_ISA_REVISION 5'd4
`define E32C_SPR_FEATURES 5'd5

`define E32C_FEAT_MUL 32'd1
`define E32C_FEAT_LDREX 32'd2
`define E32C_FEAT_PIPELINE_3 32'd4
`define E32C_FEAT_FULL_ISA 32'd8
localparam logic [3:0] E32C_VARIANT_FULL = 4'd0;
localparam logic [31:0] E32C_CORE_INFO_FULL = 32'he32c0100;
localparam logic [31:0] E32C_FEATURES_FULL = 32'h0000000b;

localparam logic [3:0] E32C_VARIANT_TN9K = 4'd1;
localparam logic [31:0] E32C_CORE_INFO_TN9K = 32'he32c0110;
localparam logic [31:0] E32C_FEATURES_TN9K = 32'h00000002;

localparam logic [3:0] E32C_VARIANT_LITE = 4'd2;
localparam logic [31:0] E32C_CORE_INFO_LITE = 32'he32c0120;
localparam logic [31:0] E32C_FEATURES_LITE = 32'h00000000;

`endif // E32C_CORES_GENERATED_SVH
