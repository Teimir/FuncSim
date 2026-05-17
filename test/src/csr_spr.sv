// SPR: IRQ control (0–2) + read-only core identity (3–5). See docs/isa/cores.yaml.
module csr_spr #(
  parameter logic [31:0] CORE_INFO_VAL = 32'hE32C0100,
  parameter logic [31:0] ISA_REVISION_VAL = 32'h0001_0005,
  parameter logic [31:0] FEATURES_VAL = 32'h0000_000B
) (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [31:0] cur_pc,
  input  logic [31:0] irq_lines,
  input  logic        int_enable,
  input  logic        iret_exec,
  input  logic        irq_ack,
  input  logic        wr_en,
  input  logic [4:0]  wr_idx,
  input  logic [31:0] wr_data,
  input  logic [4:0]  rd_idx,
  output logic [31:0] rd_data,
  output logic        irq_pending,
  output logic [31:0] irq_vector,
  output logic [31:0] saved_irq_pc
);
  logic [31:0] spr_irq_vector;
  logic [31:0] spr_irq_mask;
  logic        in_service;
  logic [31:0] irq_active;

  assign irq_active  = irq_lines & ~spr_irq_mask;
  assign irq_pending = int_enable && !in_service && !iret_exec && (|irq_active);

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      spr_irq_vector <= 32'h0000_0100;
      spr_irq_mask   <= 32'h0;
      saved_irq_pc   <= 32'h0;
      irq_vector     <= 32'h0000_0100;
      in_service     <= 1'b0;
    end else begin
      if (iret_exec)
        in_service <= 1'b0;
      if (wr_en) begin
        case (wr_idx)
          5'd0: saved_irq_pc   <= wr_data;
          5'd1: spr_irq_vector <= wr_data;
          5'd2: spr_irq_mask   <= wr_data;
          default: ;
        endcase
      end
      if (irq_ack) begin
        in_service   <= 1'b1;
        saved_irq_pc <= cur_pc;
        irq_vector   <= spr_irq_vector;
      end
    end
  end

  always_comb begin
    case (rd_idx)
      5'd0: rd_data = saved_irq_pc;
      5'd1: rd_data = spr_irq_vector;
      5'd2: rd_data = spr_irq_mask;
      5'd3: rd_data = CORE_INFO_VAL;
      5'd4: rd_data = ISA_REVISION_VAL;
      5'd5: rd_data = FEATURES_VAL;
      default: rd_data = 32'h0;
    endcase
  end
endmodule
