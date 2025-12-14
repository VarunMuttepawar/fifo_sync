`timescale 1ns/1ps
module fifo_sync #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 16
) (
    input  wire                 clk,
    input  wire                 reset,     // active-LOW async reset
    input  wire                 wr_en,
    input  wire                 rd_en,
    input  wire [WIDTH-1:0]     wr_data,
    output reg  [WIDTH-1:0]     rd_data,
    output wire                 full,
    output wire                 empty,
    output wire [$clog2(DEPTH+1)-1:0] count,
    output reg                  rd_valid
);

    // ------------------------------------------------------------------
    // Internal storage
    // ------------------------------------------------------------------
    reg [WIDTH-1:0] mem [0:DEPTH-1];

    localparam int PTR_W = $clog2(DEPTH);

    reg [PTR_W-1:0] wr_ptr;
    reg [PTR_W-1:0] rd_ptr;
    reg [$clog2(DEPTH+1)-1:0] fifo_count;

    // ------------------------------------------------------------------
    // Status outputs
    // ------------------------------------------------------------------
    assign full  = (fifo_count == DEPTH);
    assign empty = (fifo_count == 0);
    assign count = fifo_count;

    // ------------------------------------------------------------------
    // Sequential logic
    // ------------------------------------------------------------------
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            wr_ptr     <= '0;
            rd_ptr     <= '0;
            fifo_count <= '0;
            rd_data    <= '0;
            rd_valid   <= 1'b0;
        end else begin
            rd_valid <= 1'b0;

            // -------------------------------
            // Simultaneous read & write
            // -------------------------------
            if (wr_en && !full && rd_en && !empty) begin
                mem[wr_ptr] <= wr_data;
                rd_data     <= mem[rd_ptr];
                wr_ptr      <= wr_ptr + 1'b1;
                rd_ptr      <= rd_ptr + 1'b1;
                rd_valid    <= 1'b1;
                // fifo_count unchanged
            end

            // -------------------------------
            // Write only
            // -------------------------------
            else if (wr_en && !full) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr      <= wr_ptr + 1'b1;
                fifo_count  <= fifo_count + 1'b1;
            end

            // -------------------------------
            // Read only
            // -------------------------------
            else if (rd_en && !empty) begin
                rd_data     <= mem[rd_ptr];
                rd_ptr      <= rd_ptr + 1'b1;
                fifo_count  <= fifo_count - 1'b1;
                rd_valid    <= 1'b1;
            end
        end
    end

endmodule
