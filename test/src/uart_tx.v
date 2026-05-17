// UART TX — from UARTexampleGOWIN (Gowin reference), 8N1.
module uart_tx #(
  parameter CLK_FRE = 27,
  parameter BAUD_RATE = 115200
) (
  input             clk,
  input             rst_n,
  input      [7:0]  tx_data,
  input             tx_data_valid,
  output reg        tx_data_ready,
  output            tx_pin
);
  localparam CYCLE = CLK_FRE * 1000000 / BAUD_RATE;

  localparam S_IDLE      = 3'd1;
  localparam S_START     = 3'd2;
  localparam S_SEND_BYTE = 3'd3;
  localparam S_STOP      = 3'd4;

  reg [2:0]  state;
  reg [2:0]  next_state;
  reg [15:0] cycle_cnt;
  reg [2:0]  bit_cnt;
  reg [7:0]  tx_data_latch;
  reg        tx_reg;

  assign tx_pin = tx_reg;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      state <= S_IDLE;
    else
      state <= next_state;
  end

  always @(*) begin
    case (state)
      S_IDLE:
        next_state = tx_data_valid ? S_START : S_IDLE;
      S_START:
        next_state = (cycle_cnt == CYCLE - 1) ? S_SEND_BYTE : S_START;
      S_SEND_BYTE:
        next_state = (cycle_cnt == CYCLE - 1 && bit_cnt == 3'd7) ? S_STOP : S_SEND_BYTE;
      S_STOP:
        next_state = (cycle_cnt == CYCLE - 1) ? S_IDLE : S_STOP;
      default:
        next_state = S_IDLE;
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_data_ready <= 1'b0;
    else if (state == S_IDLE)
      tx_data_ready <= tx_data_valid ? 1'b0 : 1'b1;
    else if (state == S_STOP && cycle_cnt == CYCLE - 1)
      tx_data_ready <= 1'b1;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_data_latch <= 8'd0;
    else if (state == S_IDLE && tx_data_valid)
      tx_data_latch <= tx_data;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      bit_cnt <= 3'd0;
    else if (state == S_SEND_BYTE)
      bit_cnt <= (cycle_cnt == CYCLE - 1) ? bit_cnt + 3'd1 : bit_cnt;
    else
      bit_cnt <= 3'd0;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      cycle_cnt <= 16'd0;
    else if ((state == S_SEND_BYTE && cycle_cnt == CYCLE - 1) || next_state != state)
      cycle_cnt <= 16'd0;
    else
      cycle_cnt <= cycle_cnt + 16'd1;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_reg <= 1'b1;
    else
      case (state)
        S_IDLE, S_STOP:
          tx_reg <= 1'b1;
        S_START:
          tx_reg <= 1'b0;
        S_SEND_BYTE:
          tx_reg <= tx_data_latch[bit_cnt];
        default:
          tx_reg <= 1'b1;
      endcase
  end
endmodule
