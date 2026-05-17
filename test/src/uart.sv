// APB wrapper around Gowin uart_tx / uart_rx (UARTexampleGOWIN), 8N1.
module apb_uart #(
  parameter int CLK_FRE_MHZ = 27,
  parameter int BAUD_RATE   = 115200,
  parameter int TX_FIFO_DEPTH = 8
) (
  input  logic        pclk,
  input  logic        presetn,
  input  logic        psel,
  input  logic        penable,
  input  logic        pwrite,
  input  logic [31:0] paddr,
  input  logic [31:0] pwdata,
  output logic [31:0] prdata,
  output logic        pready,
  output logic        pslverr,
  output logic        irq,
  output logic        uart_tx,
  input  logic        uart_rx
);
`include "uart_regs.svh"

  localparam int TX_FIFO_PTR_W = (TX_FIFO_DEPTH <= 2) ? 1 : (TX_FIFO_DEPTH <= 4) ? 2 : 3;

  logic        apb_phase;
  logic [5:0]  reg_off;
  logic        reg_write;
  logic        reg_read;

  logic [7:0]  tx_byte;
  logic        tx_valid;
  logic        tx_ready;
  logic [7:0]  rx_byte;
  logic        rx_valid;

  logic        irq_en_rx;
  logic        irq_en_tx;

  logic [7:0]              tx_fifo [0:TX_FIFO_DEPTH-1];
  logic [TX_FIFO_PTR_W-1:0] tx_wptr;
  logic [TX_FIFO_PTR_W-1:0] tx_rptr;
  logic [$clog2(TX_FIFO_DEPTH):0] tx_count;

  wire tx_fifo_full  = (tx_count == TX_FIFO_DEPTH);
  wire tx_fifo_empty = (tx_count == 0);
  wire tx_serializer_idle = tx_ready && !tx_valid;

  assign apb_phase = psel && penable;
  assign reg_off   = paddr[5:0];
  assign reg_write = apb_phase && pwrite;
  assign reg_read  = apb_phase && !pwrite;

  assign pready  = !(reg_write && reg_off == E32C_UART_OFF_TXDATA && tx_fifo_full);
  assign pslverr = 1'b0;
  assign irq     = (irq_en_rx && rx_valid) || (irq_en_tx && tx_fifo_empty && tx_serializer_idle);

  uart_tx #(
    .CLK_FRE(CLK_FRE_MHZ),
    .BAUD_RATE(BAUD_RATE)
  ) u_tx (
    .clk(pclk),
    .rst_n(presetn),
    .tx_data(tx_byte),
    .tx_data_valid(tx_valid),
    .tx_data_ready(tx_ready),
    .tx_pin(uart_tx)
  );

  uart_rx #(
    .CLK_FRE(CLK_FRE_MHZ),
    .BAUD_RATE(BAUD_RATE)
  ) u_rx (
    .clk(pclk),
    .rst_n(presetn),
    .rx_data(rx_byte),
    .rx_data_valid(rx_valid),
    .rx_data_ready(!rx_valid || (reg_read && reg_off == E32C_UART_OFF_RXDATA)),
    .rx_pin(uart_rx)
  );

  function automatic logic [TX_FIFO_PTR_W-1:0] ptr_inc(input logic [TX_FIFO_PTR_W-1:0] p);
    ptr_inc = (p == TX_FIFO_DEPTH - 1) ? '0 : p + 1'b1;
  endfunction

  always_ff @(posedge pclk) begin
    if (!presetn) begin
      tx_byte   <= 8'h00;
      tx_valid  <= 1'b0;
      tx_wptr   <= '0;
      tx_rptr   <= '0;
      tx_count  <= '0;
      irq_en_rx <= 1'b0;
      irq_en_tx <= 1'b0;
    end else begin
      if (tx_valid && tx_ready)
        tx_valid <= 1'b0;

      if (tx_serializer_idle && !tx_fifo_empty) begin
        tx_byte  <= tx_fifo[tx_rptr];
        tx_valid <= 1'b1;
        tx_rptr  <= ptr_inc(tx_rptr);
        tx_count <= tx_count - 1'b1;
      end

      if (reg_write && reg_off == E32C_UART_OFF_TXDATA && !tx_fifo_full) begin
        tx_fifo[tx_wptr] <= pwdata[7:0];
        tx_wptr  <= ptr_inc(tx_wptr);
        tx_count <= tx_count + 1'b1;
      end

      if (reg_write && reg_off == E32C_UART_OFF_CTRL) begin
        irq_en_rx <= pwdata[0];
        irq_en_tx <= pwdata[1];
      end
    end
  end

  always_comb begin
    unique case (reg_off)
      E32C_UART_OFF_RXDATA: prdata = {24'h0, rx_byte};
      E32C_UART_OFF_STATUS: prdata = {
        30'h0,
        tx_serializer_idle && tx_fifo_empty,
        rx_valid
      };
      E32C_UART_OFF_CTRL: prdata = {30'h0, irq_en_tx, irq_en_rx};
      default:            prdata = 32'h0;
    endcase
  end
endmodule
