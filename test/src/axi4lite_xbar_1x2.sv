module axi4lite_xbar_1x2 (
  input logic        clk,
  input logic        rst_n,
  input logic        m_awvalid,
  output logic        m_awready,
  input logic [31:0] m_awaddr,
  input logic        m_wvalid,
  output logic        m_wready,
  input logic [31:0] m_wdata,
  input logic [3:0]  m_wstrb,
  output logic        m_bvalid,
  input logic        m_bready,
  output logic [1:0]  m_bresp,
  input logic        m_arvalid,
  output logic        m_arready,
  input logic [31:0] m_araddr,
  output logic        m_rvalid,
  input logic        m_rready,
  output logic [31:0] m_rdata,
  output logic [1:0]  m_rresp,
  output logic        s0_awvalid,
  input logic        s0_awready,
  output logic [31:0] s0_awaddr,
  output logic        s0_wvalid,
  input logic        s0_wready,
  output logic [31:0] s0_wdata,
  output logic [3:0]  s0_wstrb,
  input logic        s0_bvalid,
  output logic        s0_bready,
  input logic [1:0]  s0_bresp,
  output logic        s0_arvalid,
  input logic        s0_arready,
  output logic [31:0] s0_araddr,
  input logic        s0_rvalid,
  output logic        s0_rready,
  input logic [31:0] s0_rdata,
  input logic [1:0]  s0_rresp,
  output logic        s1_awvalid,
  input logic        s1_awready,
  output logic [31:0] s1_awaddr,
  output logic        s1_wvalid,
  input logic        s1_wready,
  output logic [31:0] s1_wdata,
  output logic [3:0]  s1_wstrb,
  input logic        s1_bvalid,
  output logic        s1_bready,
  input logic [1:0]  s1_bresp,
  output logic        s1_arvalid,
  input logic        s1_arready,
  output logic [31:0] s1_araddr,
  input logic        s1_rvalid,
  output logic        s1_rready,
  input logic [31:0] s1_rdata,
  input logic [1:0]  s1_rresp
);
`include "mmio_generated.svh"
  logic wr_to_apb;
  logic rd_to_apb;
  assign wr_to_apb = (m_awaddr[31:16] == `E32C_MMIO_AXI_HIGH);
  assign rd_to_apb = (m_araddr[31:16] == `E32C_MMIO_AXI_HIGH);

  assign s0_awvalid = m_awvalid && !wr_to_apb;
  assign s0_awaddr = m_awaddr;
  assign s0_wvalid = m_wvalid && !wr_to_apb;
  assign s0_wdata = m_wdata;
  assign s0_wstrb = m_wstrb;
  assign s0_arvalid = m_arvalid && !rd_to_apb;
  assign s0_araddr = m_araddr;
  assign s0_bready = m_bready && !wr_to_apb;
  assign s0_rready = m_rready && !rd_to_apb;

  assign s1_awvalid = m_awvalid && wr_to_apb;
  assign s1_awaddr = m_awaddr;
  assign s1_wvalid = m_wvalid && wr_to_apb;
  assign s1_wdata = m_wdata;
  assign s1_wstrb = m_wstrb;
  assign s1_arvalid = m_arvalid && rd_to_apb;
  assign s1_araddr = m_araddr;
  assign s1_bready = m_bready && wr_to_apb;
  assign s1_rready = m_rready && rd_to_apb;

  assign m_awready = wr_to_apb ? s1_awready : s0_awready;
  assign m_wready = wr_to_apb ? s1_wready : s0_wready;
  assign m_bvalid = wr_to_apb ? s1_bvalid : s0_bvalid;
  assign m_bresp = wr_to_apb ? s1_bresp : s0_bresp;
  assign m_arready = rd_to_apb ? s1_arready : s0_arready;
  assign m_rvalid = rd_to_apb ? s1_rvalid : s0_rvalid;
  assign m_rdata = rd_to_apb ? s1_rdata : s0_rdata;
  assign m_rresp = rd_to_apb ? s1_rresp : s0_rresp;
endmodule
