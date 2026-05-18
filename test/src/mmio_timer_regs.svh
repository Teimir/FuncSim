// GENERATED FILE — do not edit by hand.
// Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py
// Included from RTL as: `include "mmio_generated.svh" (add -Itest/src to iverilog)

`ifndef E32C_MMIO_TIMER_REGS_SVH
`define E32C_MMIO_TIMER_REGS_SVH

localparam logic [5:0] E32C_TIMER_OFF_COUNTER = 6'h00;
localparam logic [3:0] E32C_TIMER_WORD_COUNTER = 4'h0;
localparam logic [5:0] E32C_TIMER_OFF_COUNTER_HI_PAD = 6'h04;
localparam logic [3:0] E32C_TIMER_WORD_COUNTER_HI_PAD = 4'h1;
localparam logic [5:0] E32C_TIMER_OFF_PERIOD_LO = 6'h08;
localparam logic [3:0] E32C_TIMER_WORD_PERIOD_LO = 4'h2;
localparam logic [5:0] E32C_TIMER_OFF_PERIOD_HI = 6'h0c;
localparam logic [3:0] E32C_TIMER_WORD_PERIOD_HI = 4'h3;
localparam logic [5:0] E32C_TIMER_OFF_CTRL = 6'h10;
localparam logic [3:0] E32C_TIMER_WORD_CTRL = 4'h4;

localparam int E32C_TIMER_CTRL_IRQ_EN = 0;
localparam int E32C_TIMER_CTRL_PENDING = 1;
localparam int E32C_TIMER_CTRL_ACK_W1C = 2;

`endif // E32C_MMIO_TIMER_REGS_SVH
