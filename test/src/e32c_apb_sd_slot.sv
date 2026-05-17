// SD MMIO slot @ 0xFFFF_3000: block or SPI register map; SHIM or Gowin SDIO_SPI pins.
module e32c_apb_sd_slot #(
  parameter bit SD_MMIO_MODE = 1'b1,  // 0=block, 1=spi
  parameter bit SD_BACKEND = 1'b0,     // 0=SHIM (Icarus), 1=GOWIN_IP (synth)
  parameter bit SD_USE_CARD_MEM = 1'b1, // 0 on TN9K FPGA: 512x32 sector RAM blows DFF budget
  parameter int UART_CLK_MHZ = 27
) (
  input  logic        pclk,
  input  logic        presetn,
  input  logic        psel,
  input  logic        penable,
  input  logic        pwrite,
  input  logic [31:0] paddr,
  input  logic [31:0] pwdata,
  output logic [31:0] prdata,
  output logic        pready,
  output logic        pslverr,
  output logic        irq,
  output logic        spi_sck,
  output logic        spi_mosi,
  input  logic        spi_miso,
  output logic        spi_cs_n,
  inout  wire         IO_sdio_cmd,
  inout  wire         IO_sdio_dat0,
  inout  wire         IO_sdio_dat1_irq,
  inout  wire         IO_sdio_dat2_rw,
  inout  wire         IO_sdio_dat3_cd
);
  logic [31:0] shim_prdata;
  logic        shim_pready;
  logic        shim_pslverr;
  logic        shim_irq;
  logic        shim_sck, shim_mosi, shim_cs_n;

  logic        gowin_sck, gowin_mosi, gowin_cs_n;

  generate
    if (SD_MMIO_MODE == 1'b0) begin : g_block
      apb_sd_block u_block (
        .pclk(pclk),
        .presetn(presetn),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .paddr(paddr),
        .pwdata(pwdata),
        .prdata(shim_prdata),
        .pready(shim_pready),
        .pslverr(shim_pslverr),
        .irq(shim_irq)
      );
      assign shim_sck = 1'b0;
      assign shim_mosi = 1'b1;
      assign shim_cs_n = 1'b1;
    end else begin : g_spi
      apb_sdio_spi_bridge #(
        .DRIVE_SPI_PINS(SD_BACKEND == 1'b0),
        .USE_CARD_MEM(SD_USE_CARD_MEM && (SD_BACKEND == 1'b0)),
        .CARD_MEM_WORDS(512)
      ) u_bridge (
        .pclk(pclk),
        .presetn(presetn),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .paddr(paddr),
        .pwdata(pwdata),
        .prdata(shim_prdata),
        .pready(shim_pready),
        .pslverr(shim_pslverr),
        .irq(shim_irq),
        .spi_sck(shim_sck),
        .spi_mosi(shim_mosi),
        .spi_miso(spi_miso),
        .spi_cs_n(shim_cs_n)
      );
    end

    if (SD_BACKEND == 1'b0) begin : g_pins_shim
      assign spi_sck = shim_sck;
      assign spi_mosi = shim_mosi;
      assign spi_cs_n = shim_cs_n;
    end else begin : g_pins_gowin
      assign spi_sck = gowin_sck;
      assign spi_mosi = gowin_mosi;
      assign spi_cs_n = gowin_cs_n;
    end
  endgenerate

  assign prdata = shim_prdata;
  assign pready = shim_pready;
  assign pslverr = shim_pslverr;
  assign irq = shim_irq;

  generate
    if (SD_BACKEND == 1'b0) begin : g_sdio_float
      assign IO_sdio_cmd = 1'bz;
      assign IO_sdio_dat0 = 1'bz;
      assign IO_sdio_dat1_irq = 1'bz;
      assign IO_sdio_dat2_rw = 1'bz;
      assign IO_sdio_dat3_cd = 1'bz;
    end
  endgenerate

  generate
    if (SD_BACKEND == 1'b1) begin : g_sdio_ip
      sdio_spi_soc_wrapper u_sdio (
        .clk(pclk),
        .rst_n(presetn),
        .IO_sdio_cmd(IO_sdio_cmd),
        .IO_sdio_dat0(IO_sdio_dat0),
        .IO_sdio_dat1_irq(IO_sdio_dat1_irq),
        .IO_sdio_dat2_rw(IO_sdio_dat2_rw),
        .IO_sdio_dat3_cd(IO_sdio_dat3_cd),
        .spi_sck(gowin_sck),
        .spi_mosi(gowin_mosi),
        .spi_miso(spi_miso),
        .spi_cs_n(gowin_cs_n)
      );
    end
  endgenerate
endmodule
