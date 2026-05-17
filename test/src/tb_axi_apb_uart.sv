`timescale 1ns/1ps

module tb_axi_apb_uart;
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
  reg  uart_rx = 1'b1;
  wire sd_spi_sck, sd_spi_mosi, sd_spi_cs_n;
  wire soc_activity, illegal_instr, core_halted_obs, if_req_obs, if_resp_obs, if_stall_obs;
  wire [31:0] gpio_out_obs, core_pc_obs;
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
  `include "tb_axi_tasks.svh"

  localparam UART_TXDATA = `E32C_UART_BASE + 32'h0;
  localparam UART_STATUS = `E32C_UART_BASE + 32'h8;

  reg [31:0] status;
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

    fork
      begin
        #500000;
        $display("tb_axi_apb_uart global timeout");
        $finish(1);
      end
    join_none

    axi_read(UART_STATUS, status);
    if (status[1] !== 1'b1) begin
      $display("FAIL: TX should be idle after reset");
      $finish(1);
    end

    axi_write(UART_TXDATA, 32'h0000_0055);
    @(posedge clk);
    axi_read(UART_STATUS, status);
    if (status[1] !== 1'b0) begin
      $display("FAIL: expect TX busy after TXDATA write, status=%h", status);
      $finish(1);
    end

    begin : wait_idle
      integer k;
      for (k = 0; k < 50000; k = k + 1) begin
        axi_read(UART_STATUS, status);
        if (status[1] === 1'b1) disable wait_idle;
      end
      $display("FAIL: TX did not return idle");
      $finish(1);
    end

    // Back-to-back TXDATA writes must not drop bytes (blink_uart sends BL\\n).
    axi_write(UART_TXDATA, 32'h0000_0042);
    axi_write(UART_TXDATA, 32'h0000_004c);
    axi_write(UART_TXDATA, 32'h0000_000a);

    $display("tb_axi_apb_uart PASS");
    $finish;
  end
endmodule
