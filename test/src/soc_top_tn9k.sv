// Tang Nano 9K: icache + два BSRAM. Загрузка firmware_rom.svh; один порт записи в ram.sv.
module soc_top_tn9k #(
  // Частота кварца (МГц); при мусоре в UART попробовать 28–30.
  parameter int UART_CLK_MHZ = 27,
  parameter bit SD_MMIO_MODE = 1'b1,
  parameter bit SD_BACKEND = 1'b0,
  // Буфер сектора 512×32 не влезает в BSRAM GW1NR → ~16k DFF (RP0006 при лимите 8640 LUT).
  parameter bit SD_USE_CARD_MEM = 1'b0,
  // 0: UART-only (~6.8k LUT). 1: +MMIO SD shim (~+1.8k LUT, риск RP0006).
  parameter bit ENABLE_SD_SPI = 1'b0,
  parameter bit ENABLE_TIMER = 1'b0,
  parameter bit ENABLE_GPIO = 1'b0
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
  output logic        soc_activity,
  output logic        illegal_instr,
  output logic [31:0] gpio_out_obs,
  output logic [31:0] core_pc_obs,
  output logic        core_halted_obs,
  output logic        if_req_obs,
  output logic        if_resp_obs,
  output logic        if_stall_obs
);
  localparam integer TN9K_DATA_BANK0_WORDS = 8192;
  localparam integer TN9K_DATA_BANK1_WORDS = 2048;

  // Gowin EX3434: к inout в soc_top только net (wire), не logic.
  wire IO_sdio_cmd;
  wire IO_sdio_dat0;
  wire IO_sdio_dat1_irq;
  wire IO_sdio_dat2_rw;
  wire IO_sdio_dat3_cd;

  soc_top #(
    .UART_CLK_MHZ(UART_CLK_MHZ),
    .RAM_WORDS(TN9K_DATA_BANK0_WORDS),
    .PSRAM_WORDS(TN9K_DATA_BANK0_WORDS),
    .RAM_BANK1_WORDS(TN9K_DATA_BANK1_WORDS),
    .USE_DUAL_RAM(1'b1),
    .ENABLE_CORE(1),
    .USE_LITE_CORE(0),
    .USE_TN9K_CORE(1'b1),
    .FORCE_IF_NOP_FETCH(1'b0),
    .ENABLE_UART(1),
    .ENABLE_TIMER(ENABLE_TIMER),
    .ENABLE_GPIO(ENABLE_GPIO),
    .ENABLE_SD_SPI(ENABLE_SD_SPI),
    .SD_MMIO_MODE(SD_MMIO_MODE),
    .SD_BACKEND(SD_BACKEND),
    .SD_USE_CARD_MEM(SD_USE_CARD_MEM),
    .ENABLE_FW_BOOTLOAD(1'b1),
    .USE_FPGA_RAM(1'b1),
    .USE_READMEMH(1'b0)
  ) u_soc (
    .clk(clk),
    .rst_n(rst_n),
    .ext_awvalid(ext_awvalid),
    .ext_awready(ext_awready),
    .ext_awaddr(ext_awaddr),
    .ext_wvalid(ext_wvalid),
    .ext_wready(ext_wready),
    .ext_wdata(ext_wdata),
    .ext_wstrb(ext_wstrb),
    .ext_bvalid(ext_bvalid),
    .ext_bready(ext_bready),
    .ext_bresp(ext_bresp),
    .ext_arvalid(ext_arvalid),
    .ext_arready(ext_arready),
    .ext_araddr(ext_araddr),
    .ext_rvalid(ext_rvalid),
    .ext_rready(ext_rready),
    .ext_rdata(ext_rdata),
    .ext_rresp(ext_rresp),
    .uart_tx(uart_tx),
    .uart_rx(uart_rx),
    .sd_spi_sck(sd_spi_sck),
    .sd_spi_mosi(sd_spi_mosi),
    .sd_spi_miso(sd_spi_miso),
    .sd_spi_cs_n(sd_spi_cs_n),
    .IO_sdio_cmd(IO_sdio_cmd),
    .IO_sdio_dat0(IO_sdio_dat0),
    .IO_sdio_dat1_irq(IO_sdio_dat1_irq),
    .IO_sdio_dat2_rw(IO_sdio_dat2_rw),
    .IO_sdio_dat3_cd(IO_sdio_dat3_cd),
    .soc_activity(soc_activity),
    .illegal_instr(illegal_instr),
    .gpio_out_obs(gpio_out_obs),
    .core_pc_obs(core_pc_obs),
    .core_halted_obs(core_halted_obs),
    .if_req_obs(if_req_obs),
    .if_resp_obs(if_resp_obs),
    .if_stall_obs(if_stall_obs)
  );
endmodule
