// APB MMIO front-end for SD SPI (Python / apb_sd_spi register map).
// When DRIVE_SPI_PINS=0, shim keeps MMIO state but SPI pads are driven by Gowin SDIO_SPI_Top.
module apb_sdio_spi_bridge #(
  parameter bit DRIVE_SPI_PINS = 1'b1,
  parameter bit USE_CARD_MEM = 1'b1,
  parameter int CARD_MEM_WORDS = 512
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
  output logic        spi_cs_n
);
  logic shim_sck, shim_mosi, shim_cs_n;

  apb_sd_spi #(
    .USE_CARD_MEM(USE_CARD_MEM),
    .CARD_MEM_WORDS(CARD_MEM_WORDS)
  ) u_mmio (
    .pclk(pclk),
    .presetn(presetn),
    .psel(psel),
    .penable(penable),
    .pwrite(pwrite),
    .paddr(paddr),
    .pwdata(pwdata),
    .prdata(prdata),
    .pready(pready),
    .pslverr(pslverr),
    .irq(irq),
    .spi_sck(shim_sck),
    .spi_mosi(shim_mosi),
    .spi_miso(spi_miso),
    .spi_cs_n(shim_cs_n)
  );

  generate
    if (DRIVE_SPI_PINS) begin : g_drive
      assign spi_sck  = shim_sck;
      assign spi_mosi = shim_mosi;
      assign spi_cs_n = shim_cs_n;
    end else begin : g_idle
      assign spi_sck  = 1'b0;
      assign spi_mosi = 1'b1;
      assign spi_cs_n = 1'b1;
    end
  endgenerate
endmodule
