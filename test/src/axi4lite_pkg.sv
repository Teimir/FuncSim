package axi4lite_pkg;
  localparam logic [1:0] AXI_RESP_OKAY   = 2'b00;
  localparam logic [1:0] AXI_RESP_SLVERR = 2'b10;

  localparam logic [31:0] RAM_BASE  = 32'h0000_0000;
  localparam logic [31:0] APB_BASE  = 32'hFFFF_0000;
  localparam logic [31:0] UART_BASE = 32'hFFFF_1000;
endpackage
