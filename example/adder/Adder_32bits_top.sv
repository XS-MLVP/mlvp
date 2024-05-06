module Adder_32bits_top;

  logic [31:0] a;
  logic [31:0] b;
  logic  cin;
  logic [31:0] sum;


  Adder_32bits Adder_32bits (
    .a(a),
    .b(b),
    .cin(cin),
    .sum(sum)
  );

  export "DPI-C" function get_a;
  export "DPI-C" function set_a;
  export "DPI-C" function get_b;
  export "DPI-C" function set_b;
  export "DPI-C" function get_cin;
  export "DPI-C" function set_cin;
  export "DPI-C" function get_sum;
  export "DPI-C" function set_sum;


  function void get_a;
    output logic [31:0] value;
    value=a;
  endfunction

  function void set_a;
    input logic [31:0] value;
    a=value;
  endfunction

  function void get_b;
    output logic [31:0] value;
    value=b;
  endfunction

  function void set_b;
    input logic [31:0] value;
    b=value;
  endfunction

  function void get_cin;
    output logic  value;
    value=cin;
  endfunction

  function void set_cin;
    input logic  value;
    cin=value;
  endfunction

  function void get_sum;
    output logic [31:0] value;
    value=sum;
  endfunction

  function void set_sum;
    input logic [31:0] value;
    sum=value;
  endfunction



initial begin
    $dumpfile("Adder_32bits.vcd");
    $dumpvars(0, Adder_32bits_top);
 end 

endmodule
