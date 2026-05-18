`timescale 1ns/1ps
// MOVs в r11–r15 (ADDI): после HALT значения в regs[] должны совпадать.

module tb_core_tn9k_mov_regs;
  localparam [5:0] OP_ADDI = 6'd48;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  wire        if_req_valid;
  wire [31:0] if_req_addr;
  reg         if_resp_valid;
  reg  [31:0] if_resp_data;
  wire        if_stall = 1'b0;

  wire [31:0] dbg_pc;
  wire        dbg_halted;
  wire [31:0] dbg_r11, dbg_r12, dbg_r13, dbg_r14, dbg_r15;

  reg [31:0] rom[0:5];
  reg [31:0] pending_addr;
  reg        pending_valid;

  function [31:0] rom_word(input [31:0] byte_addr);
    integer idx;
    begin
      idx = byte_addr[5:2];
      if (idx < 0 || idx > 5) rom_word = 32'h0;
      else rom_word = rom[idx];
    end
  endfunction

  function [31:0] enc_addi(input [4:0] rd, input [15:0] imm);
    enc_addi = (OP_ADDI << 26) | (5'd0 << 21) | (5'd0 << 16) | (rd << 11) | imm[10:0];
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
    .d_arvalid(),
    .d_arready(1'b0),
    .d_araddr(),
    .d_rvalid(1'b0),
    .d_rready(),
    .d_rdata(32'h0),
    .d_rresp(2'b00),
    .dbg_pc(dbg_pc),
    .dbg_halted(dbg_halted),
    .illegal_instr(),
    .dbg_r1(),
    .dbg_r2(),
    .dbg_r3(),
    .dbg_r4(),
    .dbg_r11(dbg_r11),
    .dbg_r12(dbg_r12),
    .dbg_r13(dbg_r13),
    .dbg_r14(dbg_r14),
    .dbg_r15(dbg_r15)
  );

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      if_resp_valid <= 1'b0;
      if_resp_data  <= 32'h0;
      pending_valid <= 1'b0;
      pending_addr  <= 32'h0;
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
    rom[0] = enc_addi(5'd11, 16'd72);
    rom[1] = enc_addi(5'd12, 16'd105);
    rom[2] = enc_addi(5'd13, 16'd33);
    rom[3] = enc_addi(5'd14, 16'd13);
    rom[4] = enc_addi(5'd15, 16'd10);
    rom[5] = 32'hFFFF_FFFF;

    #20 rst_n = 1;
    wait (dbg_halted === 1'b1);

    if (dbg_r11 !== 32'd72) begin
      $display("FAIL r11=%0d expected 72", dbg_r11);
      $finish(1);
    end
    if (dbg_r12 !== 32'd105) begin
      $display("FAIL r12=%0d expected 105", dbg_r12);
      $finish(1);
    end
    if (dbg_r13 !== 32'd33) begin
      $display("FAIL r13=%0d expected 33", dbg_r13);
      $finish(1);
    end
    if (dbg_r14 !== 32'd13) begin
      $display("FAIL r14=%0d expected 13", dbg_r14);
      $finish(1);
    end
    if (dbg_r15 !== 32'd10) begin
      $display("FAIL r15=%0d expected 10", dbg_r15);
      $finish(1);
    end
    $display("tb_core_tn9k_mov_regs PASS");
    $finish;
  end
endmodule
