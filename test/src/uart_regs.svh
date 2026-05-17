// UART MMIO layout (matches src/core/peripherals/uart.py and docs/mmio.md).
`ifndef E32C_UART_REGS_SVH
`define E32C_UART_REGS_SVH

localparam logic [5:0] E32C_UART_OFF_TXDATA = 6'h00;
localparam logic [5:0] E32C_UART_OFF_RXDATA = 6'h04;
localparam logic [5:0] E32C_UART_OFF_STATUS = 6'h08;
localparam logic [5:0] E32C_UART_OFF_CTRL   = 6'h0C;

// STATUS bits
localparam int E32C_UART_STAT_RX_READY = 0;
localparam int E32C_UART_STAT_TX_IDLE  = 1;
localparam int E32C_UART_STAT_TX_FULL  = 2;
localparam int E32C_UART_STAT_RX_FULL  = 3;

`endif
