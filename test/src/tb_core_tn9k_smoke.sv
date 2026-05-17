`timescale 1ns/1ps
// Smoke: core_tn9k ALU + BJ + MUL illegal (IF model = 1-cycle ROM in TB).
module tb_core_tn9k_smoke;
  localparam [5:0] OP_MUL     = 6'd44;
  localparam [5:0] OP_ADDS    = 6'd35;
  localparam [5:0] OP_BJ      = 6'd24;
  localparam [5:0] OP_READSPR = 6'd52;
  localparam [31:0] EXPECT_CORE_INFO = 32'hE32C0110;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  wire        if_req_valid;
  wire [31:0] if_req_addr;
  reg         if_resp_valid;
  reg  [31:0] if_resp_data;
  wire        if_stall = 1'b0;

  wire illegal_instr;
  wire [31:0] dbg_pc;
  wire [31:0] dbg_r1;
  wire [31:0] dbg_r2;

  reg [31:0] rom[0:9];
  reg [31:0] pending_addr;
  reg        pending_valid;

  function [31:0] rom_word(input [31:0] byte_addr);
    integer idx;
    begin
      idx = byte_addr[5:2];
      if (idx < 0 || idx > 9) rom_word = 32'h0;
      else rom_word = rom[idx];
    end
  endfunction

  e32c_core_tn9k dut (
    .clk(clk),
    .rst_n(rst_n),
    .if_stall(if_stall),
    .if_req_valid(if_req_valid),
    .if_req_addr(if_req_addr),
    .if_resp_valid(if_resp_valid),
    .if_resp_data(if_resp_data),
    .irq_lines(32'h0),
    .d_awvalid(),
    .d_awready(1'b0),
    .d_awaddr(),
    .d_wvalid(),
    .d_wready(1'b0),
    .d_wdata(),
    .d_wstrb(),
    .d_bvalid(1'b0),
    .d_bready(),
    .d_bresp(2'b00),
    .d_arvalid(),
    .d_arready(1'b0),
    .d_araddr(),
    .d_rvalid(1'b0),
    .d_rready(),
    .d_rdata(32'h0),
    .d_rresp(2'b00),
    .dbg_pc(dbg_pc),
    .dbg_halted(),
    .illegal_instr(illegal_instr),
    .dbg_r1(dbg_r1),
    .dbg_r2(dbg_r2),
    .dbg_r3(),
    .dbg_r4()
  );

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      if_resp_valid  <= 1'b0;
      if_resp_data   <= 32'h0;
      pending_valid  <= 1'b0;
      pending_addr   <= 32'h0;
    end else begin
      if_resp_valid <= 1'b0;
      if (pending_valid) begin
        if_resp_valid <= 1'b1;
        if_resp_data  <= rom_word(pending_addr);
        pending_valid <= 1'b0;
      end
      if (if_req_valid) begin
        pending_valid <= 1'b1;
        pending_addr  <= if_req_addr;
      end
    end
  end

  initial begin
    // ADDS r1, r0, r0  -> r1 = 0, Z=1
    rom[0] = (OP_ADDS << 26) | (5'd0 << 21) | (5'd0 << 16) | (5'd1 << 11);
    // BJ EQ r0, +16  -> skip MUL @ 0x8, land @ 0x10 HALT
    rom[1] = (OP_BJ << 26) | (4'd0 << 22) | (5'd0 << 17) | (11'd16 << 6);
    // MUL (illegal on TN9K)
    rom[2] = (OP_MUL << 26) | (5'd1 << 21) | (5'd2 << 16) | (5'd3 << 11);
    rom[3] = 32'h0;
    // READSPR r2, 3  @ 0x10
    rom[4] = (OP_READSPR << 26) | (5'd2 << 21) | (5'd3 << 11);
    rom[5] = 32'h0;
    rom[6] = 32'hFFFF_FFFF;  // HALT @ 0x18

    #30 rst_n = 1;
    repeat (400) @(posedge clk);
    if (dbg_r1 !== 32'h0) begin
      $display("FAIL: r1=%h expected 0", dbg_r1);
      $finish(1);
    end
    if (dbg_pc !== 32'h18) begin
      $display("FAIL: pc=%h expected 18 (BJ skip + READSPR + HALT)", dbg_pc);
      $finish(1);
    end
    if (dbg_r2 !== EXPECT_CORE_INFO) begin
      $display("FAIL: r2=%h expected CORE_INFO %h", dbg_r2, EXPECT_CORE_INFO);
      $finish(1);
    end
    if (illegal_instr) begin
      $display("FAIL: illegal_instr set (BJ should skip MUL)");
      $finish(1);
    end
    $display("tb_core_tn9k_smoke PASS");
    $finish;
  end
endmodule
