// Optional sector buffer for apb_sd_spi (sim). Gowin: infer BSRAM, not registers.
module sd_spi_card_mem #(
  parameter int WORDS = 512
) (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [10:0] rd_addr,
  output logic [31:0] rd_data,
  input  logic [10:0] wr_addr,
  input  logic [31:0] wr_data,
  input  logic        wr_en
);
  localparam int ADDR_W = (WORDS <= 2) ? 1 : (WORDS <= 4) ? 2 : (WORDS <= 16) ? 4 : (WORDS <= 256) ? 8 : 11;

  (* ram_style = "block", syn_ramstyle = "block_ram" *)
  logic [31:0] mem [0:WORDS-1];

  always_ff @(posedge clk) begin
    if (!rst_n)
      rd_data <= 32'h0;
    else
      rd_data <= mem[rd_addr[ADDR_W-1:0]];
  end

  always_ff @(posedge clk) begin
    if (wr_en)
      mem[wr_addr[ADDR_W-1:0]] <= wr_data;
  end
endmodule
