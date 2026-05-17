module soc_top #(
  parameter integer RAM_WORDS = 128,
  parameter integer PSRAM_WORDS = 128,
  parameter ENABLE_CORE = 1,
  parameter USE_LITE_CORE = 0,
  parameter USE_TN9K_CORE = 0,
  parameter FORCE_IF_NOP_FETCH = 0,
  parameter integer IF_ROM_WORDS = 128,
  parameter IF_ROM_USE_BRAM = 1'b0,
  parameter USE_DUAL_RAM = 1'b0,
  parameter integer RAM_BANK1_WORDS = 8192,
  parameter ENABLE_UART = 1,
  parameter ENABLE_TIMER = 1,
  parameter ENABLE_GPIO = 1,
  parameter ENABLE_SD_SPI = 0,
  parameter bit SD_MMIO_MODE = 1'b1,
  parameter bit SD_BACKEND = 1'b0,
  parameter bit SD_USE_CARD_MEM = 1'b1,
  parameter ENABLE_FW_BOOTLOAD = 1'b0,
  parameter BOOT_INIT_MEMH = 1'b0,
  // Tang Nano 9K: simple BRAM (no PSRAM boot ROM) saves ~2k LUT.
  parameter USE_FPGA_RAM = 1'b0,
  // Simulation may preload hex; FPGA relies on firmware_rom.svh boot copy only.
  parameter USE_READMEMH = 1'b1,
  parameter integer PSRAM_READ_LATENCY = 3,
  parameter int UART_CLK_MHZ = 27,
  parameter int UART_BAUD = 115200
) (
  input logic        clk,
  input logic        rst_n,
  input logic        ext_awvalid,
  output logic        ext_awready,
  input logic [31:0] ext_awaddr,
  input logic        ext_wvalid,
  output logic        ext_wready,
  input logic [31:0] ext_wdata,
  input logic [3:0]  ext_wstrb,
  output logic        ext_bvalid,
  input logic        ext_bready,
  output logic [1:0]  ext_bresp,
  input logic        ext_arvalid,
  output logic        ext_arready,
  input logic [31:0] ext_araddr,
  output logic        ext_rvalid,
  input logic        ext_rready,
  output logic [31:0] ext_rdata,
  output logic [1:0]  ext_rresp,
  output logic        uart_tx,
  input logic        uart_rx,
  output logic        sd_spi_sck,
  output logic        sd_spi_mosi,
  input logic        sd_spi_miso,
  output logic        sd_spi_cs_n,
  inout wire          IO_sdio_cmd,
  inout wire          IO_sdio_dat0,
  inout wire          IO_sdio_dat1_irq,
  inout wire          IO_sdio_dat2_rw,
  inout wire          IO_sdio_dat3_cd,
  output logic        soc_activity,
  output logic        illegal_instr,
  output logic [31:0] gpio_out_obs,
  output logic [31:0] core_pc_obs,
  output logic        core_halted_obs,
  output logic        if_req_obs,
  output logic        if_resp_obs,
  output logic        if_stall_obs
);
  logic core_if_req_valid;
  logic [31:0] core_if_req_addr;
  logic core_if_resp_valid;
  logic [31:0] core_if_resp_data;
  logic core_if_stall;
  logic icache_stall_w;
  logic mem_fw_ready;
  logic boot_if_hold;
  assign boot_if_hold = ENABLE_FW_BOOTLOAD && !mem_fw_ready;
  logic core_d_awvalid;
  logic core_d_awready;
  logic [31:0] core_d_awaddr;
  logic core_d_wvalid;
  logic core_d_wready;
  logic [31:0] core_d_wdata;
  logic [3:0] core_d_wstrb;
  logic core_d_bvalid;
  logic core_d_bready;
  logic [1:0] core_d_bresp;
  logic core_d_arvalid;
  logic core_d_arready;
  logic [31:0] core_d_araddr;
  logic core_d_rvalid;
  logic core_d_rready;
  logic [31:0] core_d_rdata;
  logic [1:0] core_d_rresp;

  logic ic_arvalid;
  logic ic_arready;
  logic [31:0] ic_araddr;
  logic ic_rvalid;
  logic ic_rready;
  logic [31:0] ic_rdata;
  logic [1:0] ic_rresp;

  logic [31:0] irq_lines;
  logic core_illegal_instr;
  logic [31:0] core_dbg_pc;
  logic core_dbg_halted;

  generate
    if (ENABLE_CORE && (USE_LITE_CORE == 0) && (USE_TN9K_CORE == 0)) begin : g_core_full
  e32c_core u_core (
    .clk(clk),
    .rst_n(rst_n),
    .if_stall(core_if_stall),
    .if_req_valid(core_if_req_valid),
    .if_req_addr(core_if_req_addr),
    .if_resp_valid(core_if_resp_valid),
    .if_resp_data(core_if_resp_data),
    .irq_lines(irq_lines),
    .d_awvalid(core_d_awvalid),
    .d_awready(core_d_awready),
    .d_awaddr(core_d_awaddr),
    .d_wvalid(core_d_wvalid),
    .d_wready(core_d_wready),
    .d_wdata(core_d_wdata),
    .d_wstrb(core_d_wstrb),
    .d_bvalid(core_d_bvalid),
    .d_bready(core_d_bready),
    .d_bresp(core_d_bresp),
    .d_arvalid(core_d_arvalid),
    .d_arready(core_d_arready),
    .d_araddr(core_d_araddr),
    .d_rvalid(core_d_rvalid),
    .d_rready(core_d_rready),
    .d_rdata(core_d_rdata),
    .d_rresp(core_d_rresp),
    .dbg_pc(core_dbg_pc),
    .dbg_halted(core_dbg_halted),
    .illegal_instr(core_illegal_instr),
    .dbg_r1(),
    .dbg_r2(),
    .dbg_r3(),
    .dbg_r4()
  );

      if (FORCE_IF_NOP_FETCH == 0) begin : g_if_icache
        assign core_if_stall = icache_stall_w | boot_if_hold;
        icache u_icache (
          .clk(clk),
          .rst_n(rst_n),
          .req_valid(core_if_req_valid),
          .req_addr(core_if_req_addr),
          .stall(icache_stall_w),
          .resp_valid(core_if_resp_valid),
          .resp_data(core_if_resp_data),
          .m_arvalid(ic_arvalid),
          .m_arready(ic_arready),
          .m_araddr(ic_araddr),
          .m_rvalid(ic_rvalid),
          .m_rready(ic_rready),
          .m_rdata(ic_rdata),
          .m_rresp(ic_rresp)
        );
      end else if (IF_ROM_USE_BRAM) begin : g_if_bram
        instr_fetch_rom #(.WORDS(IF_ROM_WORDS)) u_if_rom (
          .clk(clk),
          .rst_n(rst_n),
          .req_valid(core_if_req_valid && !boot_if_hold),
          .req_addr(core_if_req_addr),
          .resp_valid(core_if_resp_valid),
          .resp_data(core_if_resp_data)
        );
        assign core_if_stall = boot_if_hold;
        assign ic_arvalid = 1'b0;
        assign ic_araddr = 32'h0;
        assign ic_rready = 1'b0;
      end else begin : g_if_nop
        logic [31:0] forced_instr;
        localparam integer IF_MSB = (IF_ROM_WORDS <= 1) ? 2 : ($clog2(IF_ROM_WORDS) + 1);
        always_comb begin
          case (core_if_req_addr[IF_MSB:2])
