// Minimal E32C core for Tang Nano 9K (subset ISA + timer IRQ: EI/DI/IRET/WRITESPR).
module e32c_core_tn9k (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        if_stall,
  output logic        if_req_valid,
  output logic [31:0] if_req_addr,
  input  logic        if_resp_valid,
  input  logic [31:0] if_resp_data,
  input  logic [31:0] irq_lines,
  output logic        d_awvalid,
  input  logic        d_awready,
  output logic [31:0] d_awaddr,
  output logic        d_wvalid,
  input  logic        d_wready,
  output logic [31:0] d_wdata,
  output logic [3:0]  d_wstrb,
  input  logic        d_bvalid,
  output logic        d_bready,
  input  logic [1:0]  d_bresp,
  output logic        d_arvalid,
  input  logic        d_arready,
  output logic [31:0] d_araddr,
  input  logic        d_rvalid,
  output logic        d_rready,
  input  logic [31:0] d_rdata,
  input  logic [1:0]  d_rresp,
  output logic [31:0] dbg_pc,
  output logic        dbg_halted,
  output logic        illegal_instr,
  output logic [31:0] dbg_r1,
  output logic [31:0] dbg_r2,
  output logic [31:0] dbg_r3,
  output logic [31:0] dbg_r4
);
  localparam [5:0] OP_LDR       = 6'd1;
  localparam [5:0] OP_STR       = 6'd2;
  localparam [5:0] OP_ANDS      = 6'd14;
  localparam [5:0] OP_JMP       = 6'd16;
  localparam [5:0] OP_JZ        = 6'd17;
  localparam [5:0] OP_JNZ       = 6'd18;
  localparam [5:0] OP_XOR       = 6'd39;
  localparam [5:0] OP_SLL       = 6'd40;
  localparam [5:0] OP_WRITESPR  = 6'd25;
  localparam [5:0] OP_ADDI      = 6'd48;
  localparam [5:0] OP_SUBI      = 6'd49;
  localparam [5:0] OP_EI        = 6'd50;
  localparam [5:0] OP_DI        = 6'd51;
  localparam [5:0] OP_IRET      = 6'd62;

  localparam [2:0] ST_FETCH_REQ    = 3'd0;
  localparam [2:0] ST_FETCH_WAIT   = 3'd1;
  localparam [2:0] ST_EXEC         = 3'd2;
  localparam [2:0] ST_MEM_RD_REQ   = 3'd3;
  localparam [2:0] ST_MEM_RD_WAIT  = 3'd4;
  localparam [2:0] ST_MEM_WR_REQ   = 3'd5;
  localparam [2:0] ST_MEM_WR_WAIT  = 3'd6;

  logic [2:0]  st;
  logic [31:0] regs [0:31];
  logic [31:0] ir;
  logic        zf;
  logic        d_awvalid_r, d_wvalid_r, d_bready_r, d_arvalid_r, d_rready_r;
  logic [31:0] d_awaddr_r, d_wdata_r, d_araddr_r;
  logic [3:0]  d_wstrb_r;
  logic [4:0]  mem_reg_idx;
  logic [3:0]  mem_mask;
  logic        illegal_instr_r;

  logic        int_enable;
  logic        csr_wr_en;
  logic [1:0]  csr_wr_idx;
  logic [31:0] csr_wr_data;
  logic [1:0]  csr_rd_idx;
  logic [31:0] csr_rd_data;
  logic        irq_pending;
  logic        irq_ack_r;
  logic [31:0] irq_vector;
  logic [31:0] saved_irq_pc;

  logic [4:0]  r1, r2, rd, br_raddr, spr_idx;
  logic [5:0]  op;
  logic [31:0] a, b;
  logic [15:0] imm16;
  logic [10:0] imm11;
  logic [31:0] imm16_sext, imm11_sext;
  logic [31:0] alu_res;
  integer      i;

  wire iret_exec = (st == ST_EXEC) && (op == OP_IRET) && (ir != 32'hFFFF_FFFF);

  function automatic logic [31:0] gpr_read(input logic [4:0] idx);
    gpr_read = (idx == 5'd0) ? 32'h0 : ((idx == 5'd31) ? dbg_pc : regs[idx]);
  endfunction

  assign irq_ack_r = irq_pending && (st == ST_FETCH_REQ) && !if_stall && !dbg_halted;

  csr_irq u_csr_irq (
    .clk(clk),
    .rst_n(rst_n),
    .cur_pc(dbg_pc),
    .irq_lines(irq_lines),
    .int_enable(int_enable),
    .iret_exec(iret_exec),
    .irq_ack(irq_ack_r),
    .wr_en(csr_wr_en),
    .wr_idx(csr_wr_idx),
    .wr_data(csr_wr_data),
    .rd_idx(csr_rd_idx),
    .rd_data(csr_rd_data),
    .irq_pending(irq_pending),
    .irq_vector(irq_vector),
    .saved_irq_pc(saved_irq_pc)
  );

  always_comb begin
    r1       = ir[25:21];
    r2       = ir[20:16];
    rd       = ir[15:11];
    spr_idx  = ir[15:11];
    br_raddr = ir[25:21];
    op       = ir[31:26];
    a        = gpr_read(r1);
    b        = gpr_read(r2);
    imm16    = {ir[20:16], ir[10:0]};
    imm11    = ir[10:0];
    imm16_sext = {{16{imm16[15]}}, imm16};
    imm11_sext = {{21{imm11[10]}}, imm11};
    alu_res  = 32'h0;
    unique case (op)
      OP_ADDI: alu_res = a + imm16_sext;
      OP_SLL:  alu_res = a << b[4:0];
      OP_XOR:  alu_res = a ^ b;
      default: alu_res = 32'h0;
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
  assign dbg_r1    = regs[1];
  assign dbg_r2    = regs[2];
  assign dbg_r3    = regs[3];
  assign dbg_r4    = regs[4];
  assign illegal_instr = illegal_instr_r;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      dbg_pc          <= 32'h0;
      dbg_halted      <= 1'b0;
      illegal_instr_r <= 1'b0;
      zf              <= 1'b0;
      if_req_valid    <= 1'b0;
      if_req_addr     <= 32'h0;
      ir              <= 32'h0;
      st              <= ST_FETCH_REQ;
      d_awvalid_r     <= 1'b0;
      d_wvalid_r      <= 1'b0;
      d_bready_r      <= 1'b0;
      d_arvalid_r     <= 1'b0;
      d_rready_r      <= 1'b0;
      d_awaddr_r      <= 32'h0;
      d_wdata_r       <= 32'h0;
      d_araddr_r      <= 32'h0;
      d_wstrb_r       <= 4'hF;
      mem_reg_idx     <= 5'd0;
      mem_mask        <= 4'h0;
      int_enable      <= 1'b0;
      csr_wr_en       <= 1'b0;
      csr_wr_idx      <= 2'b0;
      csr_wr_data     <= 32'h0;
      csr_rd_idx      <= 2'b0;
      for (i = 0; i < 32; i = i + 1) regs[i] <= 32'h0;
    end else begin
      csr_wr_en <= 1'b0;
      regs[0]   <= 32'h0;
      regs[31]  <= dbg_pc;
      case (st)
        ST_FETCH_REQ: begin
          if_req_valid <= !dbg_halted;
          d_awvalid_r  <= 1'b0;
          d_wvalid_r   <= 1'b0;
          d_bready_r   <= 1'b0;
          d_arvalid_r  <= 1'b0;
          d_rready_r   <= 1'b0;
          if (!if_stall && !dbg_halted) begin
            if (irq_pending) begin
              dbg_pc      <= irq_vector;
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
          illegal_instr_r <= 1'b0;
          if (ir == 32'hFFFF_FFFF) begin
            dbg_halted <= 1'b1;
            st         <= ST_FETCH_REQ;
          end else begin
            unique case (op)
              OP_JMP: begin
                dbg_pc <= gpr_read(br_raddr) + imm11_sext;
                st     <= ST_FETCH_REQ;
              end
              OP_JZ: begin
                dbg_pc <= zf ? (gpr_read(br_raddr) + imm11_sext) : (dbg_pc + 32'd4);
                st     <= ST_FETCH_REQ;
              end
              OP_JNZ: begin
                dbg_pc <= (!zf) ? (gpr_read(br_raddr) + imm11_sext) : (dbg_pc + 32'd4);
                st     <= ST_FETCH_REQ;
              end
              OP_SUBI: begin
                if (rd != 5'd0 && rd != 5'd31) regs[rd] <= a - imm16_sext;
                zf <= ((a - imm16_sext) == 32'h0);
                if (rd == 5'd31) dbg_pc <= a - imm16_sext;
                else dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_ANDS: begin
                if (rd != 5'd0 && rd != 5'd31) regs[rd] <= a & b;
                zf <= ((a & b) == 32'h0);
                if (rd == 5'd31) dbg_pc <= a & b;
                else dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_ADDI, OP_SLL, OP_XOR: begin
                if (rd != 5'd0 && rd != 5'd31) regs[rd] <= alu_res;
                if (rd == 5'd31) dbg_pc <= alu_res;
                else dbg_pc <= dbg_pc + 32'd4;
                st <= ST_FETCH_REQ;
              end
              OP_EI: begin
                int_enable <= 1'b1;
                dbg_pc     <= dbg_pc + 32'd4;
                st         <= ST_FETCH_REQ;
              end
              OP_DI: begin
                int_enable <= 1'b0;
                dbg_pc     <= dbg_pc + 32'd4;
                st         <= ST_FETCH_REQ;
              end
              OP_IRET: begin
                dbg_pc      <= saved_irq_pc;
                if_req_addr <= saved_irq_pc;
                st          <= ST_FETCH_REQ;
              end
              OP_WRITESPR: begin
                csr_wr_en   <= 1'b1;
                csr_wr_idx  <= spr_idx[1:0];
                csr_wr_data <= a;
                dbg_pc      <= dbg_pc + 32'd4;
                st          <= ST_FETCH_REQ;
              end
              OP_LDR: begin
                d_arvalid_r <= 1'b1;
                d_araddr_r  <= a + imm11_sext;
                d_rready_r  <= 1'b1;
                mem_reg_idx <= r2;
                mem_mask    <= ir[14:11];
                st          <= ST_MEM_RD_REQ;
              end
              OP_STR: begin
                d_awvalid_r <= 1'b1;
                d_awaddr_r  <= a + imm11_sext;
                d_wvalid_r  <= 1'b1;
                d_wdata_r   <= b;
                d_wstrb_r   <= ir[14:11];
                d_bready_r  <= 1'b1;
                st          <= ST_MEM_WR_REQ;
              end
              default: begin
                if (ir == 32'h0) begin
                  dbg_pc <= dbg_pc + 32'd4;
                  st     <= ST_FETCH_REQ;
                end else begin
                  illegal_instr_r <= 1'b1;
                  dbg_pc          <= dbg_pc + 32'd4;
                  st              <= ST_FETCH_REQ;
                end
              end
            endcase
          end
        end
        ST_MEM_RD_REQ: begin
          if (d_arvalid_r && d_arready) begin
            d_arvalid_r <= 1'b0;
            st          <= ST_MEM_RD_WAIT;
          end
        end
        ST_MEM_RD_WAIT: begin
          if (d_rvalid && d_rresp == 2'b00) begin
            if (mem_reg_idx != 5'd0) begin
              unique case (mem_mask)
                4'b0001: regs[mem_reg_idx] <= {24'h0, d_rdata[7:0]};
                4'b0010: regs[mem_reg_idx] <= {16'h0, d_rdata[15:8], 8'h0};
                4'b0100: regs[mem_reg_idx] <= {8'h0, d_rdata[23:16], 16'h0};
                4'b1000: regs[mem_reg_idx] <= {d_rdata[31:24], 24'h0};
                default: regs[mem_reg_idx] <= d_rdata;
              endcase
            end
            d_rready_r <= 1'b0;
            dbg_pc     <= dbg_pc + 32'd4;
            st         <= ST_FETCH_REQ;
          end
        end
        ST_MEM_WR_REQ: begin
          if (d_awvalid_r && d_awready) d_awvalid_r <= 1'b0;
          if (d_wvalid_r && d_wready) d_wvalid_r <= 1'b0;
          if (!d_awvalid_r && !d_wvalid_r) st <= ST_MEM_WR_WAIT;
        end
        ST_MEM_WR_WAIT: begin
          if (d_bvalid) begin
            d_bready_r <= 1'b0;
            dbg_pc     <= dbg_pc + 32'd4;
            st         <= ST_FETCH_REQ;
          end
        end
        default: st <= ST_FETCH_REQ;
      endcase
    end
  end
endmodule
