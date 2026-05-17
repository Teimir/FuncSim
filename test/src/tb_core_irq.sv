`timescale 1ns/1ps

module tb_core_irq;
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

  soc_top #(
    .RAM_WORDS(512),
    .PSRAM_WORDS(512),
    .ENABLE_FW_BOOTLOAD(1'b0),
    .USE_READMEMH(1'b0)
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
    .uart_tx(uart_tx),
    .uart_rx(uart_rx)
  );

  `include "tb_axi_tasks.svh"
  `include "tb_psram_mem.svh"

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

    // NOP at reset; HALT at default IRQ vector 0x100 (csr_irq reset)
    psram_write_word(0, 32'h0000_0000);
    psram_write_word(1, 32'h0000_0000);
    psram_write_word(2, 32'h0000_0000);
    psram_write_word(64, 32'hFFFF_FFFF);

    #20 rst_n = 1;

    // Timer: low compare + IRQ enable
    axi_write(32'hFFFF_2008, 32'd20);
    axi_write(32'hFFFF_200C, 32'd0);
    axi_write(32'hFFFF_2010, 32'h1);

    repeat (300) @(posedge clk);
    if (!dut.g_core_full.u_core.dbg_halted) begin
      $display("core did not halt via IRQ vector, pc=%h", dut.g_core_full.u_core.dbg_pc);
      $finish(1);
    end

    $display("tb_core_irq PASS");
    $finish;
  end
endmodule
