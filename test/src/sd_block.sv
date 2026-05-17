// Functional SD block MMIO (matches src/core/peripherals/sd_card.py).
module apb_sd_block (
  input logic        pclk,
  input logic        presetn,
  input logic        psel,
  input logic        penable,
  input logic        pwrite,
  input logic [31:0] paddr,
  input logic [31:0] pwdata,
  output logic [31:0] prdata,
  output logic        pready,
  output logic        pslverr,
  output logic        irq
);
`include "mmio_sd_regs.svh"

  logic [31:0] lba;
  logic [31:0] status;
  logic [7:0]  err_code;
  logic        mounted;
  logic [31:0] buf_mem [0:127];

  assign pready = 1'b1;
  assign pslverr = 1'b0;
  assign irq = 1'b0;

  always_ff @(posedge pclk) begin
    if (!presetn) begin
      lba <= 32'h0;
      status <= 32'h8;
      err_code <= 8'h0;
      mounted <= 1'b1;
    end else if (psel && penable && pwrite) begin
      case (paddr[6:2])
        `E32C_SD_BLOCK_REG_CTRL: begin
          case (pwdata[7:0])
            8'd1, 8'd2, 8'd3: status <= mounted ? 32'h1 : 32'hC;
            default: ;
          endcase
        end
        `E32C_SD_BLOCK_REG_LBA: lba <= pwdata;
        default: begin
          if (paddr[6:2] >= `E32C_SD_BLOCK_REG_DATA &&
              paddr[6:2] < `E32C_SD_BLOCK_REG_DATA + 128) begin
            buf_mem[paddr[6:2] - `E32C_SD_BLOCK_REG_DATA] <= pwdata;
          end
        end
      endcase
    end
  end

  always_comb begin
    prdata = 32'h0;
    case (paddr[6:2])
      `E32C_SD_BLOCK_REG_CTRL: prdata = 32'h0;
      `E32C_SD_BLOCK_REG_STATUS: prdata = status | (err_code << 16);
      `E32C_SD_BLOCK_REG_LBA: prdata = lba;
      default: begin
        if (paddr[6:2] >= `E32C_SD_BLOCK_REG_DATA &&
            paddr[6:2] < `E32C_SD_BLOCK_REG_DATA + 128) begin
          prdata = buf_mem[paddr[6:2] - `E32C_SD_BLOCK_REG_DATA];
        end
      end
    endcase
  end
endmodule
