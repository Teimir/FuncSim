module apb_timer #(
  localparam [31:0] PERIOD_CYCLES = 32'd27_000_000
) (
  input logic        pclk,
  input logic        presetn,
  input logic        psel,
  input logic        penable,
  input logic        pwrite,
  input logic [31:0] paddr,
  input logic [31:0] pwdata,
  output logic  [31:0] prdata,
  output logic        pready,
  output logic        pslverr,
  output logic        irq
);
  logic [31:0] counter;
  logic [31:0] period;
  logic irq_enable;
  logic irq_pending;

  assign pready = 1'b1;
  assign pslverr = 1'b0;
  assign irq = irq_enable && irq_pending;

  always_ff @(posedge pclk) begin
    if (!presetn) begin
      counter <= 32'h0;
      period <= PERIOD_CYCLES;
      irq_enable <= 1'b0;
      irq_pending <= 1'b0;
    end else begin
      counter <= counter + 32'd1;
      if (period != 32'h0) begin
        if (!irq_pending && (counter >= period)) irq_pending <= 1'b1;
      end
      if (psel && penable && pwrite) begin
        case (paddr[5:2])
          4'h2: period[31:0] <= pwdata;
          4'h3: period[31:16] <= pwdata[15:0];
          4'h6: period[31:0] <= pwdata;
          4'h7: period[31:16] <= pwdata[15:0];
          4'h4: begin
            irq_enable <= pwdata[0];
            if (pwdata[2]) begin
              irq_pending <= 1'b0;
              counter <= 32'h0;
            end
          end
          default: ;
        endcase
      end
    end
  end

  always_comb begin
    case (paddr[5:2])
      4'h0: prdata = counter;
      4'h1: prdata = 32'h0;
      4'h2: prdata = period;
      4'h3: prdata = period[31:16];
      4'h6: prdata = period;
      4'h7: prdata = period[31:16];
      4'h4: prdata = {29'h0, 1'b0, irq_pending, irq_enable};
      default: prdata = 32'h0;
    endcase
  end
endmodule
