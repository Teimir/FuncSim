// PSRAM byte-bank helpers for soc_top testbenches.
// Optional override: `define TB_PSRAM_PREFIX my_dut.u_psram before include.
`ifndef TB_PSRAM_PREFIX
`define TB_PSRAM_PREFIX dut.g_mem_psram.u_psram
`endif

task psram_write_word;
  input integer idx;
  input [31:0] word;
  begin
    `TB_PSRAM_PREFIX.mem_b0[idx] = word[7:0];
    `TB_PSRAM_PREFIX.mem_b1[idx] = word[15:8];
    `TB_PSRAM_PREFIX.mem_b2[idx] = word[23:16];
    `TB_PSRAM_PREFIX.mem_b3[idx] = word[31:24];
  end
endtask

task psram_read_word;
  input  integer idx;
  output [31:0] word;
  begin
    word = {
      `TB_PSRAM_PREFIX.mem_b3[idx],
      `TB_PSRAM_PREFIX.mem_b2[idx],
      `TB_PSRAM_PREFIX.mem_b1[idx],
      `TB_PSRAM_PREFIX.mem_b0[idx]
    };
  end
endtask
