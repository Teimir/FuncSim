// Tang Nano 9K: Gowin SDIO_SPI_Top (SPI1). SDIO inouts must reach top-level pads (IP: Disable I/O Insertion).
`ifndef E32C_SIM_ICARUS
module sdio_spi_soc_wrapper (
  input  logic clk,
  input  logic rst_n,
  inout  wire IO_sdio_cmd,
  inout  wire IO_sdio_dat0,
  inout  wire IO_sdio_dat1_irq,
  inout  wire IO_sdio_dat2_rw,
  inout  wire IO_sdio_dat3_cd,
  output logic spi_sck,
  output logic spi_mosi,
  input  logic spi_miso,
  output logic spi_cs_n
);
  logic clk_ip, clk_cpu, clk_sdio, clk_2m;

  sdio_spi_clocks u_clocks (
    .clk27(clk),
    .rst_n(rst_n),
    .clk_ip(clk_ip),
    .clk_cpu(clk_cpu),
    .clk_sdio(clk_sdio),
    .clk_2m(clk_2m)
  );

  logic ip_sck, ip_mosi, ip_cs_n, miso_to_ip;

  SDIO_SPI_Top u_ip (
    .I_clk(clk_ip),
    .I_rst_n(rst_n),
    .I_sdio_2M_clk(clk_2m),
    .I_sdio_cpu_clk(clk_cpu),
    .I_sdio_clk(clk_sdio),
    .IO_sdio_cmd(IO_sdio_cmd),
    .IO_sdio_dat0(IO_sdio_dat0),
    .IO_sdio_dat1_irq(IO_sdio_dat1_irq),
    .IO_sdio_dat2_rw(IO_sdio_dat2_rw),
    .IO_sdio_dat3_cd(IO_sdio_dat3_cd),
    .O_spi1_cs_n(ip_cs_n),
    .O_spi_sclk(ip_sck),
    .O_spi_mosi(ip_mosi),
    .I_spi_miso(miso_to_ip)
  );

  sdio_spi_io u_io (
    .sck_i(ip_sck),
    .sck_o(spi_sck),
    .mosi_i(ip_mosi),
    .mosi_o(spi_mosi),
    .cs_n_i(ip_cs_n),
    .cs_n_o(spi_cs_n),
    .miso_pad(spi_miso),
    .miso_to_ip(miso_to_ip)
  );
endmodule
`else
// Icarus: empty wrapper (SD_BACKEND=SHIM uses apb_sd_spi pins only).
module sdio_spi_soc_wrapper (
  input  logic clk,
  input  logic rst_n,
  inout  wire IO_sdio_cmd,
  inout  wire IO_sdio_dat0,
  inout  wire IO_sdio_dat1_irq,
  inout  wire IO_sdio_dat2_rw,
  inout  wire IO_sdio_dat3_cd,
  output logic spi_sck,
  output logic spi_mosi,
  input  logic spi_miso,
  output logic spi_cs_n
);
  assign IO_sdio_cmd = 1'bz;
  assign IO_sdio_dat0 = 1'bz;
  assign IO_sdio_dat1_irq = 1'bz;
  assign IO_sdio_dat2_rw = 1'bz;
  assign IO_sdio_dat3_cd = 1'bz;
  assign spi_sck = 1'b0;
  assign spi_mosi = 1'b1;
  assign spi_cs_n = 1'b1;
endmodule
`endif
