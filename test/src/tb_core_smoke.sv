`timescale 1ns/1ps

module tb_core_smoke;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  wire uart_tx;
  reg  uart_rx = 1'b1;

  soc_top #(.RAM_WORDS(1024)) dut (
    .clk(clk),
    .rst_n(rst_n),
    .ext_awvalid(1'b0),
    .ext_awready(),
    .ext_awaddr(32'h0),
    .ext_wvalid(1'b0),
    .ext_wready(),
    .ext_wdata(32'h0),
    .ext_wstrb(4'h0),
    .ext_bvalid(),
    .ext_bready(1'b0),
    .ext_bresp(),
    .ext_arvalid(1'b0),
    .ext_arready(),
    .ext_araddr(32'h0),
    .ext_rvalid(),
    .ext_rready(1'b0),
    .ext_rdata(),
    .ext_rresp(),
    .uart_tx(uart_tx),
    .uart_rx(uart_rx)
  );

  initial begin
    #20 rst_n = 1;
    repeat (20) @(posedge clk);
    if (dut.u_core.dbg_pc == 32'h0000_0000) begin
      $display("Expected PC to advance, got %h", dut.u_core.dbg_pc);
      $finish(1);
    end
    $display("tb_core_smoke PASS");
    $finish;
  end
endmodule
