module apb_sd_spi (
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
  // Register map (offset from base 0xFFFF_3000):
  // +0x00 CTRL   [0]=EN [1]=CS_N [2]=IRQ_EN [3]=IRQ_CLR(W1C)
  // +0x04 DIV    SCK divider
  // +0x08 CMD    write: [5:0]=cmd index, bit8=start
  // +0x0C ARG    command argument
  // +0x10 RESP0  command response
  // +0x14 STATUS [0]=BUSY [1]=READY [2]=RX_VALID [3]=IRQ_PENDING [4]=ERROR
  // +0x18 BLKIDX block index for CMD17/CMD24
  // +0x1C DATAIX data index [0..127 words]
  // +0x20 DATARD read data word at DATAIX
  // +0x24 DATAWR write data word at DATAIX
  localparam [4:0] REG_CTRL   = 5'h00;
  localparam [4:0] REG_DIV    = 5'h01;
  localparam [4:0] REG_CMD    = 5'h02;
  localparam [4:0] REG_ARG    = 5'h03;
  localparam [4:0] REG_RESP0  = 5'h04;
  localparam [4:0] REG_STATUS = 5'h05;
  localparam [4:0] REG_BLKIDX = 5'h06;
  localparam [4:0] REG_DATAIX = 5'h07;
  localparam [4:0] REG_DATARD = 5'h08;
  localparam [4:0] REG_DATAWR = 5'h09;

  localparam [2:0] ST_IDLE = 3'd0;
  localparam [2:0] ST_CMD  = 3'd1;
  localparam [2:0] ST_DATA = 3'd2;

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
  (* ram_style = "block" *) (* syn_ramstyle = "block_ram" *) logic [31:0] card_mem [0:2047]; // 16 sectors * 128 words
  logic [31:0] word_tmp;
  logic [10:0] card_word_idx;
  logic [10:0] card_rd_addr_q;
  logic [31:0] card_rd_data_q;
  assign card_word_idx = {blkidx[3:0], dataix};

  assign pready = 1'b1;
  assign pslverr = 1'b0;
  assign irq = irq_en && irq_pending;
  assign spi_mosi = 1'b1;

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
      card_rd_addr_q <= 11'd0;
      card_rd_data_q <= 32'h0;
    end else begin
      // Synchronous BRAM-friendly read path.
      card_rd_addr_q <= card_word_idx;
      card_rd_data_q <= card_mem[card_rd_addr_q];

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
            // Protocol-meaningful command handling.
            case (cmd_idx)
              6'd0: begin
                resp0 <= 32'h0000_0001; // in-idle
                ready <= 1'b0;
                app_cmd_seen <= 1'b0;
                error <= 1'b0;
              end
              6'd8: begin
                resp0 <= 32'h0000_01AA; // VHS+check pattern
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
                if (ready && blkidx < 16) begin
                  resp0 <= 32'h0000_0000;
                  error <= 1'b0;
                end else begin
                  resp0 <= 32'h0000_0004;
                  error <= 1'b1;
                end
              end
              6'd24: begin
                if (ready && blkidx < 16) begin
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
          REG_CTRL: begin
            en <= pwdata[0];
            spi_cs_n <= pwdata[1];
            irq_en <= pwdata[2];
            if (pwdata[3]) irq_pending <= 1'b0;
          end
          REG_DIV: clk_div <= pwdata[15:0];
          REG_CMD: begin
            cmd_idx <= pwdata[5:0];
            if (pwdata[8] && en && !busy) begin
              busy <= 1'b1;
              rx_valid <= 1'b0;
              st <= ST_CMD;
              clk_cnt <= clk_div;
              spi_sck <= 1'b0;
            end
          end
          REG_ARG: cmd_arg <= pwdata;
          REG_BLKIDX: blkidx <= pwdata;
          REG_DATAIX: dataix <= pwdata[6:0];
          REG_DATAWR: begin
            card_mem[card_word_idx] <= pwdata;
          end
          default: ;
        endcase
      end

      if (psel && penable && !pwrite && paddr[6:2] == REG_RESP0) rx_valid <= 1'b0;
      // Keep ARG visible for debug/host software.
      if (cmd_idx == 6'd17 || cmd_idx == 6'd24) blkidx <= cmd_arg;
    end
  end

  always_comb begin
    word_tmp = card_rd_data_q;
    case (paddr[6:2])
      REG_CTRL: prdata = {28'h0, 1'b0, irq_en, spi_cs_n, en};
      REG_DIV: prdata = {16'h0, clk_div};
      REG_CMD: prdata = {23'h0, 1'b0, 2'b0, cmd_idx};
      REG_ARG: prdata = cmd_arg;
      REG_RESP0: prdata = resp0;
      REG_STATUS: prdata = {27'h0, error, irq_pending, rx_valid, ready, busy};
      REG_BLKIDX: prdata = blkidx;
      REG_DATAIX: prdata = {25'h0, dataix};
      REG_DATARD: prdata = word_tmp;
      REG_DATAWR: prdata = word_tmp;
      default: prdata = 32'h0;
    endcase
  end
endmodule
