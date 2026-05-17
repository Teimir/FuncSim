module axi4lite_psram #(
  parameter integer MEM_WORDS = 128,
  parameter integer READ_LATENCY = 0,
  parameter [31:0] BASE_ADDR = 32'h0000_0000,
  parameter bit ENABLE_FW_BOOTLOAD = 1'b0,
  parameter bit USE_READMEMH = 1'b1
) (
  input logic        clk,
  input logic        rst_n,
  output logic        fw_ready,
  input logic        s_awvalid,
  output logic        s_awready,
  input logic [31:0] s_awaddr,
  input logic        s_wvalid,
  output logic        s_wready,
  input logic [31:0] s_wdata,
  input logic [3:0]  s_wstrb,
  output logic         s_bvalid,
  input logic        s_bready,
  output logic  [1:0]  s_bresp,
  input logic        s_arvalid,
  output logic        s_arready,
  input logic [31:0] s_araddr,
  output logic         s_rvalid,
  input logic        s_rready,
  output logic  [31:0] s_rdata,
  output logic  [1:0]  s_rresp
);
  localparam [1:0] AXI_OKAY = 2'b00;
  localparam [1:0] AXI_SLVERR = 2'b10;
  localparam bit FAST_READ = (READ_LATENCY == 0);

  (* ram_style = "block" *) logic [7:0] mem_b0 [0:MEM_WORDS-1];
  (* ram_style = "block" *) logic [7:0] mem_b1 [0:MEM_WORDS-1];
  (* ram_style = "block" *) logic [7:0] mem_b2 [0:MEM_WORDS-1];
  (* ram_style = "block" *) logic [7:0] mem_b3 [0:MEM_WORDS-1];

  logic fw_done;

  logic [31:0] rd_addr_q;
  logic rd_ok_q;
  logic [7:0] rd_wait;
  logic rd_pending;

  assign fw_ready = fw_done;
  assign s_awready = fw_done && !s_bvalid;
  assign s_wready = fw_done && !s_bvalid;
  assign s_arready = fw_done && (FAST_READ ? !s_rvalid : (!rd_pending && !s_rvalid));

  logic wr_fire;
  logic rd_fire;
  logic [31:0] wr_off;
  logic [31:0] rd_off;
  logic wr_ok;
  logic rd_ok;
  assign wr_fire = s_awvalid && s_wvalid && !s_bvalid;
  assign rd_fire = s_arvalid && s_arready;
  assign wr_off = s_awaddr - BASE_ADDR;
  assign rd_off = s_araddr - BASE_ADDR;
  assign wr_ok = (s_awaddr[1:0] == 2'b00) && (wr_off[31:2] < MEM_WORDS);
  assign rd_ok = (s_araddr[1:0] == 2'b00) && (rd_off[31:2] < MEM_WORDS);

  initial begin
    if (USE_READMEMH) begin
      $readmemh("firmware_b0.hex", mem_b0);
      $readmemh("firmware_b1.hex", mem_b1);
      $readmemh("firmware_b2.hex", mem_b2);
      $readmemh("firmware_b3.hex", mem_b3);
    end
  end

  generate
    if (ENABLE_FW_BOOTLOAD) begin : g_boot
      `include "firmware_rom.svh"
      logic [$clog2(MEM_WORDS)-1:0] fw_idx;
      logic [31:0] fw_rom_wdata;
      assign fw_rom_wdata = fw_rom_word(fw_idx);

      always_ff @(posedge clk) begin
        if (!rst_n) begin
          fw_idx <= '0;
          fw_done <= 1'b0;
        end else if (!fw_done) begin
          if (fw_idx < FW_WORDS) begin
            mem_b0[fw_idx] <= fw_rom_wdata[7:0];
            mem_b1[fw_idx] <= fw_rom_wdata[15:8];
            mem_b2[fw_idx] <= fw_rom_wdata[23:16];
            mem_b3[fw_idx] <= fw_rom_wdata[31:24];
            fw_idx <= fw_idx + 1'b1;
          end else begin
            fw_done <= 1'b1;
          end
        end
      end
    end else begin : g_no_boot
      always_ff @(posedge clk) begin
        if (!rst_n)
          fw_done <= 1'b1;
      end
    end
  endgenerate

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      s_bvalid <= 1'b0;
      s_bresp <= AXI_OKAY;
      s_rvalid <= 1'b0;
      s_rresp <= AXI_OKAY;
      s_rdata <= 32'h0;
      rd_addr_q <= 32'h0;
      rd_ok_q <= 1'b0;
      rd_wait <= 8'd0;
      rd_pending <= 1'b0;
    end else begin
      if (wr_fire) begin
        if (wr_ok) begin
          if (s_wstrb[0]) mem_b0[wr_off[31:2]] <= s_wdata[7:0];
          if (s_wstrb[1]) mem_b1[wr_off[31:2]] <= s_wdata[15:8];
          if (s_wstrb[2]) mem_b2[wr_off[31:2]] <= s_wdata[23:16];
          if (s_wstrb[3]) mem_b3[wr_off[31:2]] <= s_wdata[31:24];
          s_bresp <= AXI_OKAY;
        end else begin
          s_bresp <= AXI_SLVERR;
        end
        s_bvalid <= 1'b1;
      end else if (s_bvalid && s_bready) begin
        s_bvalid <= 1'b0;
      end

      if (FAST_READ) begin
        if (rd_fire) begin
          s_rdata <= rd_ok ? {mem_b3[rd_off[31:2]], mem_b2[rd_off[31:2]], mem_b1[rd_off[31:2]], mem_b0[rd_off[31:2]]} : 32'h0;
          s_rresp <= rd_ok ? AXI_OKAY : AXI_SLVERR;
          s_rvalid <= 1'b1;
        end else if (s_rvalid && s_rready) begin
          s_rvalid <= 1'b0;
        end
      end else begin
        if (rd_fire) begin
          rd_addr_q <= rd_off[31:2];
          rd_ok_q <= rd_ok;
          rd_wait <= READ_LATENCY[7:0];
          rd_pending <= 1'b1;
        end else if (rd_pending) begin
          if (rd_wait != 8'd0) begin
            rd_wait <= rd_wait - 8'd1;
          end else begin
            s_rdata <= rd_ok_q ? {mem_b3[rd_addr_q], mem_b2[rd_addr_q], mem_b1[rd_addr_q], mem_b0[rd_addr_q]} : 32'h0;
            s_rresp <= rd_ok_q ? AXI_OKAY : AXI_SLVERR;
            s_rvalid <= 1'b1;
            rd_pending <= 1'b0;
          end
        end
        if (s_rvalid && s_rready) begin
          s_rvalid <= 1'b0;
        end
      end
    end
  end
endmodule
