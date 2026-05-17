`timescale 1ns/1ps

// SD_BACKEND=SHIM: MMIO CMD0 + SPI shim toggles; GOWIN path uses wrapper stub under Icarus.
module tb_sd_backend_smoke;
`include "mmio_generated.svh"
`include "mmio_sd_regs.svh"

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

  wire sd_sck, sd_mosi, sd_cs_n;
  reg  sd_miso = 1'b1;

  soc_top #(
    .RAM_WORDS(256),
    .PSRAM_WORDS(256),
    .ENABLE_CORE(0),
    .ENABLE_SD_SPI(1),
    .SD_MMIO_MODE(1'b1),
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
    .sd_spi_sck(sd_sck),
    .sd_spi_mosi(sd_mosi),
    .sd_spi_miso(sd_miso),
    .sd_spi_cs_n(sd_cs_n),
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
  localparam SD_CTRL = SD_BASE + (`E32C_SD_SPI_REG_CTRL << 2);
  localparam SD_CMD  = SD_BASE + (`E32C_SD_SPI_REG_CMD << 2);
  localparam SD_ARG  = SD_BASE + (`E32C_SD_SPI_REG_ARG << 2);
  localparam SD_RESP = SD_BASE + (`E32C_SD_SPI_REG_RESP0 << 2);
  localparam SD_STAT = SD_BASE + (`E32C_SD_SPI_REG_STATUS << 2);

  reg [31:0] tmp;
  integer i;

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
    #20 rst_n = 1;

    axi_write(SD_CTRL, 32'h1);
    axi_write(SD_ARG, 32'h0);
    axi_write(SD_CMD, 32'h100);

    begin : wait_busy
      for (i = 0; i < 5000; i = i + 1) begin
        axi_read(SD_STAT, tmp);
        if (!tmp[0]) disable wait_busy;
      end
      $display("FAIL: SD busy stuck");
      $finish(1);
    end

    axi_read(SD_RESP, tmp);
    if (tmp !== 32'h1) begin
      $display("FAIL: CMD0 resp0 expected 1 got %h", tmp);
      $finish(1);
    end

    if (sd_cs_n !== 1'b0 && sd_cs_n !== 1'b1) begin
      $display("FAIL: cs_n X");
      $finish(1);
    end

    $display("tb_sd_backend_smoke PASS");
    $finish;
  end
endmodule
