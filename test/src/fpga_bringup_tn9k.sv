// Minimal Tang Nano 9K bring-up: clock heartbeat + UART 0x55 stream (no SoC).
// Use as Gowin top (fpga_bringup_tn9k) to verify pins, USB-UART, and programming.
module fpga_bringup_tn9k (
  input  logic       clk27,
  output logic [5:0] user_led,
  output logic       uart_tx
);
  logic [15:0] rst_cnt;
  logic        rst_n;

  always_ff @(posedge clk27) begin
    if (!rst_n)
      rst_cnt <= rst_cnt + 16'd1;
  end

  assign rst_n = &rst_cnt;

  logic [23:0] hb;
  always_ff @(posedge clk27) begin
    hb <= hb + 24'd1;
    // LEDs are active-low on TN9K: drive 0 to turn on.
    user_led[0] <= hb[23];
    user_led[5:1] <= 5'b11111;
  end

  uart_stream_test #(
    .CLK_PER_BIT(16'd234),
    .PATTERN(8'h55)
  ) u_uart (
    .clk(clk27),
    .rst_n(rst_n),
    .uart_tx(uart_tx)
  );
endmodule
