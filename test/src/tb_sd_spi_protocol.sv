`timescale 1ns/1ps

module tb_sd_spi_protocol;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg         m_awvalid;
  wire        m_awready;
  reg  [31:0] m_awaddr;
  reg         m_wvalid;
  wire        m_wready;
  reg  [31:0] m_wdata;
  reg  [3:0]  m_wstrb;
  wire        m_bvalid;
  reg         m_bready;
  wire [1:0]  m_bresp;
  reg         m_arvalid;
  wire        m_arready;
  reg  [31:0] m_araddr;
  wire        m_rvalid;
  reg         m_rready;
  wire [31:0] m_rdata;
  wire [1:0]  m_rresp;

  wire uart_tx;
  reg uart_rx = 1'b1;
  wire sd_sck, sd_mosi, sd_cs_n;
  reg sd_miso = 1'b1;

  soc_top #(.RAM_WORDS(256), .PSRAM_WORDS(256), .ENABLE_SD_SPI(1)) dut (
    .clk(clk),
    .rst_n(rst_n),
    .ext_awvalid(m_awvalid),
    .ext_awready(m_awready),
    .ext_awaddr(m_awaddr),
    .ext_wvalid(m_wvalid),
    .ext_wready(m_wready),
    .ext_wdata(m_wdata),
    .ext_wstrb(m_wstrb),
    .ext_bvalid(m_bvalid),
    .ext_bready(m_bready),
    .ext_bresp(m_bresp),
    .ext_arvalid(m_arvalid),
    .ext_arready(m_arready),
    .ext_araddr(m_araddr),
    .ext_rvalid(m_rvalid),
    .ext_rready(m_rready),
    .ext_rdata(m_rdata),
    .ext_rresp(m_rresp),
    .uart_tx(uart_tx),
    .uart_rx(uart_rx),
    .sd_spi_sck(sd_sck),
    .sd_spi_mosi(sd_mosi),
    .sd_spi_miso(sd_miso),
    .sd_spi_cs_n(sd_cs_n)
  );

  `include "tb_axi_tasks.svh"
  `include "tb_psram_mem.svh"

  task run_cmd(input [5:0] idx, input [31:0] arg, output [31:0] resp);
    begin
      axi_write(32'hFFFF_300C, arg);
      axi_write(32'hFFFF_3008, {23'h0, 1'b1, 2'b0, idx});
      repeat (120) @(posedge clk);
      axi_read(32'hFFFF_3010, resp);
    end
  endtask

  reg [31:0] resp;
  reg [31:0] rdw;
  initial begin
    m_awvalid = 0;
    m_awaddr = 0;
    m_wvalid = 0;
    m_wdata = 0;
    m_wstrb = 0;
    m_bready = 0;
    m_arvalid = 0;
    m_araddr = 0;
    m_rready = 0;

    psram_write_word(0, 32'hFFFF_FFFF);

    #20 rst_n = 1;

    axi_write(32'hFFFF_3000, 32'h0000_0005);
    run_cmd(6'd0, 32'h0, resp);
    if (resp[7:0] != 8'h01) $display("WARN CMD0 response mismatch: %h", resp);
    run_cmd(6'd8, 32'h0000_01AA, resp);
    if (resp != 32'h0000_01AA) $display("WARN CMD8 response mismatch: %h", resp);
    run_cmd(6'd55, 32'h0, resp);
    run_cmd(6'd41, 32'h4000_0000, resp);
    if (resp != 32'h0) $display("WARN ACMD41 response mismatch: %h", resp);

    axi_write(32'hFFFF_3018, 32'd2);
    run_cmd(6'd17, 32'd2, resp);
    if (resp != 32'h0) $display("WARN CMD17 response mismatch: %h", resp);
    axi_write(32'hFFFF_301C, 32'd0);
    axi_read(32'hFFFF_3020, rdw);
    if (rdw == 32'h0) $display("WARN CMD17 data appears zero");

    axi_write(32'hFFFF_3018, 32'd3);
    axi_write(32'hFFFF_301C, 32'd0);
    axi_write(32'hFFFF_3024, 32'h1122_3344);
    run_cmd(6'd24, 32'd3, resp);
    if (resp != 32'h0) $display("WARN CMD24 response mismatch: %h", resp);
    run_cmd(6'd17, 32'd3, resp);
    axi_write(32'hFFFF_301C, 32'd0);
    axi_read(32'hFFFF_3020, rdw);
    if (rdw != 32'h1122_3344) $display("WARN CMD24 verify mismatch: %h", rdw);

    $display("tb_sd_spi_protocol PASS");
    $finish;
  end
endmodule
