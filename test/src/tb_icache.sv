`timescale 1ns/1ps

module tb_icache;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg         req_valid;
  reg  [31:0] req_addr;
  wire        stall;
  wire        resp_valid;
  wire [31:0] resp_data;

  wire        m_arvalid;
  reg         m_arready;
  wire [31:0] m_araddr;
  reg         m_rvalid;
  wire        m_rready;
  reg  [31:0] m_rdata;
  reg  [1:0]  m_rresp;

  icache #(
    .LINE_WORDS(4),
    .NUM_LINES(8)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .req_valid(req_valid),
    .req_addr(req_addr),
    .stall(stall),
    .resp_valid(resp_valid),
    .resp_data(resp_data),
    .m_arvalid(m_arvalid),
    .m_arready(m_arready),
    .m_araddr(m_araddr),
    .m_rvalid(m_rvalid),
    .m_rready(m_rready),
    .m_rdata(m_rdata),
    .m_rresp(m_rresp)
  );

  initial begin
    req_valid = 0; req_addr = 0;
    m_arready = 0; m_rvalid = 0; m_rdata = 0; m_rresp = 2'b00;
    #20 rst_n = 1;

    // First access: miss/refill
    @(posedge clk);
    req_addr <= 32'h0000_0040;
    req_valid <= 1;
    wait (m_arvalid);
    m_arready <= 1;
    @(posedge clk);
    m_arready <= 0;
    m_rdata <= 32'hDEAD_BEEF;
    m_rvalid <= 1;
    wait (m_rready);
    @(posedge clk);
    m_rvalid <= 0;
    wait (resp_valid);
    if (resp_data !== 32'hDEAD_BEEF) begin $display("Miss refill value mismatch"); $finish(1); end

    // Second access: hit
    @(posedge clk);
    req_addr <= 32'h0000_0040;
    wait (resp_valid);
    if (resp_data !== 32'hDEAD_BEEF) begin $display("Hit value mismatch"); $finish(1); end
    req_valid <= 0;
    $display("tb_icache PASS");
    $finish;
  end
endmodule
