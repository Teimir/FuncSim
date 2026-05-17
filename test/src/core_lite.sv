module e32c_core_lite (
  input logic        clk,
  input logic        rst_n,
  input logic        if_stall,
  output logic         if_req_valid,
  output logic  [31:0] if_req_addr,
  input logic        if_resp_valid,
  input logic [31:0] if_resp_data,
  input logic [31:0] irq_lines,
  output logic        d_awvalid,
  input logic        d_awready,
  output logic [31:0] d_awaddr,
  output logic        d_wvalid,
  input logic        d_wready,
  output logic [31:0] d_wdata,
  output logic [3:0]  d_wstrb,
  input logic        d_bvalid,
  output logic        d_bready,
  input logic [1:0]  d_bresp,
  output logic        d_arvalid,
  input logic        d_arready,
  output logic [31:0] d_araddr,
  input logic        d_rvalid,
  output logic        d_rready,
  input logic [31:0] d_rdata,
  input logic [1:0]  d_rresp,
  output logic  [31:0] dbg_pc,
  output logic         dbg_halted,
  output logic [31:0] dbg_r1,
  output logic [31:0] dbg_r2,
  output logic [31:0] dbg_r3,
  output logic [31:0] dbg_r4
);
  assign d_awvalid = 1'b0;
  assign d_awaddr  = 32'h0;
  assign d_wvalid  = 1'b0;
  assign d_wdata   = 32'h0;
  assign d_wstrb   = 4'h0;
  assign d_bready  = 1'b0;
  assign d_arvalid = 1'b0;
  assign d_araddr  = 32'h0;
  assign d_rready  = 1'b0;
  assign dbg_r1 = 32'h0;
  assign dbg_r2 = 32'h0;
  assign dbg_r3 = 32'h0;
  assign dbg_r4 = 32'h0;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      dbg_pc <= 32'h0;
      dbg_halted <= 1'b0;
      if_req_valid <= 1'b1;
      if_req_addr <= 32'h0;
    end else begin
      if_req_valid <= 1'b1;
      if_req_addr <= dbg_pc;
      if (if_resp_valid && if_resp_data == 32'hFFFF_FFFF) begin
        dbg_halted <= 1'b1;
        if_req_valid <= 1'b0;
      end else if (!if_stall) begin
        dbg_pc <= dbg_pc + 32'd4;
      end
    end
  end
endmodule
