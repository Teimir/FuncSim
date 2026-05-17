// Functional SD SPI MMIO shim (Python-aligned). CARD_MEM optional (off on TN9K + Gowin IP).
module apb_sd_spi #(
  parameter bit USE_CARD_MEM = 1'b1,
  parameter int CARD_MEM_WORDS = 512,
  parameter int MAX_BLK = 4
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
  output logic        irq,
  output logic         spi_sck,
  output logic        spi_mosi,
  input logic        spi_miso,
  output logic         spi_cs_n
);
`include "mmio_sd_regs.svh"

  localparam [2:0] ST_IDLE = 3'd0;
  localparam [2:0] ST_CMD  = 3'd1;

  logic        en;
  logic        irq_en;
  logic        irq_pending;
  logic        busy;
  logic        ready;
  logic        rx_valid;
  logic        error;
  logic [15:0] clk_div;
  logic [15:0] clk_cnt;
  logic [5:0]  cmd_idx;
  logic [31:0] cmd_arg;
  logic [31:0] resp0;
  logic [31:0] blkidx;
  logic [6:0]  dataix;
  logic [2:0]  st;
  logic        app_cmd_seen;
  logic [31:0] word_tmp;
  logic [10:0] card_word_idx;
  logic [10:0] card_rd_addr;
  logic [31:0] card_rd_data;
  logic        card_wr_en;

  assign card_word_idx = {blkidx[3:0], dataix};
  assign card_rd_addr  = card_word_idx;
  assign pready  = 1'b1;
  assign pslverr = 1'b0;
  assign irq     = irq_en && irq_pending;
  assign spi_mosi = 1'b1;

  generate
    if (USE_CARD_MEM && CARD_MEM_WORDS > 0) begin : g_card_ram
      sd_spi_card_mem #(.WORDS(CARD_MEM_WORDS)) u_card_mem (
        .clk(pclk),
        .rst_n(presetn),
        .rd_addr(card_rd_addr),
        .rd_data(card_rd_data),
        .wr_addr(card_word_idx),
        .wr_data(pwdata),
        .wr_en(card_wr_en)
      );
    end else begin : g_no_card_ram
      assign card_rd_data = 32'h0;
    end
  endgenerate

  always_ff @(posedge pclk) begin
    if (!presetn) begin
      en <= 1'b0;
      spi_cs_n <= 1'b1;
      spi_sck <= 1'b0;
      irq_en <= 1'b0;
      irq_pending <= 1'b0;
      busy <= 1'b0;
      ready <= 1'b0;
      rx_valid <= 1'b0;
      error <= 1'b0;
      clk_div <= 16'd8;
      clk_cnt <= 16'd0;
      cmd_idx <= 6'd0;
      cmd_arg <= 32'h0;
      resp0 <= 32'hFFFF_FFFF;
      blkidx <= 32'h0;
      dataix <= 7'd0;
      st <= ST_IDLE;
      app_cmd_seen <= 1'b0;
      card_wr_en <= 1'b0;
    end else begin
      card_wr_en <= 1'b0;

      if (busy) begin
        if (clk_cnt == 16'd0) begin
          clk_cnt <= clk_div;
          spi_sck <= ~spi_sck;
          if (st == ST_CMD) begin
            busy <= 1'b0;
            st <= ST_IDLE;
            rx_valid <= 1'b1;
            irq_pending <= 1'b1;
            spi_sck <= 1'b0;
            case (cmd_idx)
              6'd0: begin
                resp0 <= 32'h0000_0001;
                ready <= 1'b0;
                app_cmd_seen <= 1'b0;
                error <= 1'b0;
              end
              6'd8: begin
                resp0 <= 32'h0000_01AA;
                error <= 1'b0;
              end
              6'd55: begin
                resp0 <= 32'h0000_0001;
                app_cmd_seen <= 1'b1;
                error <= 1'b0;
              end
              6'd41: begin
                if (app_cmd_seen) begin
                  ready <= 1'b1;
                  resp0 <= 32'h0000_0000;
                  app_cmd_seen <= 1'b0;
                  error <= 1'b0;
                end else begin
                  resp0 <= 32'h0000_0005;
                  error <= 1'b1;
                end
              end
              6'd17: begin
                if (ready && (blkidx < MAX_BLK)) begin
                  resp0 <= 32'h0000_0000;
                  error <= 1'b0;
                end else begin
                  resp0 <= 32'h0000_0004;
                  error <= 1'b1;
                end
              end
              6'd24: begin
                if (ready && (blkidx < MAX_BLK)) begin
                  resp0 <= 32'h0000_0000;
                  error <= 1'b0;
                end else begin
                  resp0 <= 32'h0000_0004;
                  error <= 1'b1;
                end
              end
              default: begin
                resp0 <= 32'h0000_0004;
                error <= 1'b1;
              end
            endcase
          end
        end else begin
          clk_cnt <= clk_cnt - 1'b1;
        end
      end

      if (psel && penable && pwrite) begin
        case (paddr[6:2])
          `E32C_SD_SPI_REG_CTRL: begin
            en <= pwdata[0];
            spi_cs_n <= pwdata[1];
            irq_en <= pwdata[2];
            if (pwdata[3]) irq_pending <= 1'b0;
          end
          `E32C_SD_SPI_REG_DIV: clk_div <= pwdata[15:0];
          `E32C_SD_SPI_REG_CMD: begin
            cmd_idx <= pwdata[5:0];
            if (pwdata[8] && en && !busy) begin
              busy <= 1'b1;
              rx_valid <= 1'b0;
              st <= ST_CMD;
              clk_cnt <= clk_div;
              spi_sck <= 1'b0;
            end
          end
          `E32C_SD_SPI_REG_ARG: cmd_arg <= pwdata;
          `E32C_SD_SPI_REG_BLKIDX: blkidx <= pwdata;
          `E32C_SD_SPI_REG_DATAIX: dataix <= pwdata[6:0];
          `E32C_SD_SPI_REG_DATAWR: card_wr_en <= USE_CARD_MEM;
          default: ;
        endcase
      end

      if (psel && penable && !pwrite && paddr[6:2] == `E32C_SD_SPI_REG_RESP0)
        rx_valid <= 1'b0;
      if (cmd_idx == 6'd17 || cmd_idx == 6'd24)
        blkidx <= cmd_arg;
    end
  end

  always_comb begin
    word_tmp = card_rd_data;
    case (paddr[6:2])
      `E32C_SD_SPI_REG_CTRL: prdata = {28'h0, 1'b0, irq_en, spi_cs_n, en};
      `E32C_SD_SPI_REG_DIV: prdata = {16'h0, clk_div};
      `E32C_SD_SPI_REG_CMD: prdata = {23'h0, 1'b0, 2'b0, cmd_idx};
      `E32C_SD_SPI_REG_ARG: prdata = cmd_arg;
      `E32C_SD_SPI_REG_RESP0: prdata = resp0;
      `E32C_SD_SPI_REG_STATUS: prdata = {27'h0, error, irq_pending, rx_valid, ready, busy};
      `E32C_SD_SPI_REG_BLKIDX: prdata = blkidx;
      `E32C_SD_SPI_REG_DATAIX: prdata = {25'h0, dataix};
      `E32C_SD_SPI_REG_DATARD: prdata = word_tmp;
      `E32C_SD_SPI_REG_DATAWR: prdata = word_tmp;
      default: prdata = 32'h0;
    endcase
  end
endmodule
