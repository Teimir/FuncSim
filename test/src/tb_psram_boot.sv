`timescale 1ns/1ps

// Reset boot copy into PSRAM, then core fetches from PC=0.
module tb_psram_boot;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  wire uart_tx;
  reg uart_rx = 1'b1;
  wire sd_spi_sck, sd_spi_mosi, sd_spi_cs_n;
  wire soc_activity, illegal_instr, core_halted_obs;
  wire [31:0] gpio_out_obs, core_pc_obs;
soc_top #(
    .RAM_WORDS(256),
    .PSRAM_WORDS(256),
    .ENABLE_FW_BOOTLOAD(1'b1),
    .USE_FPGA_RAM(1'b0),
    .USE_READMEMH(1'b0)
  ) dut (
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
    .sd_spi_sck(sd_spi_sck),
    .sd_spi_mosi(sd_spi_mosi),
    .sd_spi_miso(1'b1),
    .sd_spi_cs_n(sd_spi_cs_n),
    .soc_activity(soc_activity),
    .illegal_instr(illegal_instr),
    .gpio_out_obs(gpio_out_obs),
    .core_pc_obs(core_pc_obs),
    .core_halted_obs(core_halted_obs),
    .if_req_obs(),
    .if_resp_obs(),
    .if_stall_obs()
  );

  wire fw_ready = dut.g_mem_psram.u_psram.fw_ready;

  initial begin
    #19 rst_n = 1;
    wait (fw_ready === 1'b1);
    repeat (200) @(posedge clk);
    if (!fw_ready) begin
      $display("fw_ready lost");
      $finish(1);
    end
    if (core_pc_obs === 32'h0) begin
      $display("pc still zero after boot");
      $finish(1);
    end
    $display("tb_psram_boot PASS");
    $finish;
  end
endmodule
