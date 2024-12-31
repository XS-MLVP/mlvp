
module mem (
    input logic clk,
    input logic rst_n,
    input logic [1:0] bank,
    input logic [3:0] addr,
    input logic [7:0] data_in,
    input logic write_enable,
    output logic [7:0] data_out
);
    reg [7:0] memory [3:0][15:0];
    reg [7:0] data_buffer;
    reg [31:0] wcounter;
    reg [31:0] rcounter;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_buffer <= 8'b0;
            wcounter <= 32'b0;
            rcounter <= 32'b0;
        end else if (write_enable) begin
            memory[bank][addr] <= data_in;
            wcounter <= wcounter + 1;
        end else begin
            data_buffer <= memory[bank][addr];
            rcounter <= rcounter + 1;
        end
    end
    assign data_out = data_buffer;
endmodule
