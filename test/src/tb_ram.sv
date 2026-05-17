`timescale 1ns/1ps

module tb_ram;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg         awvalid;
  wire        awready;
  reg  [31:0] awaddr;
  reg         wvalid;
  wire        wready;
  reg  [31:0] wdata;
  reg  [3:0]  wstrb;
  wire        bvalid;
  reg         bready;
  wire [1:0]  bresp;
  reg         arvalid;
  wire        arready;
  reg  [31:0] araddr;
  wire        rvalid;
  reg         rready;
  wire [31:0] rdata;
  wire [1:0]  rresp;

  axi4lite_ram #(
    .MEM_WORDS(256),
    .BASE_ADDR(32'h0000_0000)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .s_awvalid(awvalid),
    .s_awready(awready),
    .s_awaddr(awaddr),
    .s_wvalid(wvalid),
    .s_wready(wready),
    .s_wdata(wdata),
    .s_wstrb(wstrb),
    .s_bvalid(bvalid),
    .s_bready(bready),
    .s_bresp(bresp),
    .s_arvalid(arvalid),
    .s_arready(arready),
    .s_araddr(araddr),
    .s_rvalid(rvalid),
    .s_rready(rready),
    .s_rdata(rdata),
    .s_rresp(rresp)
  );

  initial begin
    awvalid = 0; awaddr = 0; wvalid = 0; wdata = 0; wstrb = 4'h0;
    bready = 0; arvalid = 0; araddr = 0; rready = 0;
    #20 rst_n = 1;

    @(posedge clk);
    awaddr <= 32'h0000_0010;
    wdata <= 32'hA5A5_1234;
    wstrb <= 4'hF;
    awvalid <= 1;
    wvalid <= 1;
    bready <= 1;
    wait (awready && wready);
    @(posedge clk);
    awvalid <= 0;
    wvalid <= 0;
    wait (bvalid);
    if (bresp !== 2'b00) begin $display("Write response not OKAY"); $finish(1); end
    @(posedge clk);
    bready <= 0;

    @(posedge clk);
    araddr <= 32'h0000_0010;
    arvalid <= 1;
    rready <= 1;
    wait (arready);
    @(posedge clk) arvalid <= 0;
    wait (rvalid);
    if (rresp !== 2'b00) begin $display("Read response not OKAY"); $finish(1); end
    if (rdata !== 32'hA5A5_1234) begin $display("Readback mismatch: %h", rdata); $finish(1); end

    $display("tb_ram PASS");
    $finish;
  end
endmodule
