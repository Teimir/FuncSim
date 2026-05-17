`timescale 1ns/1ps

module tb_sd_block;
`include "mmio_generated.svh"
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

soc_top #(
  .RAM_WORDS(256),
  .PSRAM_WORDS(256),
  .ENABLE_CORE(0),
  .ENABLE_SD_SPI(1),
  .SD_MMIO_MODE(1'b0),
  .SD_BACKEND(1'b0)
) dut (
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
    .uart_tx(),
    .uart_rx(1'b1),
    .sd_spi_sck(),
    .sd_spi_mosi(),
    .sd_spi_miso(1'b1),
    .sd_spi_cs_n(),
    .soc_activity(),
    .illegal_instr(),
    .gpio_out_obs(),
    .core_pc_obs(),
    .core_halted_obs(),
    .if_req_obs(),
    .if_resp_obs(),
    .if_stall_obs()
  );
  `include "tb_axi_tasks.svh"

  localparam SD_BASE = `E32C_SD_SPI_BASE;
  localparam OFF_CTRL = 32'h00;
  localparam OFF_STATUS = 32'h04;
  localparam OFF_LBA = 32'h08;
  localparam OFF_DATA = 32'h10;

  reg [31:0] status;
  reg [31:0] word;

  initial begin
    m_awvalid = 0;
    m_wvalid = 0;
    m_bready = 0;
    m_arvalid = 0;
    m_rready = 0;
    #20 rst_n = 1;

    axi_write(SD_BASE + OFF_LBA, 32'd0);
    axi_write(SD_BASE + OFF_DATA, 32'hDEADBEEF);
    axi_write(SD_BASE + OFF_CTRL, 32'd2);
    axi_read(SD_BASE + OFF_STATUS, status);
    if (!(status & 32'h1)) begin
      $display("FAIL: block write not READY");
      $finish(1);
    end
    axi_write(SD_BASE + OFF_CTRL, 32'd1);
    axi_read(SD_BASE + OFF_DATA, word);
    if (word !== 32'hDEADBEEF) begin
      $display("FAIL: block read expected DEADBEEF got %h", word);
      $finish(1);
    end
    $display("tb_sd_block PASS");
    $finish;
  end
endmodule
