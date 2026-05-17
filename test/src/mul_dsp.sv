module e32c_mul_u_dsp (
  input logic [31:0] a,
  input logic [31:0] b,
  output logic [63:0] p
);
  (* use_dsp = "yes" *) logic [63:0] p_int;
  assign p_int = a * b;
  assign p = p_int;
endmodule

module e32c_mul_s_dsp (
  input logic [31:0] a,
  input logic [31:0] b,
  output logic [63:0] p
);
  (* use_dsp = "yes" *) logic signed [63:0] p_int;
  assign p_int = $signed(a) * $signed(b);
  assign p = p_int;
endmodule