`include "fetch_rom_nop.svh"
          endcase
        end
        assign core_if_stall = boot_if_hold;
        assign core_if_resp_valid = core_if_req_valid && !boot_if_hold;
        assign core_if_resp_data = forced_instr;
        assign ic_arvalid = 1'b0;
        assign ic_araddr = 32'h0;
        assign ic_rready = 1'b0;
      end
    end else if (ENABLE_CORE && (USE_LITE_CORE == 0) && (USE_TN9K_CORE == 1)) begin : g_core_tn9k
      e32c_core_tn9k u_core_tn9k (
        .clk(clk),
        .rst_n(rst_n),
        .if_stall(core_if_stall),
        .if_req_valid(core_if_req_valid),
        .if_req_addr(core_if_req_addr),
        .if_resp_valid(core_if_resp_valid),
        .if_resp_data(core_if_resp_data),
        .irq_lines(irq_lines),
        .d_awvalid(core_d_awvalid),
        .d_awready(core_d_awready),
        .d_awaddr(core_d_awaddr),
        .d_wvalid(core_d_wvalid),
        .d_wready(core_d_wready),
        .d_wdata(core_d_wdata),
        .d_wstrb(core_d_wstrb),
        .d_bvalid(core_d_bvalid),
        .d_bready(core_d_bready),
        .d_bresp(core_d_bresp),
        .d_arvalid(core_d_arvalid),
        .d_arready(core_d_arready),
        .d_araddr(core_d_araddr),
        .d_rvalid(core_d_rvalid),
        .d_rready(core_d_rready),
        .d_rdata(core_d_rdata),
        .d_rresp(core_d_rresp),
        .dbg_pc(core_dbg_pc),
        .dbg_halted(core_dbg_halted),
        .illegal_instr(core_illegal_instr),
        .dbg_r1(),
        .dbg_r2(),
        .dbg_r3(),
        .dbg_r4()
      );

      if (FORCE_IF_NOP_FETCH == 0) begin : g_if_icache_tn9k
        assign core_if_stall = icache_stall_w | boot_if_hold;
        icache u_icache (
          .clk(clk),
          .rst_n(rst_n),
          .req_valid(core_if_req_valid),
          .req_addr(core_if_req_addr),
          .stall(icache_stall_w),
          .resp_valid(core_if_resp_valid),
          .resp_data(core_if_resp_data),
          .m_arvalid(ic_arvalid),
          .m_arready(ic_arready),
          .m_araddr(ic_araddr),
          .m_rvalid(ic_rvalid),
          .m_rready(ic_rready),
          .m_rdata(ic_rdata),
          .m_rresp(ic_rresp)
        );
      end else if (IF_ROM_USE_BRAM) begin : g_if_bram_tn9k
        instr_fetch_rom #(.WORDS(IF_ROM_WORDS)) u_if_rom (
          .clk(clk),
          .rst_n(rst_n),
          .req_valid(core_if_req_valid && !boot_if_hold),
          .req_addr(core_if_req_addr),
          .resp_valid(core_if_resp_valid),
          .resp_data(core_if_resp_data)
        );
        assign core_if_stall = boot_if_hold;
        assign ic_arvalid = 1'b0;
        assign ic_araddr = 32'h0;
        assign ic_rready = 1'b0;
      end else begin : g_if_nop_tn9k
        logic [31:0] forced_instr;
        localparam integer IF_MSB = (IF_ROM_WORDS <= 1) ? 2 : ($clog2(IF_ROM_WORDS) + 1);
        always_comb begin
          case (core_if_req_addr[IF_MSB:2])
`include "fetch_rom_nop.svh"
          endcase
        end
        assign core_if_stall = boot_if_hold;
        assign core_if_resp_valid = core_if_req_valid && !boot_if_hold;
        assign core_if_resp_data = forced_instr;
        assign ic_arvalid = 1'b0;
        assign ic_araddr = 32'h0;
        assign ic_rready = 1'b0;
      end
    end else if (ENABLE_CORE && (USE_LITE_CORE == 1)) begin : g_core_lite
      e32c_core_lite u_core_lite (
        .clk(clk),
        .rst_n(rst_n),
        .if_stall(core_if_stall),
        .if_req_valid(core_if_req_valid),
        .if_req_addr(core_if_req_addr),
        .if_resp_valid(core_if_resp_valid),
        .if_resp_data(core_if_resp_data),
        .irq_lines(irq_lines),
        .d_awvalid(core_d_awvalid),
        .d_awready(core_d_awready),
        .d_awaddr(core_d_awaddr),
        .d_wvalid(core_d_wvalid),
        .d_wready(core_d_wready),
        .d_wdata(core_d_wdata),
        .d_wstrb(core_d_wstrb),
        .d_bvalid(core_d_bvalid),
        .d_bready(core_d_bready),
        .d_bresp(core_d_bresp),
        .d_arvalid(core_d_arvalid),
        .d_arready(core_d_arready),
        .d_araddr(core_d_araddr),
        .d_rvalid(core_d_rvalid),
        .d_rready(core_d_rready),
        .d_rdata(core_d_rdata),
        .d_rresp(core_d_rresp),
        .dbg_pc(core_dbg_pc),
        .dbg_halted(core_dbg_halted),
        .illegal_instr(),
        .dbg_r1(),
        .dbg_r2(),
        .dbg_r3(),
        .dbg_r4()
      );

      assign core_if_stall = icache_stall_w | boot_if_hold;
      icache u_icache_lite (
        .clk(clk),
        .rst_n(rst_n),
        .req_valid(core_if_req_valid),
        .req_addr(core_if_req_addr),
        .stall(icache_stall_w),
        .resp_valid(core_if_resp_valid),
        .resp_data(core_if_resp_data),
        .m_arvalid(ic_arvalid),
        .m_arready(ic_arready),
        .m_araddr(ic_araddr),
        .m_rvalid(ic_rvalid),
        .m_rready(ic_rready),
        .m_rdata(ic_rdata),
        .m_rresp(ic_rresp)
      );
      assign core_illegal_instr = 1'b0;
    end else begin : g_core_off
      assign core_if_stall = 1'b0;
      assign core_if_req_valid = 1'b0;
      assign core_if_req_addr  = 32'h0;
      assign core_d_awvalid = 1'b0;
      assign core_d_awaddr  = 32'h0;
      assign core_d_wvalid  = 1'b0;
      assign core_d_wdata   = 32'h0;
      assign core_d_wstrb   = 4'h0;
      assign core_d_bready  = 1'b0;
      assign core_d_arvalid = 1'b0;
      assign core_d_araddr  = 32'h0;
      assign core_d_rready  = 1'b0;
      assign ic_arvalid = 1'b0;
      assign ic_araddr  = 32'h0;
      assign ic_rready  = 1'b0;
      assign core_illegal_instr = 1'b0;
      assign core_dbg_pc = 32'h0;
      assign core_dbg_halted = 1'b0;
    end
  endgenerate

  logic ext_lock;
  always_ff @(posedge clk) begin
    if (!rst_n) begin
      ext_lock <= 1'b0;
    end else begin
      if (!ext_lock && (ext_awvalid || ext_wvalid || ext_arvalid)) begin
        ext_lock <= 1'b1;
      end else if (ext_lock && ((m_bvalid && ext_bready) || (m_rvalid && ext_rready))) begin
        ext_lock <= 1'b0;
      end
    end
  end

  logic use_ext;
  logic m_awvalid;
  logic [31:0] m_awaddr;
  logic m_wvalid;
  logic [31:0] m_wdata;
  logic [3:0] m_wstrb;
  logic m_bready;
  logic m_arvalid;
  logic [31:0] m_araddr;
  logic m_rready;
  logic ar_was_core;
  always_ff @(posedge clk) begin
    if (!rst_n)
      ar_was_core <= 1'b0;
    else if (!use_ext && m_arvalid && m_arready)
      ar_was_core <= core_d_arvalid;
  end

  assign use_ext = ext_lock || ext_awvalid || ext_wvalid || ext_arvalid;
  assign m_awvalid = use_ext ? ext_awvalid : core_d_awvalid;
  assign m_awaddr = use_ext ? ext_awaddr : core_d_awaddr;
  assign m_wvalid = use_ext ? ext_wvalid : core_d_wvalid;
  assign m_wdata = use_ext ? ext_wdata : core_d_wdata;
  assign m_wstrb = use_ext ? ext_wstrb : core_d_wstrb;
  assign m_bready = use_ext ? ext_bready : core_d_bready;
  // Core data reads share AR with icache; multicycle CPU usually has one outstanding read — core has priority when both assert.
  assign m_arvalid = use_ext ? ext_arvalid : (core_d_arvalid ? 1'b1 : ic_arvalid);
  assign m_araddr = use_ext ? ext_araddr : (core_d_arvalid ? core_d_araddr : ic_araddr);
  assign m_rready = use_ext ? ext_rready : (ar_was_core ? core_d_rready : ic_rready);
  assign soc_activity = core_if_req_valid ^ core_if_resp_valid ^ m_arvalid ^ m_rvalid ^ core_d_awvalid ^ core_d_wvalid;
  assign illegal_instr = core_illegal_instr;
  assign gpio_out_obs = gpio_out;
  assign core_pc_obs = core_dbg_pc;
  assign core_halted_obs = core_dbg_halted;
  assign if_req_obs = core_if_req_valid;
  assign if_resp_obs = core_if_resp_valid;
  assign if_stall_obs = core_if_stall;

  logic m_awready;
  logic m_wready;
  logic m_bvalid;
  logic [1:0] m_bresp;
  logic m_arready;
  logic m_rvalid;
  logic [31:0] m_rdata;
  logic [1:0] m_rresp;

  assign ext_awready = use_ext ? m_awready : 1'b0;
  assign ext_wready  = use_ext ? m_wready  : 1'b0;
  assign ext_bvalid  = use_ext ? m_bvalid  : 1'b0;
  assign ext_bresp   = use_ext ? m_bresp   : 2'b00;
  assign ext_arready = use_ext ? m_arready : 1'b0;
  assign ext_rvalid  = use_ext ? m_rvalid  : 1'b0;
  assign ext_rdata   = use_ext ? m_rdata   : 32'h0;
  assign ext_rresp   = use_ext ? m_rresp   : 2'b00;

  assign core_d_awready = (!use_ext) ? m_awready : 1'b0;
  assign core_d_wready  = (!use_ext) ? m_wready : 1'b0;
  assign core_d_bvalid  = (!use_ext) ? m_bvalid : 1'b0;
  assign core_d_bresp   = (!use_ext) ? m_bresp : 2'b00;
  assign core_d_arready = (!use_ext) && m_arready && core_d_arvalid;
  assign core_d_rvalid  = (!use_ext) && m_rvalid && ar_was_core;
  assign core_d_rdata   = m_rdata;
  assign core_d_rresp   = m_rresp;
  assign ic_arready = (!use_ext) && m_arready && !core_d_arvalid && ic_arvalid;
  assign ic_rvalid = (!use_ext) && m_rvalid && !ar_was_core;
  assign ic_rdata = m_rdata;
  assign ic_rresp = (!use_ext) ? m_rresp : 2'b10;

  logic s0_awvalid, s0_awready, s0_wvalid, s0_wready, s0_bvalid, s0_bready, s0_arvalid, s0_arready, s0_rvalid, s0_rready;
  logic s1_awvalid, s1_awready, s1_wvalid, s1_wready, s1_bvalid, s1_bready, s1_arvalid, s1_arready, s1_rvalid, s1_rready;
  logic [31:0] s0_awaddr, s0_wdata, s0_araddr, s0_rdata, s1_awaddr, s1_wdata, s1_araddr, s1_rdata;
  logic [3:0] s0_wstrb, s1_wstrb;
  logic [1:0] s0_bresp, s0_rresp, s1_bresp, s1_rresp;

  axi4lite_xbar_1x2 u_xbar (
    .clk(clk), .rst_n(rst_n),
    .m_awvalid(m_awvalid), .m_awready(m_awready), .m_awaddr(m_awaddr),
    .m_wvalid(m_wvalid), .m_wready(m_wready), .m_wdata(m_wdata), .m_wstrb(m_wstrb),
    .m_bvalid(m_bvalid), .m_bready(m_bready), .m_bresp(m_bresp),
    .m_arvalid(m_arvalid), .m_arready(m_arready), .m_araddr(m_araddr),
    .m_rvalid(m_rvalid), .m_rready(m_rready), .m_rdata(m_rdata), .m_rresp(m_rresp),
    .s0_awvalid(s0_awvalid), .s0_awready(s0_awready), .s0_awaddr(s0_awaddr),
    .s0_wvalid(s0_wvalid), .s0_wready(s0_wready), .s0_wdata(s0_wdata), .s0_wstrb(s0_wstrb),
    .s0_bvalid(s0_bvalid), .s0_bready(s0_bready), .s0_bresp(s0_bresp),
    .s0_arvalid(s0_arvalid), .s0_arready(s0_arready), .s0_araddr(s0_araddr),
    .s0_rvalid(s0_rvalid), .s0_rready(s0_rready), .s0_rdata(s0_rdata), .s0_rresp(s0_rresp),
    .s1_awvalid(s1_awvalid), .s1_awready(s1_awready), .s1_awaddr(s1_awaddr),
    .s1_wvalid(s1_wvalid), .s1_wready(s1_wready), .s1_wdata(s1_wdata), .s1_wstrb(s1_wstrb),
    .s1_bvalid(s1_bvalid), .s1_bready(s1_bready), .s1_bresp(s1_bresp),
    .s1_arvalid(s1_arvalid), .s1_arready(s1_arready), .s1_araddr(s1_araddr),
    .s1_rvalid(s1_rvalid), .s1_rready(s1_rready), .s1_rdata(s1_rdata), .s1_rresp(s1_rresp)
  );

  generate
    if (USE_FPGA_RAM) begin : g_mem_ram
      localparam integer MEM_WORDS_P = (PSRAM_WORDS != 4096) ? PSRAM_WORDS : RAM_WORDS;
      if (USE_DUAL_RAM) begin : g_mem_dual
        axi4lite_ram_dual #(
          .BANK0_WORDS(MEM_WORDS_P),
          .BANK1_WORDS(RAM_BANK1_WORDS),
          .BASE_ADDR(32'h0000_0000),
          .ENABLE_FW_BOOTLOAD(ENABLE_FW_BOOTLOAD),
          .BOOT_INIT_MEMH(BOOT_INIT_MEMH)
        ) u_ram_dual (
          .clk(clk),
          .rst_n(rst_n),
          .fw_ready(mem_fw_ready),
          .s_awvalid(s0_awvalid),
          .s_awready(s0_awready),
          .s_awaddr(s0_awaddr),
          .s_wvalid(s0_wvalid),
          .s_wready(s0_wready),
          .s_wdata(s0_wdata),
          .s_wstrb(s0_wstrb),
          .s_bvalid(s0_bvalid),
          .s_bready(s0_bready),
          .s_bresp(s0_bresp),
          .s_arvalid(s0_arvalid),
          .s_arready(s0_arready),
          .s_araddr(s0_araddr),
          .s_rvalid(s0_rvalid),
          .s_rready(s0_rready),
          .s_rdata(s0_rdata),
          .s_rresp(s0_rresp)
        );
      end else begin : g_mem_single
        axi4lite_ram #(
          .MEM_WORDS(MEM_WORDS_P),
          .BASE_ADDR(32'h0000_0000),
          .ENABLE_FW_BOOTLOAD(ENABLE_FW_BOOTLOAD),
          .BOOT_INIT_MEMH(BOOT_INIT_MEMH)
        ) u_ram (
          .clk(clk),
          .rst_n(rst_n),
          .fw_ready(mem_fw_ready),
          .s_awvalid(s0_awvalid),
          .s_awready(s0_awready),
          .s_awaddr(s0_awaddr),
          .s_wvalid(s0_wvalid),
          .s_wready(s0_wready),
          .s_wdata(s0_wdata),
          .s_wstrb(s0_wstrb),
          .s_bvalid(s0_bvalid),
          .s_bready(s0_bready),
          .s_bresp(s0_bresp),
          .s_arvalid(s0_arvalid),
          .s_arready(s0_arready),
          .s_araddr(s0_araddr),
          .s_rvalid(s0_rvalid),
          .s_rready(s0_rready),
          .s_rdata(s0_rdata),
          .s_rresp(s0_rresp)
        );
      end
    end else begin : g_mem_psram
      axi4lite_psram #(
        .MEM_WORDS((PSRAM_WORDS != 4096) ? PSRAM_WORDS : RAM_WORDS),
        .READ_LATENCY(PSRAM_READ_LATENCY),
        .BASE_ADDR(32'h0000_0000),
        .ENABLE_FW_BOOTLOAD(ENABLE_FW_BOOTLOAD),
        .USE_READMEMH(USE_READMEMH)
      ) u_psram (
        .clk(clk), .rst_n(rst_n),
        .fw_ready(mem_fw_ready),
        .s_awvalid(s0_awvalid), .s_awready(s0_awready), .s_awaddr(s0_awaddr),
        .s_wvalid(s0_wvalid), .s_wready(s0_wready), .s_wdata(s0_wdata), .s_wstrb(s0_wstrb),
        .s_bvalid(s0_bvalid), .s_bready(s0_bready), .s_bresp(s0_bresp),
        .s_arvalid(s0_arvalid), .s_arready(s0_arready), .s_araddr(s0_araddr),
        .s_rvalid(s0_rvalid), .s_rready(s0_rready), .s_rdata(s0_rdata), .s_rresp(s0_rresp)
      );
    end
  endgenerate

  logic        psel, penable, pwrite, pready, pslverr, uart_irq, timer_irq, sd_spi_irq;
  logic [31:0] gpio_out;
  logic [31:0] paddr, pwdata, prdata;
  axi_to_apb_bridge u_a2p (
    .clk(clk), .rst_n(rst_n),
    .s_awvalid(s1_awvalid), .s_awready(s1_awready), .s_awaddr(s1_awaddr),
    .s_wvalid(s1_wvalid), .s_wready(s1_wready), .s_wdata(s1_wdata), .s_wstrb(s1_wstrb),
    .s_bvalid(s1_bvalid), .s_bready(s1_bready), .s_bresp(s1_bresp),
    .s_arvalid(s1_arvalid), .s_arready(s1_arready), .s_araddr(s1_araddr),
    .s_rvalid(s1_rvalid), .s_rready(s1_rready), .s_rdata(s1_rdata), .s_rresp(s1_rresp),
    .psel(psel), .penable(penable), .pwrite(pwrite), .paddr(paddr), .pwdata(pwdata),
    .prdata(prdata), .pready(pready), .pslverr(pslverr)
  );

  apb_decoder #(
    .ENABLE_UART(ENABLE_UART),
    .ENABLE_TIMER(ENABLE_TIMER),
    .ENABLE_GPIO(ENABLE_GPIO),
    .ENABLE_SD_SPI(ENABLE_SD_SPI),
    .SD_MMIO_MODE(SD_MMIO_MODE),
    .SD_BACKEND(SD_BACKEND),
    .SD_USE_CARD_MEM(SD_USE_CARD_MEM),
    .UART_CLK_MHZ(UART_CLK_MHZ),
    .UART_BAUD(UART_BAUD)
  ) u_apb_dec (
    .pclk(clk), .presetn(rst_n),
    .psel(psel), .penable(penable), .pwrite(pwrite),
    .paddr(paddr), .pwdata(pwdata),
    .prdata(prdata), .pready(pready), .pslverr(pslverr),
    .uart_irq(uart_irq), .timer_irq(timer_irq), .sd_spi_irq(sd_spi_irq), .gpio_out(gpio_out), .uart_tx(uart_tx), .uart_rx(uart_rx),
    .sd_spi_sck(sd_spi_sck), .sd_spi_mosi(sd_spi_mosi), .sd_spi_miso(sd_spi_miso), .sd_spi_cs_n(sd_spi_cs_n),
    .IO_sdio_cmd(IO_sdio_cmd), .IO_sdio_dat0(IO_sdio_dat0), .IO_sdio_dat1_irq(IO_sdio_dat1_irq),
    .IO_sdio_dat2_rw(IO_sdio_dat2_rw), .IO_sdio_dat3_cd(IO_sdio_dat3_cd)
  );

  assign irq_lines = {29'h0, sd_spi_irq, uart_irq, timer_irq};
endmodule
