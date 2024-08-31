module Adder_top;

  wire [63:0] io_a;
  wire [63:0] io_b;
  wire  io_cin;
  wire [63:0] io_sum;
  wire  io_cout;


Adder Adder (
    .io_a(io_a),
    .io_b(io_b),
    .io_cin(io_cin),
    .io_sum(io_sum),
    .io_cout(io_cout)
  );
endmodule
