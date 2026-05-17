// Instruction ROM: 4 byte-wide block RAMs (Gowin BSRAM). Init via firmware_b0..b3.hex.
// Do not use $readmemh on a [31:0] array — Gowin infers ~50k+ DFF instead of BSRAM.
module instr_fetch_rom #(
  parameter integer WORDS = 128,
  parameter        INIT_B0 = "firmware_b0.hex",
  parameter        INIT_B1 = "firmware_b1.hex",
  parameter        INIT_B2 = "firmware_b2.hex",
  parameter        INIT_B3 = "firmware_b3.hex"
) (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        req_valid,
  input  logic [31:0] req_addr,
  output logic        resp_valid,
  output logic [31:0] resp_data
);
  localparam integer AW = (WORDS <= 1) ? 1 : $clog2(WORDS);
  localparam integer ADDR_MSB = AW + 1;

  (* ram_style = "block", syn_ramstyle = "block_ram" *) logic [7:0] mem_b0[0:WORDS-1];
  (* ram_style = "block", syn_ramstyle = "block_ram" *) logic [7:0] mem_b1[0:WORDS-1];
  (* ram_style = "block", syn_ramstyle = "block_ram" *) logic [7:0] mem_b2[0:WORDS-1];
  (* ram_style = "block", syn_ramstyle = "block_ram" *) logic [7:0] mem_b3[0:WORDS-1];

  logic [AW-1:0] idx_q;
  logic          pending;

  initial begin
    $readmemh(INIT_B0, mem_b0);
    $readmemh(INIT_B1, mem_b1);
    $readmemh(INIT_B2, mem_b2);
    $readmemh(INIT_B3, mem_b3);
  end

  // 2-cycle read; ignore held req_valid while pending (core keeps req high in ST_FETCH_WAIT).
  always_ff @(posedge clk) begin
    if (!rst_n) begin
      pending    <= 1'b0;
      resp_valid <= 1'b0;
      resp_data  <= 32'h0;
    end else begin
      resp_valid <= 1'b0;
      if (req_valid && !pending) begin
        idx_q   <= req_addr[ADDR_MSB:2];
        pending <= 1'b1;
      end else if (pending) begin
        resp_valid <= 1'b1;
        resp_data  <= {mem_b3[idx_q], mem_b2[idx_q], mem_b1[idx_q], mem_b0[idx_q]};
        pending    <= 1'b0;
      end
    end
  end
endmodule
