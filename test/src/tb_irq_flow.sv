`timescale 1ns/1ps

module tb_irq_flow;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg        irq0;
  reg        int_en;
  reg        iret;
  reg        ack;
  reg [31:0] cur_pc;
  wire       pending;
  wire [31:0] vec;
  wire [31:0] saved;

  csr_irq dut (
    .clk(clk),
    .rst_n(rst_n),
    .cur_pc(cur_pc),
    .irq_lines({31'b0, irq0}),
    .int_enable(int_en),
    .iret_exec(iret),
    .irq_ack(ack),
    .wr_en(1'b0),
    .wr_idx(2'b00),
    .wr_data(32'h0),
    .rd_idx(2'b00),
    .rd_data(),
    .irq_pending(pending),
    .irq_vector(vec),
    .saved_irq_pc(saved)
  );

  initial begin
    irq0 = 0;
    int_en = 1;
    iret = 0;
    ack = 0;
    cur_pc = 32'h40;
    #20 rst_n = 1;
    @(posedge clk);
    if (vec !== 32'h100) begin
      $display("FAIL default vector %h", vec);
      $finish(1);
    end
    irq0 <= 1;
    @(posedge clk);
    if (!pending) begin
      $display("FAIL no pending on level irq");
      $finish(1);
    end
    ack <= 1;
    @(posedge clk);
    ack <= 0;
    if (saved !== 32'h40) begin
      $display("FAIL saved %h", saved);
      $finish(1);
    end
    if (!pending) begin
      $display("FAIL pending cleared while irq high and in_service");
      $finish(1);
    end
    iret <= 1;
    @(posedge clk);
    iret <= 0;
    irq0 <= 0;
    @(posedge clk);
    if (pending) begin
      $display("FAIL pending after iret with irq low");
      $finish(1);
    end
    irq0 <= 1;
    @(posedge clk);
    if (!pending) begin
      $display("FAIL no second pending after iret");
      $finish(1);
    end
    $display("tb_irq_flow PASS");
    $finish;
  end
endmodule
