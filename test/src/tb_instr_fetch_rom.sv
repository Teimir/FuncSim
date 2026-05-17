`timescale 1ns/1ps

module tb_instr_fetch_rom;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg         req_valid;
  reg  [31:0] req_addr;
  wire        resp_valid;
  wire [31:0] resp_data;

  instr_fetch_rom #(.WORDS(128)) dut (
    .clk(clk),
    .rst_n(rst_n),
    .req_valid(req_valid),
    .req_addr(req_addr),
    .resp_valid(resp_valid),
    .resp_data(resp_data)
  );

  initial begin
    req_valid = 1'b0;
    req_addr  = 32'h0;
    #12 rst_n = 1;

  // word 0 from blink_uart_irq image (ADDI r0, r21, 256 after asm layout — non-zero)
    req_valid = 1'b1;
    req_addr  = 32'h0;
    @(posedge clk);
    req_valid = 1'b1;
    @(posedge clk);
    @(posedge clk);
    if (!resp_valid) begin
      $display("FAIL: no resp @0");
      $finish(1);
    end
    if (resp_data == 32'h0) begin
      $display("FAIL: word0 zero");
      $finish(1);
    end

    req_valid = 1'b0;
    @(posedge clk);
    req_valid = 1'b1;
    req_addr  = 32'h100;
    @(posedge clk);
    req_valid = 1'b1;
    @(posedge clk);
    @(posedge clk);
    if (!resp_valid) begin
      $display("FAIL: no resp @0x100");
      $finish(1);
    end

    $display("tb_instr_fetch_rom PASS");
    $finish;
  end
endmodule
