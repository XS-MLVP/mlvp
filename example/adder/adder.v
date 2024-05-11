module Adder_32bits(
    input [31:0]   a,
    input [31:0]   b,
    input          cin,
    output [31:0]  sum,
);
    assign sum = a + b + cin;

endmodule