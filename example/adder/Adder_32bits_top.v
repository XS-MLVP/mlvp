module Adder_32bits_top;

  wire [31:0] a;
  wire [31:0] b;
  wire  cin;
  wire [31:0] sum;


Adder_32bits Adder_32bits (
    .a(a),
    .b(b),
    .cin(cin),
    .sum(sum)
  );
endmodule
