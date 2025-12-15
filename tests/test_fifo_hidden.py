import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
import os
from pathlib import Path

# Enable waveform dumping (do not override externally-set value)
os.environ.setdefault("WAVES", "1")

# -----------------------------------------------------------------------------
# Clock + Reset helpers
# -----------------------------------------------------------------------------

async def generate_clock(dut, period_ns=10):
    """Start the clock for this test."""
    clk = Clock(dut.clk, period_ns, unit="ns")
    cocotb.start_soon(clk.start())

async def reset_dut(dut):
    """Active-LOW asynchronous reset."""
    dut.reset.value = 0
    dut.wr_en.value = 0
    dut.rd_en.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    dut.reset.value = 1
    await RisingEdge(dut.clk)

# -----------------------------------------------------------------------------
# Cocotb tests
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_write_read_basic(dut):
    await generate_clock(dut)
    await reset_dut(dut)

    DEPTH = 16

    # Fill FIFO
    for i in range(DEPTH):
        dut.wr_data.value = i & 0xFF
        dut.wr_en.value = 1
        await RisingEdge(dut.clk)
        dut.wr_en.value = 0

    await Timer(1, unit="ps")
    assert int(dut.full.value) == 1
    assert int(dut.count.value) == DEPTH

    # Read FIFO
    collected = []
    for _ in range(DEPTH):
        dut.rd_en.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")

        if int(dut.rd_valid.value):
            collected.append(int(dut.rd_data.value))

        dut.rd_en.value = 0

    assert collected == list(range(DEPTH)), f"Got {collected}"

@cocotb.test()
async def test_full_and_overflow_behavior(dut):
    await generate_clock(dut)
    await reset_dut(dut)

    DEPTH = 16

    # Fill FIFO
    for i in range(DEPTH):
        dut.wr_data.value = i
        dut.wr_en.value = 1
        await RisingEdge(dut.clk)
        dut.wr_en.value = 0

    await Timer(1, unit="ps")
    dut._log.info(f"After fill: full={int(dut.full.value)} count={int(dut.count.value)}")
    assert int(dut.full.value) == 1
    assert int(dut.count.value) == DEPTH

    # Overflow write (should be ignored)
    dut.wr_data.value = 0xAB
    dut.wr_en.value = 1
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await Timer(1, unit="ps")

    dut._log.info(f"After overflow attempt: count={int(dut.count.value)} full={int(dut.full.value)}")
    assert int(dut.count.value) == DEPTH

    # One read
    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ps")
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    dut._log.info(f"After one read: full={int(dut.full.value)} count={int(dut.count.value)}")
    assert int(dut.full.value) == 0
    assert int(dut.count.value) == DEPTH - 1

    # Write again
    dut.wr_data.value = 0x7F
    dut.wr_en.value = 1
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    await Timer(1, unit="ps")
    await RisingEdge(dut.clk)
    dut._log.info(f"After refill: count={int(dut.count.value)} full={int(dut.full.value)}")
    assert int(dut.count.value) == DEPTH

@cocotb.test()
async def test_simultaneous_read_write(dut):
    await generate_clock(dut)
    await reset_dut(dut)

    # Preload FIFO
    for v in range(10, 14):
        dut.wr_data.value = v
        dut.wr_en.value = 1
        await RisingEdge(dut.clk)
        dut.wr_en.value = 0

    read_vals = []

    for v in range(20, 24):
        dut.wr_data.value = v
        dut.wr_en.value = 1
        dut.rd_en.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")

        if int(dut.rd_valid.value):
            read_vals.append(int(dut.rd_data.value))

        dut.wr_en.value = 0
        dut.rd_en.value = 0

    dut._log.info(f"Simultaneous read values: {read_vals}")
    assert read_vals == [10, 11, 12, 13], f"Got {read_vals}"

# -----------------------------------------------------------------------------
# Pytest wrapper (HUD REQUIRED - per CONTRACTOR_GUIDE lines 484-504)
# -----------------------------------------------------------------------------

def test_fifo_hidden_runner():
    from cocotb_tools.runner import get_runner
    
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "sources" / "fifo_sync.sv"]

    # Build and run tests using cocotb_tools.runner (per CONTRACTOR_GUIDE)
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="fifo_sync",
        always=True,
    )
    
    runner.test(
        hdl_toplevel="fifo_sync",
        test_module="test_fifo_hidden",
        waves=True,
    )
    
    # No need to check results.xml - runner.test() will raise SystemExit if tests fail

