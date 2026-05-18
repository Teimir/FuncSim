// Файл ram.sv; модуль axi4lite_ram — AXI4-Lite RAM на BSRAM (байтовые банки).
module axi4lite_ram #(
  parameter integer MEM_WORDS = 1024,
  parameter [31:0] BASE_ADDR = 32'h0000_0000,
  parameter bit ENABLE_FW_BOOTLOAD = 1'b0
) (
  input  logic        clk,
  input  logic        rst_n,
  output logic        fw_ready,
  input  logic        s_awvalid,
  output logic        s_awready,
  input  logic [31:0] s_awaddr,
  input  logic        s_wvalid,
  output logic        s_wready,
  input  logic [31:0] s_wdata,
  input  logic [3:0]  s_wstrb,
  output logic         s_bvalid,
  input  logic        s_bready,
  output logic  [1:0]  s_bresp,
  input  logic        s_arvalid,
  output logic        s_arready,
  input  logic [31:0] s_araddr,
  output logic         s_rvalid,
  input  logic        s_rready,
  output logic  [31:0] s_rdata,
  output logic  [1:0]  s_rresp
);
  localparam [1:0] AXI_OKAY = 2'b00;
  localparam [1:0] AXI_SLVERR = 2'b10;

  (* syn_ramstyle = "block_ram" *) logic [7:0] mem_b0[0:MEM_WORDS-1];
  (* syn_ramstyle = "block_ram" *) logic [7:0] mem_b1[0:MEM_WORDS-1];
  (* syn_ramstyle = "block_ram" *) logic [7:0] mem_b2[0:MEM_WORDS-1];
  (* syn_ramstyle = "block_ram" *) logic [7:0] mem_b3[0:MEM_WORDS-1];

  logic wr_fire;
  logic rd_fire;
  logic [31:0] wr_off;
  logic [31:0] rd_off;
  logic wr_aligned;
  logic rd_aligned;
  logic wr_in_range;
  logic rd_in_range;
  logic rd_pending;
  logic rd_ok;
  logic [31:0] rd_addr_q;
  logic fw_done;
  logic boot_copy;
  logic [$clog2(MEM_WORDS)-1:0] fw_idx;
  logic rom_boot_wr;
  logic [$clog2(MEM_WORDS)-1:0] rom_boot_addr;
  logic [31:0] rom_boot_wdata;

  assign fw_ready = fw_done;
  assign wr_fire = s_awvalid && s_wvalid && !s_bvalid;
  assign rd_fire = s_arvalid && !s_rvalid;
  assign s_awready = fw_done && !s_bvalid;
  assign s_wready  = fw_done && !s_bvalid;
  assign s_arready = fw_done && !s_rvalid;
  assign wr_off = s_awaddr - BASE_ADDR;
  assign rd_off = s_araddr - BASE_ADDR;
  assign wr_aligned = (s_awaddr[1:0] == 2'b00);
  assign rd_aligned = (s_araddr[1:0] == 2'b00);
  assign wr_in_range = (wr_off[31:2] < MEM_WORDS);
  assign rd_in_range = (rd_off[31:2] < MEM_WORDS);
  // После сброса — копия firmware_rom.svh (на TN9K/Gowin пути $readmemh ненадёжны).
  assign boot_copy = ENABLE_FW_BOOTLOAD && !fw_done;

  generate
    if (ENABLE_FW_BOOTLOAD) begin : g_boot_runtime
      `include "firmware_rom.svh"
      assign rom_boot_wdata = fw_rom_word(fw_idx);
      assign rom_boot_wr    = boot_copy && (fw_idx < FW_WORDS);
      assign rom_boot_addr  = fw_idx[$clog2(MEM_WORDS)-1:0];

      always_ff @(posedge clk) begin
        if (!rst_n) begin
          fw_idx   <= '0;
          fw_done  <= 1'b0;
        end else if (boot_copy) begin
          if (fw_idx < FW_WORDS)
            fw_idx <= fw_idx + 1'b1;
          else
            fw_done <= 1'b1;
        end
      end
    end else begin : g_no_boot
      assign rom_boot_wr    = 1'b0;
      assign rom_boot_addr  = '0;
      assign rom_boot_wdata = 32'h0;
      always_ff @(posedge clk) begin
        if (!rst_n)
          fw_done <= 1'b1;
      end
    end
  endgenerate

  // Один порт записи — иначе Gowin не выводит BSRAM (два always_ff → взрыв LUT/DFF).
  always_ff @(posedge clk) begin
    if (rom_boot_wr) begin
      mem_b0[rom_boot_addr] <= rom_boot_wdata[7:0];
      mem_b1[rom_boot_addr] <= rom_boot_wdata[15:8];
      mem_b2[rom_boot_addr] <= rom_boot_wdata[23:16];
      mem_b3[rom_boot_addr] <= rom_boot_wdata[31:24];
    end else if (wr_fire && fw_done) begin
      if (wr_aligned && wr_in_range) begin
        if (s_wstrb[0]) mem_b0[wr_off[31:2]] <= s_wdata[7:0];
        if (s_wstrb[1]) mem_b1[wr_off[31:2]] <= s_wdata[15:8];
        if (s_wstrb[2]) mem_b2[wr_off[31:2]] <= s_wdata[23:16];
        if (s_wstrb[3]) mem_b3[wr_off[31:2]] <= s_wdata[31:24];
      end
    end
  end

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      s_bvalid <= 1'b0;
      s_bresp <= AXI_OKAY;
      s_rvalid <= 1'b0;
      s_rresp <= AXI_OKAY;
      s_rdata <= 32'h0;
      rd_pending <= 1'b0;
      rd_ok <= 1'b0;
      rd_addr_q <= 32'h0;
    end else begin
      if (wr_fire) begin
        if (wr_aligned && wr_in_range) begin
          s_bresp <= AXI_OKAY;
        end else begin
          s_bresp <= AXI_SLVERR;
        end
        s_bvalid <= 1'b1;
      end else if (s_bvalid && s_bready) begin
        s_bvalid <= 1'b0;
      end

      if (rd_fire) begin
        rd_addr_q <= rd_off[31:2];
        rd_ok <= rd_aligned && rd_in_range;
        rd_pending <= 1'b1;
      end
      if (rd_pending) begin
        s_rdata <= rd_ok ? {mem_b3[rd_addr_q], mem_b2[rd_addr_q], mem_b1[rd_addr_q], mem_b0[rd_addr_q]} : 32'h0;
        s_rresp <= rd_ok ? AXI_OKAY : AXI_SLVERR;
        s_rvalid <= 1'b1;
        rd_pending <= 1'b0;
      end else if (s_rvalid && s_rready) begin
        s_rvalid <= 1'b0;
      end
    end
  end
endmodule
