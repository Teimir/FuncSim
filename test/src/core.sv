`include "cores_generated.svh"

module e32c_core (
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
  output logic         illegal_instr,
  output logic [31:0] dbg_r1,
  output logic [31:0] dbg_r2,
  output logic [31:0] dbg_r3,
  output logic [31:0] dbg_r4
);
  localparam [5:0] OP_LDR      = 6'd1;
  localparam [5:0] OP_STR      = 6'd2;
  localparam [5:0] OP_ROL      = 6'd3;
  localparam [5:0] OP_LDRPRE   = 6'd5;
  localparam [5:0] OP_STRPRE   = 6'd6;
  localparam [5:0] OP_LDREX    = 6'd7;
  localparam [5:0] OP_SMUL     = 6'd4;
  localparam [5:0] OP_UMULL    = 6'd8;   // excluded: treated as NOP
  localparam [5:0] OP_SMULL    = 6'd9;   // excluded: treated as NOP
  localparam [5:0] OP_MLA      = 6'd10;  // excluded: treated as NOP
  localparam [5:0] OP_BIC      = 6'd11;
  localparam [5:0] OP_MVN      = 6'd12;
  localparam [5:0] OP_NEG      = 6'd13;
  localparam [5:0] OP_ANDS     = 6'd14;
  localparam [5:0] OP_ROR      = 6'd15;
  localparam [5:0] OP_JMP      = 6'd16;
  localparam [5:0] OP_JZ       = 6'd17;
  localparam [5:0] OP_JNZ      = 6'd18;
  localparam [5:0] OP_JC       = 6'd19;
  localparam [5:0] OP_JS       = 6'd20;
  localparam [5:0] OP_JO       = 6'd21;
  localparam [5:0] OP_LDRPOST  = 6'd22;
  localparam [5:0] OP_STRPOST  = 6'd23;
  localparam [5:0] OP_BJ       = 6'd24;
  localparam [5:0] OP_WRITESPR = 6'd25;
  localparam [5:0] OP_ADDSI    = 6'd26;
  localparam [5:0] OP_SUBSI    = 6'd27;
  localparam [5:0] OP_ADC      = 6'd28;
  localparam [5:0] OP_ADCS     = 6'd29;
  localparam [5:0] OP_SBC      = 6'd30;
  localparam [5:0] OP_SBCS     = 6'd31;
  localparam [5:0] OP_ADD      = 6'd33;
  localparam [5:0] OP_SUB      = 6'd34;
  localparam [5:0] OP_ADDS     = 6'd35;
  localparam [5:0] OP_SUBS     = 6'd36;
  localparam [5:0] OP_AND      = 6'd37;
  localparam [5:0] OP_OR       = 6'd38;
  localparam [5:0] OP_XOR      = 6'd39;
  localparam [5:0] OP_SLL      = 6'd40;
  localparam [5:0] OP_SLR      = 6'd41;
  localparam [5:0] OP_SAL      = 6'd42;
  localparam [5:0] OP_MUL      = 6'd44;
  localparam [5:0] OP_STREX    = 6'd32;
  localparam [5:0] OP_ADDI     = 6'd48;
  localparam [5:0] OP_SUBI     = 6'd49;
  localparam [5:0] OP_EI       = 6'd50;
  localparam [5:0] OP_DI       = 6'd51;
  localparam [5:0] OP_READSPR  = 6'd52;
  localparam [5:0] OP_IRET     = 6'd62;

  localparam [2:0] ST_FETCH_REQ  = 3'd0;
  localparam [2:0] ST_FETCH_WAIT = 3'd1;
  localparam [2:0] ST_EXEC       = 3'd2;
  localparam [2:0] ST_MEM_RD_REQ = 3'd3;
  localparam [2:0] ST_MEM_RD_WAIT= 3'd4;
  localparam [2:0] ST_MEM_WR_REQ = 3'd5;
  localparam [2:0] ST_MEM_WR_WAIT= 3'd6;

  logic [2:0] st;
  logic [31:0] regs [0:31];
  logic [31:0] ir;
  logic int_enable;
  logic zf, cf, vf, sf;
  logic d_awvalid_r, d_wvalid_r, d_bready_r, d_arvalid_r, d_rready_r;
  logic [31:0] d_awaddr_r, d_wdata_r, d_araddr_r;
  logic [3:0] d_wstrb_r;
  logic [4:0] mem_reg_idx, mem_addr_reg_idx;
  logic [3:0] mem_mask;
  logic mem_is_post;
  logic mem_pre_update;
  logic mem_is_strex;
  logic [4:0] mem_strex_status;
  logic [31:0] mem_post_val;
  logic [31:0] exclusive_addr;
  logic exclusive_valid;
  logic [4:0] mul_resh;
  logic [63:0] mul_u_prod;
  logic [63:0] mul_s_prod;

  logic csr_wr_en;
  logic [4:0] csr_wr_idx;
  logic [31:0] csr_wr_data;
  logic [4:0] csr_rd_idx;
  logic [4:0] csr_rd_idx_eff;
  logic [31:0] csr_rd_data;
  logic irq_pending;
  logic irq_ack_r;
  logic [31:0] irq_vector;
  logic [31:0] saved_irq_pc;

  logic [4:0] r1, r2, rd, bj_raddr;
  logic [5:0] op;
  logic [3:0] cond;
  logic [31:0] a, b;
  logic [15:0] imm16;
  logic [10:0] imm11, bj_imm11;
  logic [31:0] imm16_sext;
  logic [31:0] imm11_sext;
  logic [31:0] res;
  logic [31:0] rhs;
  logic [32:0] sum33;
  logic take_branch;
  logic illegal_instr_r;
  integer i;

  always_comb begin
    r1 = ir[25:21];
    r2 = ir[20:16];
    rd = ir[15:11];
    bj_raddr = ir[21:17];
    op = ir[31:26];
    cond = ir[25:22];
    a = regs[r1];
    b = regs[r2];
    imm16 = {ir[20:16], ir[10:0]};
    imm11 = ir[10:0];
    bj_imm11 = ir[16:6];
    imm16_sext = {{16{imm16[15]}}, imm16};
    imm11_sext = {{21{imm11[10]}}, imm11};
    res = 32'h0;
    case (op)
      OP_ADD:  res = a + b;
      OP_SUB:  res = a - b;
      OP_AND:  res = a & b;
      OP_OR:   res = a | b;
      OP_XOR:  res = a ^ b;
      OP_ADDI: res = a + imm16_sext;
      OP_SUBI: res = a - imm16_sext;
      OP_BIC:  res = a & ~b;
      OP_MVN:  res = ~b;
      OP_NEG:  res = (~b) + 1;
      OP_SLL, OP_SAL: res = a << b[4:0];
      OP_SLR:  res = a >> b[4:0];
      OP_ROL:  res = (b[4:0] == 0) ? a : ((a << b[4:0]) | (a >> (6'd32 - b[4:0])));
      OP_ROR:  res = (b[4:0] == 0) ? a : ((a >> b[4:0]) | (a << (6'd32 - b[4:0])));
      default: res = 32'h0;
    endcase
  end

  assign d_awvalid = d_awvalid_r;
  assign d_awaddr  = d_awaddr_r;
  assign d_wvalid  = d_wvalid_r;
  assign d_wdata   = d_wdata_r;
  assign d_wstrb   = d_wstrb_r;
  assign d_bready  = d_bready_r;
  assign d_arvalid = d_arvalid_r;
  assign d_araddr  = d_araddr_r;
  assign d_rready  = d_rready_r;

  assign dbg_r1 = regs[1];
  assign dbg_r2 = regs[2];
  assign dbg_r3 = regs[3];
  assign dbg_r4 = regs[4];
  assign illegal_instr = illegal_instr_r;

  wire iret_exec = (st == ST_EXEC) && (op == OP_IRET) && (ir != 32'hFFFF_FFFF);

  assign mul_resh = ir[10:6];
  e32c_mul_u_dsp u_mul_u(.a(a), .b(b), .p(mul_u_prod));
  e32c_mul_s_dsp u_mul_s(.a(a), .b(b), .p(mul_s_prod));

  assign irq_ack_r = irq_pending && (st == ST_FETCH_REQ) && !if_stall && !dbg_halted;
  assign csr_rd_idx_eff =
      (st == ST_EXEC && op == OP_READSPR) ? ir[15:11] : csr_rd_idx;

  csr_spr #(
    .CORE_INFO_VAL(E32C_CORE_INFO_FULL),
    .ISA_REVISION_VAL(E32C_ISA_REVISION),
    .FEATURES_VAL(E32C_FEATURES_FULL)
  ) u_csr_spr (
    .clk(clk), .rst_n(rst_n), .cur_pc(dbg_pc), .irq_lines(irq_lines),
    .int_enable(int_enable), .iret_exec(iret_exec), .irq_ack(irq_ack_r),
    .wr_en(csr_wr_en), .wr_idx(csr_wr_idx), .wr_data(csr_wr_data),
    .rd_idx(csr_rd_idx_eff), .rd_data(csr_rd_data), .irq_pending(irq_pending),
    .irq_vector(irq_vector), .saved_irq_pc(saved_irq_pc)
  );

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      dbg_pc <= 32'h0;
      dbg_halted <= 1'b0;
      illegal_instr_r <= 1'b0;
      int_enable <= 1'b1;
      zf <= 1'b0;
      cf <= 1'b0;
      vf <= 1'b0;
      sf <= 1'b0;
      if_req_valid <= 1'b0;
      if_req_addr <= 32'h0;
      ir <= 32'h0;
      st <= ST_FETCH_REQ;
      d_awvalid_r <= 1'b0;
      d_wvalid_r <= 1'b0;
      d_bready_r <= 1'b0;
      d_arvalid_r <= 1'b0;
      d_rready_r <= 1'b0;
      d_awaddr_r <= 32'h0;
      d_wdata_r <= 32'h0;
      d_araddr_r <= 32'h0;
      d_wstrb_r <= 4'hF;
      mem_reg_idx <= 5'd0;
      mem_addr_reg_idx <= 5'd0;
      mem_mask <= 4'h0;
      mem_is_post <= 1'b0;
      mem_pre_update <= 1'b0;
      mem_is_strex <= 1'b0;
      mem_strex_status <= 5'd0;
      mem_post_val <= 32'h0;
      exclusive_addr <= 32'h0;
      exclusive_valid <= 1'b0;
      csr_wr_en <= 1'b0;
      csr_wr_idx <= 5'b0;
      csr_wr_data <= 32'h0;
      csr_rd_idx <= 5'b0;
      for (i = 0; i < 32; i = i + 1) regs[i] <= 32'h0;
    end else begin
      csr_wr_en <= 1'b0;
      regs[0] <= 32'h0;
      case (st)
        ST_FETCH_REQ: begin
          if_req_valid <= !dbg_halted;
          d_awvalid_r <= 1'b0;
          d_wvalid_r <= 1'b0;
          d_bready_r <= 1'b0;
          d_arvalid_r <= 1'b0;
          d_rready_r <= 1'b0;
          if (!if_stall && !dbg_halted) begin
            if (irq_pending) begin
              dbg_pc <= irq_vector;
              if_req_addr <= irq_vector;
            end else begin
              if_req_addr <= dbg_pc;
            end
            st <= ST_FETCH_WAIT;
          end
        end
        ST_FETCH_WAIT: begin
          if_req_valid <= !dbg_halted;
          if (if_resp_valid) begin
            ir <= if_resp_data;
            st <= ST_EXEC;
          end
        end
        ST_EXEC: begin
          if_req_valid <= 1'b0;
          if (ir == 32'hFFFF_FFFF) begin
            dbg_halted <= 1'b1;
            st <= ST_FETCH_REQ;
          end else begin
            case (op)
              OP_SMUL: begin
                if (rd != 5'd0) regs[rd] <= mul_s_prod[31:0];
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_MUL, OP_UMULL: begin
                if (rd != 5'd0) regs[rd] <= mul_u_prod[31:0];
                if (mul_resh != 5'd0) regs[mul_resh] <= mul_u_prod[63:32];
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_SMULL: begin
                if (rd != 5'd0) regs[rd] <= mul_s_prod[31:0];
                if (mul_resh != 5'd0) regs[mul_resh] <= mul_s_prod[63:32];
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_MLA: begin
                if (rd != 5'd0) regs[rd] <= mul_u_prod[31:0] + regs[ir[15:11]];
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_JMP: begin
                dbg_pc <= a + imm11_sext;
                st <= ST_FETCH_REQ;
              end
              OP_JZ: begin
                dbg_pc <= zf ? (a + imm11_sext) : (dbg_pc + 32'd4);
                st <= ST_FETCH_REQ;
              end
              OP_JNZ: begin
                dbg_pc <= (!zf) ? (a + imm11_sext) : (dbg_pc + 32'd4);
                st <= ST_FETCH_REQ;
              end
              OP_JC: begin
                dbg_pc <= cf ? (a + imm11_sext) : (dbg_pc + 32'd4);
                st <= ST_FETCH_REQ;
              end
              OP_JS: begin
                dbg_pc <= sf ? (a + imm11_sext) : (dbg_pc + 32'd4);
                st <= ST_FETCH_REQ;
              end
              OP_JO: begin
                dbg_pc <= vf ? (a + imm11_sext) : (dbg_pc + 32'd4);
                st <= ST_FETCH_REQ;
              end
              OP_BJ: begin
                take_branch = 1'b0;
                case (cond)
                  4'd0: take_branch = zf;
                  4'd1: take_branch = !zf;
                  4'd2: take_branch = cf;
                  4'd3: take_branch = !cf;
                  4'd4: take_branch = sf;
                  4'd5: take_branch = !sf;
                  4'd6: take_branch = vf;
                  4'd7: take_branch = !vf;
                  4'd8: take_branch = cf && !zf;
                  4'd9: take_branch = !cf || zf;
                  4'd10: take_branch = (sf == vf);
                  4'd11: take_branch = (sf != vf);
                  4'd12: take_branch = !zf && (sf == vf);
                  4'd13: take_branch = zf || (sf != vf);
                  4'd14: take_branch = 1'b1;
                  default: take_branch = 1'b0;
                endcase
                dbg_pc <= take_branch ? (regs[bj_raddr] + {{21{bj_imm11[10]}}, bj_imm11}) : (dbg_pc + 32'd4);
                st <= ST_FETCH_REQ;
              end
              OP_LDR: begin
                exclusive_valid <= 1'b0;
                d_arvalid_r <= 1'b1;
                d_araddr_r <= a + imm11_sext;
                d_rready_r <= 1'b1;
                mem_reg_idx <= r2;
                mem_addr_reg_idx <= r1;
                mem_mask <= ir[14:11];
                mem_is_post <= 1'b0;
                mem_pre_update <= 1'b0;
                mem_post_val <= a + imm11_sext;
                st <= ST_MEM_RD_REQ;
              end
              OP_LDRPRE: begin
                exclusive_valid <= 1'b0;
                d_arvalid_r <= 1'b1;
                d_araddr_r <= a + imm11_sext;
                d_rready_r <= 1'b1;
                mem_reg_idx <= r2;
                mem_addr_reg_idx <= r1;
                mem_mask <= ir[14:11];
                mem_is_post <= 1'b0;
                mem_pre_update <= 1'b1;
                mem_post_val <= a + imm11_sext;
                st <= ST_MEM_RD_REQ;
              end
              OP_LDREX: begin
                exclusive_addr <= a + imm11_sext;
                exclusive_valid <= 1'b1;
                d_arvalid_r <= 1'b1;
                d_araddr_r <= a + imm11_sext;
                d_rready_r <= 1'b1;
                mem_reg_idx <= r2;
                mem_addr_reg_idx <= r1;
                mem_mask <= ir[14:11];
                mem_is_post <= 1'b0;
                mem_pre_update <= 1'b0;
                mem_post_val <= a + imm11_sext;
                st <= ST_MEM_RD_REQ;
              end
              OP_LDRPOST: begin
                exclusive_valid <= 1'b0;
                d_arvalid_r <= 1'b1;
                d_araddr_r <= a;
                d_rready_r <= 1'b1;
                mem_reg_idx <= r2;
                mem_addr_reg_idx <= r1;
                mem_mask <= ir[14:11];
                mem_is_post <= 1'b1;
                mem_post_val <= a + imm11_sext;
                st <= ST_MEM_RD_REQ;
              end
              OP_STR: begin
                exclusive_valid <= 1'b0;
                d_awvalid_r <= 1'b1;
                d_awaddr_r <= a + imm11_sext;
                d_wvalid_r <= 1'b1;
                d_wdata_r <= b;
                d_wstrb_r <= ir[14:11];
                d_bready_r <= 1'b1;
                mem_addr_reg_idx <= r1;
                mem_is_post <= 1'b0;
                mem_pre_update <= 1'b0;
                mem_post_val <= a + imm11_sext;
                st <= ST_MEM_WR_REQ;
              end
              OP_STRPRE: begin
                exclusive_valid <= 1'b0;
                d_awvalid_r <= 1'b1;
                d_awaddr_r <= a + imm11_sext;
                d_wvalid_r <= 1'b1;
                d_wdata_r <= b;
                d_wstrb_r <= ir[14:11];
                d_bready_r <= 1'b1;
                mem_addr_reg_idx <= r1;
                mem_is_post <= 1'b0;
                mem_pre_update <= 1'b1;
                mem_post_val <= a + imm11_sext;
                st <= ST_MEM_WR_REQ;
              end
              OP_STREX: begin
                if (exclusive_valid && (exclusive_addr == (a + imm11_sext))) begin
                  exclusive_valid <= 1'b0;
                  d_awvalid_r <= 1'b1;
                  d_awaddr_r <= a + imm11_sext;
                  d_wvalid_r <= 1'b1;
                  d_wdata_r <= regs[ir[20:16]];
                  d_wstrb_r <= 4'hF;
                  d_bready_r <= 1'b1;
                  mem_addr_reg_idx <= r1;
                  mem_is_post <= 1'b0;
                  mem_pre_update <= 1'b0;
                  mem_is_strex <= 1'b1;
                  mem_strex_status <= ir[15:11];
                  st <= ST_MEM_WR_REQ;
                end else begin
                  exclusive_valid <= 1'b0;
                  if (ir[15:11] != 5'd0) regs[ir[15:11]] <= 32'd1;
                  dbg_pc <= dbg_pc + 32'd4;
                  st <= ST_FETCH_REQ;
                end
              end
              OP_STRPOST: begin
                exclusive_valid <= 1'b0;
                d_awvalid_r <= 1'b1;
                d_awaddr_r <= a;
                d_wvalid_r <= 1'b1;
                d_wdata_r <= b;
                d_wstrb_r <= ir[14:11];
                d_bready_r <= 1'b1;
                mem_addr_reg_idx <= r1;
                mem_is_post <= 1'b1;
                mem_post_val <= a + imm11_sext;
                st <= ST_MEM_WR_REQ;
              end
              OP_EI: begin
                int_enable <= 1'b1;
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_DI: begin
                int_enable <= 1'b0;
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_IRET: begin
                dbg_pc <= saved_irq_pc;
                if_req_addr <= saved_irq_pc;
                st <= ST_FETCH_REQ;
              end
              OP_READSPR: begin
                csr_rd_idx <= ir[15:11];
                if (r1 != 5'd0) regs[r1] <= csr_rd_data;
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_WRITESPR: begin
                csr_wr_en <= 1'b1;
                csr_wr_idx <= ir[15:11];
                csr_wr_data <= a;
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_ADDS, OP_ADDSI: begin
                rhs = (op == OP_ADDSI) ? imm16_sext : b;
                sum33 = {1'b0, a} + {1'b0, rhs};
                if (rd != 5'd0) regs[rd] <= sum33[31:0];
                zf <= (sum33[31:0] == 32'h0);
                sf <= sum33[31];
                cf <= sum33[32];
                vf <= (~(a[31] ^ rhs[31]) & (a[31] ^ sum33[31]));
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_SUBS, OP_SUBSI: begin
                rhs = (op == OP_SUBSI) ? imm16_sext : b;
                if (rd != 5'd0) regs[rd] <= a - rhs;
                zf <= ((a - rhs) == 32'h0);
                sf <= ((a - rhs) >> 31);
                cf <= (a >= rhs);
                vf <= ((a[31] ^ rhs[31]) & (a[31] ^ ((a - rhs) >> 31)));
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_ADC, OP_ADCS: begin
                rhs = b + {31'h0, cf};
                sum33 = {1'b0, a} + {1'b0, rhs};
                if (rd != 5'd0) regs[rd] <= sum33[31:0];
                if (op == OP_ADCS) begin
                  zf <= (sum33[31:0] == 32'h0);
                  sf <= sum33[31];
                  cf <= sum33[32];
                  vf <= (~(a[31] ^ rhs[31]) & (a[31] ^ sum33[31]));
                end
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_SBC, OP_SBCS: begin
                rhs = b + {31'h0, ~cf};
                if (rd != 5'd0) regs[rd] <= a - rhs;
                if (op == OP_SBCS) begin
                  zf <= ((a - rhs) == 32'h0);
                  sf <= ((a - rhs) >> 31);
                  cf <= (a >= rhs);
                  vf <= ((a[31] ^ rhs[31]) & (a[31] ^ ((a - rhs) >> 31)));
                end
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_ANDS: begin
                if (rd != 5'd0) regs[rd] <= (a & b);
                zf <= ((a & b) == 32'h0);
                sf <= (a[31] & b[31]);
                cf <= 1'b0;
                vf <= 1'b0;
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_ADDI, OP_SUBI: begin
                if (rd != 5'd0) regs[rd] <= res;
                if (op == OP_SUBI) zf <= (res == 32'h0);
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR, OP_BIC, OP_MVN, OP_NEG,
              OP_SLL, OP_SLR, OP_SAL, OP_ROL, OP_ROR: begin
                if (rd != 5'd0) regs[rd] <= res;
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              default: begin
                illegal_instr_r <= 1'b1;
                dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
            endcase
          end
        end
        ST_MEM_RD_REQ: begin
          if (d_arvalid_r && d_arready) begin
            d_arvalid_r <= 1'b0;
            st <= ST_MEM_RD_WAIT;
          end
        end
        ST_MEM_RD_WAIT: begin
          if (d_rvalid && d_rresp == 2'b00) begin
            if (mem_reg_idx != 5'd0) begin
              rhs = 32'h0;
              if (mem_mask[0]) rhs[7:0] = d_rdata[7:0];
              if (mem_mask[1]) rhs[15:8] = d_rdata[15:8];
              if (mem_mask[2]) rhs[23:16] = d_rdata[23:16];
              if (mem_mask[3]) rhs[31:24] = d_rdata[31:24];
              regs[mem_reg_idx] <= rhs;
            end
            if (mem_pre_update && mem_addr_reg_idx != 5'd0) regs[mem_addr_reg_idx] <= mem_post_val;
            if (mem_is_post && mem_addr_reg_idx != 5'd0) regs[mem_addr_reg_idx] <= mem_post_val;
            d_rready_r <= 1'b0;
            dbg_pc <= dbg_pc + 32'd4;
            st <= ST_FETCH_REQ;
          end
        end
        ST_MEM_WR_REQ: begin
          if (d_awvalid_r && d_awready) d_awvalid_r <= 1'b0;
          if (d_wvalid_r && d_wready) d_wvalid_r <= 1'b0;
          if (!d_awvalid_r && !d_wvalid_r) st <= ST_MEM_WR_WAIT;
        end
        ST_MEM_WR_WAIT: begin
          if (d_bvalid) begin
            if (mem_pre_update && mem_addr_reg_idx != 5'd0) regs[mem_addr_reg_idx] <= mem_post_val;
            if (mem_is_post && mem_addr_reg_idx != 5'd0) regs[mem_addr_reg_idx] <= mem_post_val;
            if (mem_is_strex && mem_strex_status != 5'd0) regs[mem_strex_status] <= 32'd0;
            mem_is_strex <= 1'b0;
            d_bready_r <= 1'b0;
            dbg_pc <= dbg_pc + 32'd4;
            st <= ST_FETCH_REQ;
          end
        end
        default: st <= ST_FETCH_REQ;
      endcase
    end
  end
endmodule
