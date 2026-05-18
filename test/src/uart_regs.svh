// GENERATED FILE — do not edit by hand.
// Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py
// Included from RTL as: `include "mmio_generated.svh" (add -Itest/src to iverilog)

`ifndef E32C_UART_REGS_SVH
`define E32C_UART_REGS_SVH

localparam logic [5:0] E32C_UART_OFF_TXDATA = 6'h00;
localparam logic [5:0] E32C_UART_OFF_RXDATA = 6'h04;
localparam logic [5:0] E32C_UART_OFF_STATUS = 6'h08;
localparam logic [5:0] E32C_UART_OFF_CTRL = 6'h0c;

localparam int E32C_UART_STAT_RX_READY = 0;
localparam int E32C_UART_STAT_TX_IDLE = 1;
localparam int E32C_UART_STAT_TX_FULL = 2;
localparam int E32C_UART_STAT_RX_FULL = 3;

localparam int E32C_UART_CTRL_IRQ_RX = 0;
localparam int E32C_UART_CTRL_IRQ_TX = 1;

`endif // E32C_UART_REGS_SVH
