// Continuous 8N1 UART stream (bring-up helper): repeats PATTERN indefinitely.
module uart_stream_test #(
  parameter bit [15:0] CLK_PER_BIT = 16'd234,
  parameter bit [7:0]  PATTERN = 8'h55
) (
  input  logic clk,
  input  logic rst_n,
  output logic uart_tx
);

  typedef enum logic [1:0] {
    IDLE,
    ACTIVE,
    GAP
  } st_t;
  st_t st;

  logic [15:0] baud_ctr;
  logic [3:0]  idx;       // active bit phase: 0=start, 1..8=data, 9=stop

  localparam logic [15:0] GAP_CYCLES = 16'd27_000; // ~1 ms @27MHz between chars
  logic [15:0] gap_ctr;

  function automatic logic uart_tx_for_idx(logic [3:0] i);
    uart_tx_for_idx =
      i == 4'd9 ? 1'b1
      : i == 4'd0 ? 1'b0
      : PATTERN[i - 4'd1];
  endfunction

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      uart_tx <= 1'b1;
      baud_ctr <= '0;
      idx <= '0;
      gap_ctr <= '0;
      st <= IDLE;
    end else begin
      unique case (st)
        IDLE: begin
          uart_tx <= 1'b1;
          idx <= '0;
          baud_ctr <= CLK_PER_BIT - 16'd1;
          st <= ACTIVE;
        end
        ACTIVE: begin
          if (baud_ctr != 16'd0) begin
            baud_ctr <= baud_ctr - 16'd1;
          end else begin
            uart_tx <= uart_tx_for_idx(idx);
            baud_ctr <= CLK_PER_BIT - 16'd1;
            if (idx == 4'd9) begin
              gap_ctr <= GAP_CYCLES - 16'd1;
              st <= GAP;
            end else begin
              idx <= idx + 4'd1;
            end
          end
        end
        GAP: begin
          uart_tx <= 1'b1;
          if (gap_ctr != 16'd0) begin
            gap_ctr <= gap_ctr - 16'd1;
          end else begin
            st <= IDLE;
          end
        end
        default: st <= IDLE;
      endcase
    end
  end
endmodule
