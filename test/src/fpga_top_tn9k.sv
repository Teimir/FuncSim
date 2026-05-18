module fpga_top_tn9k #(
  // 0: поток UART без SoC (отладка). 1: SoC + прошивка.
  parameter USE_HW_UART_STREAM = 1'b0,
  // 0 = hello baseline (UART-only, ~6.8k LUT). 1 = demo (UART+Timer+SD shim, ~8.2k LUT).
  parameter bit TN9K_PROFILE_DEMO = 1'b0,
  // 0: MMIO shim на SPI-пинах (~8640 LUT). 1: Gowin SDIO_SPI_Top (не помещается на TN9K).
  parameter bit SD_BACKEND = 1'b0,
  // На TN9K обязательно 0 (буфер сектора ~3k LUT).
  parameter bit SD_USE_CARD_MEM = 1'b0
) (
  input  logic       clk27,
  // Пин в CST (IO 3); сброс только POR — кнопка не участвует (на части плат не подключена).
  (* syn_keep = 1 *) input logic user_btn_n,
  output logic       uart_tx,
  input  logic       uart_rx, // не используется в режиме UART bring-up
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
  logic        user_btn_sense;

  assign user_btn_sense = user_btn_n;

  always_ff @(posedge clk27) begin
    if (!rst_n_por)
      rst_cnt <= rst_cnt + 16'd1;
  end

  assign rst_n_por = &rst_cnt;
  assign rst_n     = rst_n_por;

  localparam bit ENABLE_SD_SPI = TN9K_PROFILE_DEMO;
  localparam bit ENABLE_TIMER  = TN9K_PROFILE_DEMO;
  localparam bit ENABLE_GPIO   = 1'b0;

  generate
    if (!USE_HW_UART_STREAM) begin : g_soc
      soc_top_tn9k #(
        .SD_MMIO_MODE(1'b1),
        .SD_BACKEND(SD_BACKEND),
        .SD_USE_CARD_MEM(SD_USE_CARD_MEM),
        .ENABLE_SD_SPI(ENABLE_SD_SPI),
        .ENABLE_TIMER(ENABLE_TIMER),
        .ENABLE_GPIO(ENABLE_GPIO)
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
        .uart_rx(uart_rx | 1'b1),
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
      // 27 МГц: CLK_PER_BIT 281 ≈ 9600, 234 ≈ 115200.
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

  always_ff @(posedge clk27) begin
    in_handler_d <= in_handler;
    if (!rst_n_por)
      led4_tgl <= 1'b1;
    else if (in_handler && !in_handler_d)
      led4_tgl <= ~led4_tgl;
  end

  always_ff @(posedge clk27) begin
    hb <= hb + 24'd1;
    // LED активны по нулю.
    if (!rst_n_por) begin
      user_led <= 6'b111111;
    end else if (USE_HW_UART_STREAM) begin
      user_led[0] <= ~hb[23];
      user_led[1] <= ~hb[20];
      user_led[5:2] <= 4'b1111;
    end else begin
      user_led[0] <= ~hb[23];
      user_led[1] <= ~gpio_out_obs[0];
      user_led[2] <= ~core_halted_obs;
      user_led[3] <= ~illegal_instr_obs;
      user_led[5:4] <= ~core_pc_obs[5:4];
    end
  end
endmodule
