module apb_gpio (
  input logic        pclk,
  input logic        presetn,
  input logic        psel,
  input logic        penable,
  input logic        pwrite,
  input logic [31:0] paddr,
  input logic [31:0] pwdata,
  output logic  [31:0] prdata,
  output logic        pready,
  output logic        pslverr,
  output logic  [31:0] gpio_out
);
  assign pready = 1'b1;
  assign pslverr = 1'b0;

  always_ff @(posedge pclk) begin
    if (!presetn) begin
      gpio_out <= 32'h0;
    end else if (psel && penable && pwrite && paddr[5:2] == 4'h0) begin
      gpio_out <= pwdata;
    end
  end

  always_comb begin
    if (paddr[5:2] == 4'h0) prdata = gpio_out;
    else prdata = 32'h0;
  end
endmodule
