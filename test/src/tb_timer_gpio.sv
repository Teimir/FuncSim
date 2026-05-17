`timescale 1ns/1ps

module tb_timer_gpio;
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
  reg  uart_rx = 1'b1;
soc_top #(.RAM_WORDS(1024), .PSRAM_WORDS(1024)) dut (
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
    .uart_rx(uart_rx)
  );
  `include "tb_axi_tasks.svh"
  `include "tb_psram_mem.svh"

  reg [31:0] d;
  initial begin
    m_awvalid = 0;
    m_wvalid = 0;
    m_bready = 0;
    m_arvalid = 0;
    m_rready = 0;
    m_awaddr = 0;
    m_araddr = 0;
    m_wdata = 0;
    m_wstrb = 0;

    psram_write_word(0, 32'hFFFF_FFFF);

    #20 rst_n = 1;

    axi_write(32'hFFFF_0000, 32'h0000_00AA);
    axi_write(32'hFFFF_2008, 32'd20);
    axi_write(32'hFFFF_200C, 32'd0);
    axi_write(32'hFFFF_2010, 32'h1);
    repeat (40) @(posedge clk);
    axi_read(32'hFFFF_2010, d);
    axi_read(32'hFFFF_0000, d);
    if (d[7:0] !== 8'hAA) begin
      $display("GPIO readback mismatch: %h", d);
      $finish(1);
    end

    $display("tb_timer_gpio PASS");
    $finish;
  end
endmodule
