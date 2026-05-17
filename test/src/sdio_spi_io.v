// SPI pad drivers for SDIO_SPI_Top (Disable I/O Insertion).
module sdio_spi_io (
  input  wire sck_i,
  output wire sck_o,
  input  wire mosi_i,
  output wire mosi_o,
  input  wire cs_n_i,
  output wire cs_n_o,
  input  wire miso_pad,
  output wire miso_to_ip
);
  assign sck_o      = sck_i;
  assign mosi_o     = mosi_i;
  assign cs_n_o     = cs_n_i;
  assign miso_to_ip = miso_pad;
endmodule
