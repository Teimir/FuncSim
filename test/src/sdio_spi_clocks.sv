// Clock enables for Gowin SDIO_SPI_Top from 27 MHz SoC clock.
module sdio_spi_clocks (
  input  logic clk27,
  input  logic rst_n,
  output logic clk_ip,
  output logic clk_cpu,
  output logic clk_sdio,
  output logic clk_2m
);
  logic [15:0] div_sdio;
  logic [12:0] div_2m;

  assign clk_ip = clk27;
  assign clk_cpu = clk27;

  always_ff @(posedge clk27) begin
    if (!rst_n) begin
      div_sdio <= 16'd0;
      div_2m <= 13'd0;
    end else begin
      div_sdio <= div_sdio + 16'd1;
      div_2m <= div_2m + 13'd1;
    end
  end

  // ~400 kHz init clock from 27 MHz (toggle every 33 cycles)
  assign clk_sdio = div_sdio[5];
  // ~2 MHz (toggle every 6-7 cycles)
  assign clk_2m = div_2m[3];
endmodule
