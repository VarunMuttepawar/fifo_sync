# FIFO Sync - Specification

## Overview
A synchronous FIFO (first-in-first-out) buffering module with parameterizable data width and depth. The FIFO supports synchronous write and read operations on the same clock. Reset is asynchronous active-LOW.

## Interface

- `clk` (input): Rising-edge clock.
- `reset` (input): Asynchronous active-LOW reset. When `reset == 0`, FIFO clears and count -> 0.
- `wr_en` (input): Write enable. When high at rising edge and FIFO is not full, `wr_data` is written.
- `rd_en` (input): Read enable. When high at rising edge and FIFO is not empty, `rd_data` is presented on output and `rd_valid` asserted.
- `wr_data` (input WIDTH bits): Data to write on a write cycle.
- `rd_data` (output WIDTH bits): Data read out when `rd_valid` is asserted.
- `full` (output): High when FIFO cannot accept writes (count == DEPTH).
- `empty` (output): High when FIFO contains no data (count == 0).
- `count` (output integer bits): Number of words currently stored (0..DEPTH).
- `rd_valid` (output): Asserted for the cycle where `rd_data` is valid due to a read.

## Behavior

- Reset (active-LOW): On `reset == 0`, `wr_ptr`, `rd_ptr`, `fifo_count`, `rd_data`, `rd_valid` are cleared to zero (or '0).
- Writes:
  - If `wr_en` is high at a rising clock and `full` is low, write `wr_data` into FIFO at `wr_ptr` and increment `wr_ptr` (wrap-around modulo DEPTH).
  - If `wr_en` asserted while `full` is high, the write is ignored.
- Reads:
  - If `rd_en` is high at a rising clock and `empty` is low, read data from FIFO at `rd_ptr` and present it on `rd_data` and assert `rd_valid` during that cycle. Increment `rd_ptr` (wrap-around).
  - If `rd_en` asserted while `empty` is high, no read occurs and `rd_valid` stays low.
- Simultaneous read and write in same cycle:
  - Allowed. If FIFO is not empty and not full, reading returns the word at `rd_ptr` and writing places `wr_data` at `wr_ptr`. `fifo_count` remains unchanged. Pointers both advance.
  - If read and write are both asserted but one of them would be illegal (empty/full), the legal operation occurs and the illegal operation is ignored.

## Implementation constraints
- Synthesis-friendly SystemVerilog only (no SVA, no DPI).
- Use non-blocking (`<=`) sequential assignments inside the clocked process.
- Memory should be implemented as a reg array.
- Counters/pointers must wrap modulo DEPTH.

## Recommended parameters for tests
- Default `WIDTH = 8`, `DEPTH = 16` (used by tests).
