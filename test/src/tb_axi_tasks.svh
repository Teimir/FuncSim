// Shared AXI4-Lite master tasks for external port on soc_top.
// Requires: reg clk; and m_awvalid/m_awready/... signals named as below.

task axi_write;
  input [31:0] addr;
  input [31:0] data;
  integer tmo;
  begin
    @(posedge clk);
    m_awaddr <= addr;
    m_wdata <= data;
    m_wstrb <= 4'hF;
    m_awvalid <= 1'b1;
    m_wvalid <= 1'b1;
    m_bready <= 1'b1;
    tmo = 0;
    while (!(m_awready && m_wready) && tmo < 200) begin
      @(posedge clk);
      tmo = tmo + 1;
    end
    if (tmo >= 200) begin
      $display("AXI write handshake timeout at %h", addr);
      $finish(1);
    end
    @(posedge clk);
    m_awvalid <= 1'b0;
    m_wvalid <= 1'b0;
    tmo = 0;
    while (!m_bvalid && tmo < 200) begin
      @(posedge clk);
      tmo = tmo + 1;
    end
    if (tmo >= 200) begin
      $display("AXI write response timeout at %h", addr);
      $finish(1);
    end
    if (m_bresp !== 2'b00) begin
      $display("AXI write error at %h bresp=%b", addr, m_bresp);
      $finish(1);
    end
    @(posedge clk);
    m_bready <= 1'b0;
  end
endtask

task axi_read;
  input  [31:0] addr;
  output [31:0] data;
  integer tmo;
  begin
    @(posedge clk);
    m_araddr <= addr;
    m_arvalid <= 1'b1;
    m_rready <= 1'b1;
    tmo = 0;
    while (!m_arready && tmo < 200) begin
      @(posedge clk);
      tmo = tmo + 1;
    end
    if (tmo >= 200) begin
      $display("AXI read addr timeout at %h", addr);
      $finish(1);
    end
    @(posedge clk);
    m_arvalid <= 1'b0;
    tmo = 0;
    while (!m_rvalid && tmo < 400) begin
      @(posedge clk);
      tmo = tmo + 1;
    end
    if (tmo >= 400) begin
      $display("AXI read data timeout at %h", addr);
      $finish(1);
    end
    if (m_rresp !== 2'b00) begin
      $display("AXI read error at %h rresp=%b", addr, m_rresp);
      $finish(1);
    end
    data = m_rdata;
    @(posedge clk);
    m_rready <= 1'b0;
  end
endtask
