`timescale 1ns/1ps

module tb_equiv_basic;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  wire uart_tx;
  reg uart_rx = 1'b1;
  wire sd_spi_sck, sd_spi_mosi, sd_spi_cs_n;
  wire soc_activity, illegal_instr, core_halted_obs, if_req_obs, if_resp_obs, if_stall_obs;
  wire [31:0] gpio_out_obs, core_pc_obs;

  soc_top #(.RAM_WORDS(256), .PSRAM_WORDS(256)) dut (
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
    .if_req_obs(if_req_obs),
    .if_resp_obs(if_resp_obs),
    .if_stall_obs(if_stall_obs)
  );

  initial begin
    // ADDI 0 1 5; HALT — little-endian word in PSRAM byte banks
    dut.g_mem_psram.u_psram.mem_b0[0] = 8'h05;
    dut.g_mem_psram.u_psram.mem_b1[0] = 8'h08;
    dut.g_mem_psram.u_psram.mem_b2[0] = 8'h00;
    dut.g_mem_psram.u_psram.mem_b3[0] = 8'hC0;
    dut.g_mem_psram.u_psram.mem_b0[1] = 8'hFF;
    dut.g_mem_psram.u_psram.mem_b1[1] = 8'hFF;
    dut.g_mem_psram.u_psram.mem_b2[1] = 8'hFF;
    dut.g_mem_psram.u_psram.mem_b3[1] = 8'hFF;
    #20 rst_n = 1;
    repeat (500) @(posedge clk);
    $display("RTL_R1=%0d", dut.g_core_full.u_core.dbg_r1);
    $finish;
  end
endmodule
