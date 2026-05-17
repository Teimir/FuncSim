`timescale 1ns/1ps

// UART TX pin wired to RX — full 8N1 loopback through Gowin uart_tx/uart_rx.
module tb_uart_loopback;
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

  wire uart_tx;
  wire uart_rx;

  assign uart_rx = uart_tx;
soc_top #(.RAM_WORDS(256), .PSRAM_WORDS(256), .ENABLE_CORE(0)) dut (
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

  localparam UART_TXDATA = `E32C_UART_BASE + 32'h0;
  localparam UART_RXDATA = `E32C_UART_BASE + 32'h4;
  localparam UART_STATUS = `E32C_UART_BASE + 32'h8;

  reg [31:0] status;
  reg [31:0] rxdata;
  reg [7:0]  test_byte;

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
    test_byte = 8'hA5;
    #20 rst_n = 1;

    fork
      begin
        #2_000_000;
        $display("tb_uart_loopback global timeout");
        $finish(1);
      end
    join_none

    axi_write(UART_TXDATA, {24'h0, test_byte});

    begin : wait_rx
      integer k;
      for (k = 0; k < 100000; k = k + 1) begin
        axi_read(UART_STATUS, status);
        if (status[0]) disable wait_rx;
      end
      $display("FAIL: RX not ready after loopback");
      $finish(1);
    end

    axi_read(UART_RXDATA, rxdata);
    if (rxdata[7:0] !== test_byte) begin
      $display("FAIL: loopback byte expected %h got %h", test_byte, rxdata[7:0]);
      $finish(1);
    end

    $display("tb_uart_loopback PASS");
    $finish;
  end
endmodule
