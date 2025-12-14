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

    // FIFO memory
    reg [WIDTH-1:0] fifo_mem [DEPTH-1:0];

    // Pointers
    reg [$clog2(DEPTH)-1:0] wr_ptr;
    reg [$clog2(DEPTH)-1:0] rd_ptr;
    reg [$clog2(DEPTH+1)-1:0] fifo_count;

    // Status flags
    assign full = (fifo_count == DEPTH);
    assign empty = (fifo_count == 0);
    assign count = fifo_count;

    // Reset logic
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            fifo_count <= 0;
            rd_data <= 0;
            rd_valid <= 0;
        end else begin
            // Write operation
            if (wr_en && !full) begin
                fifo_mem[wr_ptr] <= wr_data;
                wr_ptr <= (wr_ptr + 1) % DEPTH;
                fifo_count <= fifo_count + 1;
            end

            // Read operation
            if (rd_en && !empty) begin
                rd_data <= fifo_mem[rd_ptr];
                rd_ptr <= (rd_ptr + 1) % DEPTH;
                fifo_count <= fifo_count - 1;
                rd_valid <= 1;
            end else if (rd_en && empty) begin
                rd_valid <= 0;
            end else begin
                rd_valid <= 0;
            end
        end
    end

endmodule