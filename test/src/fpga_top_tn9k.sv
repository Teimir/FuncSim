module fpga_top_tn9k #(
  // 1: UART test stream (no SoC). 0: normal SoC + firmware (after bring-up OK).
  parameter USE_HW_UART_STREAM = 1'b0,
  // 0: MMIO shim on SPI pins (~fits 8640 LUT). 1: Gowin SDIO_SPI_Top (overflow on TN9K).
  parameter bit SD_BACKEND = 1'b0
) (
  input  logic       clk27,
  input  logic       user_btn_n, // optional; extend reset if wired
  output logic       uart_tx,
  input  logic       uart_rx, // unused; tied high inside when SoC off
  output logic [5:0] user_led,
  output logic       sd_spi_sck,
  output logic       sd_spi_mosi,
  input  logic       sd_spi_miso,
  output logic       sd_spi_cs_n
);
  logic [15:0] rst_cnt;
  logic        rst_n_por;
  logic        rst_n;
  logic        soc_uart_tx;
  logic [23:0] hb;
  logic [31:0] gpio_out_obs;
  logic [31:0] core_pc_obs;
  logic        core_halted_obs;
  logic        illegal_instr_obs;
  logic        in_handler;
  logic        in_handler_d;
  logic        led4_tgl;

  always_ff @(posedge clk27) begin
    if (!rst_n_por)
      rst_cnt <= rst_cnt + 16'd1;
  end

  // POR only; do not gate on user_btn_n (pin 3 may be unwired / wrong on some boards).
  assign rst_n_por = &rst_cnt;
  assign rst_n     = rst_n_por;

  generate
    if (!USE_HW_UART_STREAM) begin : g_soc
      soc_top_tn9k #(
        .SD_MMIO_MODE(1'b1),
        .SD_BACKEND(SD_BACKEND)
      ) u_soc (
        .clk(clk27),
        .rst_n(rst_n),
        .ext_awvalid(1'b0),
        .ext_awready(),
        .ext_awaddr(32'h0),
        .ext_wvalid(1'b0),
        .ext_wready(),
        .ext_wdata(32'h0),
        .ext_wstrb(4'h0),
        .ext_bvalid(),
        .ext_bready(1'b0),
        .ext_bresp(),
        .ext_arvalid(1'b0),
        .ext_arready(),
        .ext_araddr(32'h0),
        .ext_rvalid(),
        .ext_rready(1'b1),
        .ext_rdata(),
        .ext_rresp(),
        .uart_tx(soc_uart_tx),
        .uart_rx(1'b1),
        .sd_spi_sck(sd_spi_sck),
        .sd_spi_mosi(sd_spi_mosi),
        .sd_spi_miso(sd_spi_miso),
        .sd_spi_cs_n(sd_spi_cs_n),
        .soc_activity(),
        .illegal_instr(illegal_instr_obs),
        .gpio_out_obs(gpio_out_obs),
        .core_pc_obs(core_pc_obs),
        .core_halted_obs(core_halted_obs),
        .if_req_obs(),
        .if_resp_obs(),
        .if_stall_obs()
      );
      assign uart_tx = soc_uart_tx;
    end else begin : g_uart_bringup
      // 27 MHz: CLK_PER_BIT 281 ≈ 9600, 234 ≈ 115200. Try both in terminal.
      // Pattern 'H' (0x48). Only 0x0A on screen ⇒ wrong COM port or terminal UI.
      uart_stream_test #(
        .CLK_PER_BIT(16'd281),
        .PATTERN(8'h48)
      ) u_uart_stream (
        .clk(clk27),
        .rst_n(rst_n),
        .uart_tx(uart_tx)
      );
      assign soc_uart_tx           = 1'b1;
      assign sd_spi_sck            = 1'b1;
      assign sd_spi_mosi           = 1'b1;
      assign sd_spi_cs_n           = 1'b1;
      assign illegal_instr_obs     = 1'b0;
      assign gpio_out_obs          = 32'h0;
      assign core_pc_obs           = 32'h0;
      assign core_halted_obs       = 1'b0;
    end
  endgenerate

  assign in_handler =
    (core_pc_obs >= 32'h200) & (core_pc_obs < 32'h280) & ~core_halted_obs;

  // Handler runs only ~µs per IRQ; holding PC in 0x100.. is invisible. Toggle on each entry (~0.5 Hz).
  always_ff @(posedge clk27) begin
    in_handler_d <= in_handler;
    if (!rst_n_por)
      led4_tgl <= 1'b1;
    else if (in_handler && !in_handler_d)
      led4_tgl <= ~led4_tgl;
  end

  always_ff @(posedge clk27) begin
    hb <= hb + 24'd1;
    // Active-low LEDs: 0 = on.
    if (!rst_n_por) begin
      user_led <= 6'b111111;
    end else if (USE_HW_UART_STREAM) begin
      // Bring-up: LED0 slow blink, LED1 fast blink (distinct from SoC bitstream).
      user_led[0] <= ~hb[23];
      user_led[1] <= ~hb[20];
      user_led[5:2] <= 4'b1111;
    end else begin
      user_led[0] <= ~hb[23];
      user_led[1] <= ~gpio_out_obs[0];
      user_led[2] <= ~core_halted_obs;
      user_led[3] <= ~illegal_instr_obs;
      user_led[4] <= led4_tgl;
      user_led[5] <= 1'b1;
    end
  end
endmodule
