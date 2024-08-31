module Adder_top;

  logic [63:0] io_a;
  logic [63:0] io_b;
  logic  io_cin;
  logic [63:0] io_sum;
  logic  io_cout;


  Adder Adder (
    .io_a(io_a),
    .io_b(io_b),
    .io_cin(io_cin),
    .io_sum(io_sum),
    .io_cout(io_cout)
  );

  export "DPI-C" function get_io_axxPfBDHOpxzz9;
  export "DPI-C" function set_io_axxPfBDHOpxzz9;
  export "DPI-C" function get_io_bxxPfBDHOpxzz9;
  export "DPI-C" function set_io_bxxPfBDHOpxzz9;
  export "DPI-C" function get_io_cinxxPfBDHOpxzz9;
  export "DPI-C" function set_io_cinxxPfBDHOpxzz9;
  export "DPI-C" function get_io_sumxxPfBDHOpxzz9;
  export "DPI-C" function set_io_sumxxPfBDHOpxzz9;
  export "DPI-C" function get_io_coutxxPfBDHOpxzz9;
  export "DPI-C" function set_io_coutxxPfBDHOpxzz9;


  function void get_io_axxPfBDHOpxzz9;
    output logic [63:0] value;
    value=io_a;
  endfunction

  function void set_io_axxPfBDHOpxzz9;
    input logic [63:0] value;
    io_a=value;
  endfunction

  function void get_io_bxxPfBDHOpxzz9;
    output logic [63:0] value;
    value=io_b;
  endfunction

  function void set_io_bxxPfBDHOpxzz9;
    input logic [63:0] value;
    io_b=value;
  endfunction

  function void get_io_cinxxPfBDHOpxzz9;
    output logic  value;
    value=io_cin;
  endfunction

  function void set_io_cinxxPfBDHOpxzz9;
    input logic  value;
    io_cin=value;
  endfunction

  function void get_io_sumxxPfBDHOpxzz9;
    output logic [63:0] value;
    value=io_sum;
  endfunction

  function void set_io_sumxxPfBDHOpxzz9;
    input logic [63:0] value;
    io_sum=value;
  endfunction

  function void get_io_coutxxPfBDHOpxzz9;
    output logic  value;
    value=io_cout;
  endfunction

  function void set_io_coutxxPfBDHOpxzz9;
    input logic  value;
    io_cout=value;
  endfunction



initial begin
    $dumpfile("Adder.fst");
    $dumpvars(0, Adder_top);
 end 

endmodule
