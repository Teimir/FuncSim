`timescale 1ns/1ps

module tb_soc_longrun;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  wire uart_tx, sd_sck, sd_mosi, sd_cs_n;
  reg uart_rx = 1'b1;
  reg sd_miso = 1'b1;
soc_top #(.RAM_WORDS(1024), .PSRAM_WORDS(1024)) dut (
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
    .uart_rx(uart_rx),
    .sd_spi_sck(sd_sck),
    .sd_spi_mosi(sd_mosi),
    .sd_spi_miso(sd_miso),
    .sd_spi_cs_n(sd_cs_n)
  );
  `include "tb_psram_mem.svh"

  initial begin
    // NOP; JMP r0,-4 (tight loop)
    psram_write_word(0, 32'h0000_0000);
    psram_write_word(1, 32'h4000_07FC);

    #20 rst_n = 1;
    repeat (5000) @(posedge clk);

    if (dut.g_core_full.u_core.dbg_halted) begin
      $display("Unexpected HALT in long-run");
      $finish(1);
    end

    $display("tb_soc_longrun PASS");
    $finish;
  end
endmodule
