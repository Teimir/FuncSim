// Two contiguous AXI RAM banks: bank0 @ BASE, bank1 @ BASE + BANK0_WORDS*4.
// Optional reset copy of firmware_rom.svh into bank0 (bootloader / PZU image).
module axi4lite_ram_dual #(
  parameter integer BANK0_WORDS = 8192,
  parameter integer BANK1_WORDS = 8192,
  parameter [31:0] BASE_ADDR = 32'h0000_0000,
  parameter bit ENABLE_FW_BOOTLOAD = 1'b0,
  parameter bit BOOT_INIT_MEMH = 1'b0
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
  output logic        s_bvalid,
  input  logic        s_bready,
  output logic [1:0]  s_bresp,
  input  logic        s_arvalid,
  output logic        s_arready,
  input  logic [31:0] s_araddr,
  output logic        s_rvalid,
  input  logic        s_rready,
  output logic [31:0] s_rdata,
  output logic [1:0]  s_rresp
);
  localparam [31:0] BANK1_BASE = BASE_ADDR + (BANK0_WORDS * 32'd4);

  logic        b0_awvalid, b0_wvalid, b0_arvalid, b0_bvalid, b0_rvalid;
  logic        b0_awready, b0_wready, b0_arready, b0_bready, b0_rready;
  logic [31:0] b0_awaddr, b0_wdata, b0_araddr, b0_rdata;
  logic [3:0]  b0_wstrb;
  logic [1:0]  b0_bresp, b0_rresp;
  logic        b0_fw_ready;

  logic        b1_fw_ready;
  logic        b1_awvalid, b1_wvalid, b1_arvalid, b1_bvalid, b1_rvalid;
  logic        b1_awready, b1_wready, b1_arready, b1_bready, b1_rready;
  logic [31:0] b1_awaddr, b1_wdata, b1_araddr, b1_rdata;
  logic [3:0]  b1_wstrb;
  logic [1:0]  b1_bresp, b1_rresp;

  logic sel_aw, sel_w, sel_ar;
  logic in_b0, in_b1, in_r0, in_r1;

  assign fw_ready = b0_fw_ready;
  assign sel_aw = (s_awaddr >= BANK1_BASE);
  assign sel_w  = (s_awaddr >= BANK1_BASE);
  assign sel_ar = (s_araddr >= BANK1_BASE);

  assign b0_awvalid = s_awvalid && !sel_aw;
  assign b0_awaddr  = s_awaddr;
  assign b0_wvalid  = s_wvalid && !sel_w;
  assign b0_wdata   = s_wdata;
  assign b0_wstrb   = s_wstrb;
  assign b0_arvalid = s_arvalid && !sel_ar;
  assign b0_araddr  = s_araddr;

  assign b1_awvalid = s_awvalid && sel_aw;
  assign b1_awaddr  = s_awaddr;
  assign b1_wvalid  = s_wvalid && sel_w;
  assign b1_wdata   = s_wdata;
  assign b1_wstrb   = s_wstrb;
  assign b1_arvalid = s_arvalid && sel_ar;
  assign b1_araddr  = s_araddr;

  assign in_b0 = b0_bvalid && b0_bready;
  assign in_b1 = b1_bvalid && b1_bready;
  assign in_r0 = b0_rvalid && b0_rready;
  assign in_r1 = b1_rvalid && b1_rready;

  assign s_awready = sel_aw ? b1_awready : b0_awready;
  assign s_wready  = sel_w ? b1_wready : b0_wready;
  assign s_arready = sel_ar ? b1_arready : b0_arready;

  assign s_bvalid = b0_bvalid | b1_bvalid;
  assign s_bresp  = in_b1 ? b1_bresp : b0_bresp;
  assign b0_bready = s_bready && b0_bvalid;
  assign b1_bready = s_bready && b1_bvalid;

  assign s_rvalid = b0_rvalid | b1_rvalid;
  assign s_rdata  = in_r1 ? b1_rdata : b0_rdata;
  assign s_rresp  = in_r1 ? b1_rresp : b0_rresp;
  assign b0_rready = s_rready && b0_rvalid;
  assign b1_rready = s_rready && b1_rvalid;

  axi4lite_ram #(
    .MEM_WORDS(BANK0_WORDS),
    .BASE_ADDR(BASE_ADDR),
    .ENABLE_FW_BOOTLOAD(ENABLE_FW_BOOTLOAD),
    .BOOT_INIT_MEMH(BOOT_INIT_MEMH)
  ) u_bank0 (
    .clk(clk),
    .rst_n(rst_n),
    .fw_ready(b0_fw_ready),
    .s_awvalid(b0_awvalid),
    .s_awready(b0_awready),
    .s_awaddr(b0_awaddr),
    .s_wvalid(b0_wvalid),
    .s_wready(b0_wready),
    .s_wdata(b0_wdata),
    .s_wstrb(b0_wstrb),
    .s_bvalid(b0_bvalid),
    .s_bready(b0_bready),
    .s_bresp(b0_bresp),
    .s_arvalid(b0_arvalid),
    .s_arready(b0_arready),
    .s_araddr(b0_araddr),
    .s_rvalid(b0_rvalid),
    .s_rready(b0_rready),
    .s_rdata(b0_rdata),
    .s_rresp(b0_rresp)
  );

  axi4lite_ram #(
    .MEM_WORDS(BANK1_WORDS),
    .BASE_ADDR(BANK1_BASE),
    .ENABLE_FW_BOOTLOAD(1'b0)
  ) u_bank1 (
    .clk(clk),
    .rst_n(rst_n),
    .fw_ready(b1_fw_ready),
    .s_awvalid(b1_awvalid),
    .s_awready(b1_awready),
    .s_awaddr(b1_awaddr),
    .s_wvalid(b1_wvalid),
    .s_wready(b1_wready),
    .s_wdata(b1_wdata),
    .s_wstrb(b1_wstrb),
    .s_bvalid(b1_bvalid),
    .s_bready(b1_bready),
    .s_bresp(b1_bresp),
    .s_arvalid(b1_arvalid),
    .s_arready(b1_arready),
    .s_araddr(b1_araddr),
    .s_rvalid(b1_rvalid),
    .s_rready(b1_rready),
    .s_rdata(b1_rdata),
    .s_rresp(b1_rresp)
  );
endmodule
