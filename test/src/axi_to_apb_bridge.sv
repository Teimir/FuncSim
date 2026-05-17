module axi_to_apb_bridge (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        s_awvalid,
  output logic        s_awready,
  input  logic [31:0] s_awaddr,
  input  logic        s_wvalid,
  output logic        s_wready,
  input  logic [31:0] s_wdata,
  input  logic [3:0]  s_wstrb,
  output logic        s_bvalid,
  input  logic        s_bready,
  output logic [1:0]  s_bresp,
  input  logic        s_arvalid,
  output logic        s_arready,
  input  logic [31:0] s_araddr,
  output logic        s_rvalid,
  input  logic        s_rready,
  output logic [31:0] s_rdata,
  output logic [1:0]  s_rresp,
  output logic        psel,
  output logic        penable,
  output logic        pwrite,
  output logic [31:0] paddr,
  output logic [31:0] pwdata,
  input  logic [31:0] prdata,
  input  logic        pready,
  input  logic        pslverr
);
  localparam logic [1:0] AXI_OKAY   = 2'b00;
  localparam logic [1:0] AXI_SLVERR = 2'b10;

  typedef enum logic [1:0] {
    ST_IDLE   = 2'd0,
    ST_SETUP  = 2'd1,
    ST_ACCESS = 2'd2
  } apb_st_e;

  apb_st_e     st;
  logic        is_write;
  logic        aw_latched;
  logic        w_latched;
  logic [31:0] lat_awaddr;
  logic [31:0] lat_wdata;

  logic write_collecting;
  assign write_collecting = aw_latched | w_latched;

  assign s_awready = (st == ST_IDLE) && !aw_latched;
  assign s_wready  = (st == ST_IDLE) && !w_latched;
  assign s_arready = (st == ST_IDLE) && !write_collecting && s_arvalid;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      st         <= ST_IDLE;
      is_write   <= 1'b0;
      aw_latched <= 1'b0;
      w_latched  <= 1'b0;
      lat_awaddr <= 32'h0;
      lat_wdata  <= 32'h0;
      psel       <= 1'b0;
      penable    <= 1'b0;
      pwrite     <= 1'b0;
      paddr      <= 32'h0;
      pwdata     <= 32'h0;
      s_bvalid   <= 1'b0;
      s_bresp    <= AXI_OKAY;
      s_rvalid   <= 1'b0;
      s_rresp    <= AXI_OKAY;
      s_rdata    <= 32'h0;
    end else begin
      if (s_bvalid && s_bready)
        s_bvalid <= 1'b0;
      if (s_rvalid && s_rready)
        s_rvalid <= 1'b0;

      unique case (st)
        ST_IDLE: begin
          psel    <= 1'b0;
          penable <= 1'b0;
          pwrite  <= 1'b0;

          // Core may assert AW+W in the same cycle for STR.
          if (s_awvalid && s_awready && s_wvalid && s_wready && !write_collecting) begin
            is_write <= 1'b1;
            pwrite   <= 1'b1;
            paddr    <= s_awaddr;
            pwdata   <= s_wdata;
            st       <= ST_SETUP;
          end else begin
            if (s_awvalid && s_awready) begin
              aw_latched <= 1'b1;
              lat_awaddr <= s_awaddr;
            end
            if (s_wvalid && s_wready) begin
              w_latched <= 1'b1;
              lat_wdata <= s_wdata;
            end
            if (aw_latched && w_latched) begin
              is_write   <= 1'b1;
              pwrite     <= 1'b1;
              paddr      <= lat_awaddr;
              pwdata     <= lat_wdata;
              aw_latched <= 1'b0;
              w_latched  <= 1'b0;
              st         <= ST_SETUP;
            end else if (s_arvalid && s_arready) begin
              is_write <= 1'b0;
              pwrite   <= 1'b0;
              paddr    <= s_araddr;
              st       <= ST_SETUP;
            end
          end
        end

        ST_SETUP: begin
          psel    <= 1'b1;
          penable <= 1'b0;
          st      <= ST_ACCESS;
        end

        ST_ACCESS: begin
          psel    <= 1'b1;
          penable <= 1'b1;
          // First ACCESS cycle still sees penable==0 at the slave; complete when it was already 1.
          if (pready && penable) begin
            psel    <= 1'b0;
            penable <= 1'b0;
            pwrite  <= 1'b0;
            if (is_write) begin
              s_bvalid <= 1'b1;
              s_bresp  <= pslverr ? AXI_SLVERR : AXI_OKAY;
            end else begin
              s_rvalid <= 1'b1;
              s_rresp  <= pslverr ? AXI_SLVERR : AXI_OKAY;
              s_rdata  <= prdata;
            end
            st <= ST_IDLE;
          end
        end

        default: st <= ST_IDLE;
      endcase
    end
  end

  // s_wstrb unused: all MMIO peripherals accept full 32-bit writes today.
endmodule
