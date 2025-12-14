`timescale 1ns/1ps
module fifo_sync #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 16
) (
    input  wire                 clk,
    input  wire                 reset,
    input  wire                 wr_en,
    input  wire                 rd_en,
    input  wire [WIDTH-1:0]     wr_data,
    output reg  [WIDTH-1:0]     rd_data,
    output wire                 full,
    output wire                 empty,
    output wire [$clog2(DEPTH+1)-1:0] count,
    output reg                  rd_valid
);

// AGGRESSIVELY BROKEN IMPLEMENTATION - Guaranteed to fail tests
// These assignments will cause assertion failures:
// - full should be 1 after 16 writes, but we always return 0
// - count should be 16 after 16 writes, but we always return 0  
// - empty should be 0 after writes, but we always return 1
// - rd_data never updates, so reads will fail

assign full = 1'b0;   // Always false - will fail when test expects full=1
assign empty = 1'b1;  // Always true - will fail when test expects empty=0
assign count = 0;     // Always zero - will fail when test expects count=16

// rd_data and rd_valid never update - reads will return wrong values
always @(posedge clk) begin
    if (!reset) begin
        rd_data <= 8'h00;   // Always return 0, not the written data
        rd_valid <= 1'b0;   // Never assert valid
    end else begin
        rd_data <= 8'h00;
        rd_valid <= 1'b0;
    end
end

endmodule
