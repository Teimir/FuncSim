module apb_decoder #(
  parameter ENABLE_UART = 1,
  parameter ENABLE_TIMER = 1,
  parameter ENABLE_GPIO = 1,
  parameter ENABLE_SD_SPI = 1,
  parameter int UART_CLK_MHZ = 27,
  parameter int UART_BAUD = 115200
) (
  input logic        pclk,
  input logic        presetn,
  input logic        psel,
  input logic        penable,
  input logic        pwrite,
  input logic [31:0] paddr,
  input logic [31:0] pwdata,
  output logic  [31:0] prdata,
  output logic         pready,
  output logic         pslverr,
  output logic        uart_irq,
  output logic        timer_irq,
  output logic        sd_spi_irq,
  output logic [31:0] gpio_out,
  output logic        uart_tx,
  input logic        uart_rx,
  output logic        sd_spi_sck,
  output logic        sd_spi_mosi,
  input logic        sd_spi_miso,
  output logic        sd_spi_cs_n
);
`include "mmio_generated.svh"
  logic hit_uart;
  logic hit_timer;
  logic hit_gpio;
  logic hit_sd_spi;
  logic sel_uart;
  logic sel_timer;
  logic sel_gpio;
  logic sel_sd_spi;
  assign hit_uart = (paddr[31:12] == `E32C_UART_PAGE);
  assign hit_timer = (paddr[31:12] == `E32C_TIMER_PAGE);
  assign hit_gpio = (paddr[31:12] == `E32C_GPIO_PAGE);
  assign hit_sd_spi = (paddr[31:12] == `E32C_SD_SPI_PAGE);
  assign sel_uart = psel && ENABLE_UART && hit_uart;
  assign sel_timer = psel && ENABLE_TIMER && hit_timer;
  assign sel_gpio = psel && ENABLE_GPIO && hit_gpio;
  assign sel_sd_spi = psel && ENABLE_SD_SPI && hit_sd_spi;

  logic [31:0] uart_prdata;
  logic uart_pready;
  logic uart_pslverr;
  logic [31:0] timer_prdata;
  logic timer_pready;
  logic timer_pslverr;
  logic [31:0] gpio_prdata;
  logic gpio_pready;
  logic gpio_pslverr;
  logic [31:0] sd_spi_prdata;
  logic sd_spi_pready;
  logic sd_spi_pslverr;
  logic uart_irq_int;
  logic timer_irq_int;
  logic [31:0] gpio_out_int;
  logic sd_spi_irq_int;

  apb_uart #(
    .CLK_FRE_MHZ(UART_CLK_MHZ),
    .BAUD_RATE(UART_BAUD)
  ) u_uart (
    .pclk(pclk),
    .presetn(presetn),
    .psel(sel_uart),
    .penable(penable),
    .pwrite(pwrite),
    .paddr(paddr - `E32C_UART_BASE),
    .pwdata(pwdata),
    .prdata(uart_prdata),
    .pready(uart_pready),
    .pslverr(uart_pslverr),
    .irq(uart_irq_int),
    .uart_tx(uart_tx),
    .uart_rx(uart_rx)
  );

  apb_timer u_timer (
    .pclk(pclk),
    .presetn(presetn),
    .psel(sel_timer),
    .penable(penable),
    .pwrite(pwrite),
    .paddr(paddr - `E32C_TIMER_BASE),
    .pwdata(pwdata),
    .prdata(timer_prdata),
    .pready(timer_pready),
    .pslverr(timer_pslverr),
    .irq(timer_irq_int)
  );

  (* keep = "true", syn_preserve = 1 *) apb_gpio u_gpio (
    .pclk(pclk),
    .presetn(presetn),
    .psel(sel_gpio),
    .penable(penable),
    .pwrite(pwrite),
    .paddr(paddr - `E32C_GPIO_BASE),
    .pwdata(pwdata),
    .prdata(gpio_prdata),
    .pready(gpio_pready),
    .pslverr(gpio_pslverr),
    .gpio_out(gpio_out_int)
  );

  generate
    if (ENABLE_SD_SPI) begin : g_sdspi_on
      (* keep = "true", syn_preserve = 1 *) apb_sd_spi u_sd_spi (
        .pclk(pclk),
        .presetn(presetn),
        .psel(sel_sd_spi),
        .penable(penable),
        .pwrite(pwrite),
        .paddr(paddr - `E32C_SD_SPI_BASE),
        .pwdata(pwdata),
        .prdata(sd_spi_prdata),
        .pready(sd_spi_pready),
        .pslverr(sd_spi_pslverr),
        .irq(sd_spi_irq_int),
        .spi_sck(sd_spi_sck),
        .spi_mosi(sd_spi_mosi),
        .spi_miso(sd_spi_miso),
        .spi_cs_n(sd_spi_cs_n)
      );
    end else begin : g_sdspi_off
      assign sd_spi_prdata = 32'h0;
      assign sd_spi_pready = 1'b1;
      assign sd_spi_pslverr = 1'b0;
      assign sd_spi_irq_int = 1'b0;
      assign sd_spi_sck = 1'b0;
      assign sd_spi_mosi = 1'b0;
      assign sd_spi_cs_n = 1'b1;
    end
  endgenerate

  assign uart_irq = ENABLE_UART ? uart_irq_int : 1'b0;
  assign timer_irq = ENABLE_TIMER ? timer_irq_int : 1'b0;
  assign gpio_out = ENABLE_GPIO ? gpio_out_int : 32'h0;
  assign sd_spi_irq = ENABLE_SD_SPI ? sd_spi_irq_int : 1'b0;

  always_comb begin
    if (sel_uart) begin
      prdata = uart_prdata;
      pready = uart_pready;
      pslverr = uart_pslverr;
    end else if (sel_timer) begin
      prdata = timer_prdata;
      pready = timer_pready;
      pslverr = timer_pslverr;
    end else if (sel_gpio) begin
      prdata = gpio_prdata;
      pready = gpio_pready;
      pslverr = gpio_pslverr;
    end else if (sel_sd_spi) begin
      prdata = sd_spi_prdata;
      pready = sd_spi_pready;
      pslverr = sd_spi_pslverr;
    end else begin
      prdata = 32'h0;
      pready = 1'b1;
      // Unmapped region or disabled target block -> SLVERR on access.
      pslverr = psel;
    end
  end
endmodule
