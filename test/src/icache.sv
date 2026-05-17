// AXI instruction-fetch bridge (no tag RAM). Stall until read data returns.
module icache #(
  parameter integer LINE_WORDS = 4,
  parameter integer NUM_LINES = 16
) (
  input logic        clk,
  input logic        rst_n,
  input logic        req_valid,
  input logic [31:0] req_addr,
  output logic        stall,
  output logic         resp_valid,
  output logic  [31:0] resp_data,
  output logic         m_arvalid,
  input logic        m_arready,
  output logic  [31:0] m_araddr,
  input logic        m_rvalid,
  output logic        m_rready,
  input logic [31:0] m_rdata,
  input logic [1:0]  m_rresp
);
  logic pending;
  assign stall = req_valid && (pending || m_arvalid);
  assign m_rready = 1'b1;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      resp_valid <= 1'b0;
      resp_data <= 32'h0;
      m_arvalid <= 1'b0;
      m_araddr <= 32'h0;
      pending <= 1'b0;
    end else begin
      resp_valid <= 1'b0;

      if (req_valid && !pending && !m_arvalid) begin
        m_arvalid <= 1'b1;
        m_araddr <= {req_addr[31:2], 2'b00};
      end

      if (m_arvalid && m_arready) begin
        m_arvalid <= 1'b0;
        pending <= 1'b1;
      end

      if (pending && m_rvalid) begin
        if (m_rresp == 2'b00) begin
          resp_data <= m_rdata;
          resp_valid <= 1'b1;
        end
        pending <= 1'b0;
      end
    end
  end
endmodule
