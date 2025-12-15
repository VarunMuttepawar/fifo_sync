import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Enable waveform dumping (do not override externally-set value)
os.environ.setdefault("WAVES", "1")

# -----------------------------------------------------------------------------
# Clock + Reset helpers
# -----------------------------------------------------------------------------

_clock_started = False

async def generate_clock(dut, period_ns=10):
    """Start the clock only once (important!)."""
    global _clock_started
    if _clock_started:
        return
    _clock_started = True
    clk = Clock(dut.clk, period_ns, units="ns")
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
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert int(dut.full.value) == 1
    assert int(dut.count.value) == DEPTH

    # Read FIFO
    collected = []
    for _ in range(DEPTH):
        dut.rd_en.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        
        if int(dut.rd_valid.value):
            collected.append(int(dut.rd_data.value))

        dut.rd_en.value = 0

    await Timer(1, "ns")
    assert collected == list(range(DEPTH)), f"Got {collected}"

@cocotb.test()
async def test_full_and_overflow_behavior(dut):
    await generate_clock(dut)
    await reset_dut(dut)

    DEPTH = 16

    # Fill FIFO
    for i in range(DEPTH):
        dut.wr_data.value = (i + 10) & 0xFF
        dut.wr_en.value = 1
        await RisingEdge(dut.clk)
        dut.wr_en.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert int(dut.full.value) == 1
    assert int(dut.count.value) == DEPTH

    # Overflow write (should be ignored)
    dut.wr_data.value = 0xAB
    dut.wr_en.value = 1
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert int(dut.count.value) == DEPTH

    # One read
    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    dut.rd_en.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert int(dut.full.value) == 0
    assert int(dut.count.value) == DEPTH - 1

    # Write again
    dut.wr_data.value = 0x7F
    dut.wr_en.value = 1
    await RisingEdge(dut.clk)
    dut.wr_en.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
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

        await Timer(1, "ns")
        if int(dut.rd_valid.value):
            read_vals.append(int(dut.rd_data.value))

        dut.wr_en.value = 0
        dut.rd_en.value = 0

    assert read_vals == [10, 11, 12, 13], f"Got {read_vals}"

# -----------------------------------------------------------------------------
# JUnit parsing helper
# -----------------------------------------------------------------------------

def _count_failures_errors(results_xml: Path) -> tuple[int, int]:
    tree = ET.parse(results_xml)
    root = tree.getroot()

    suites = []
    if root.tag == "testsuite":
        suites.append(root)
    suites.extend(root.findall(".//testsuite"))

    failures = 0
    errors = 0
    for ts in suites:
        failures += int(ts.get("failures", "0"))
        errors += int(ts.get("errors", "0"))

    return failures, errors

# -----------------------------------------------------------------------------
# Pytest wrapper (HUD REQUIRED)
# -----------------------------------------------------------------------------

def test_fifo_hidden_runner():
    from cocotb_tools.runner import get_runner

    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "sources" / "fifo_sync.sv"]

    results_xml = proj_path / "sim_build" / "results.xml"
    results_xml.parent.mkdir(parents=True, exist_ok=True)
    results_xml.unlink(missing_ok=True)

    os.environ["COCOTB_RESULTS_FILE"] = str(results_xml)

    runner = get_runner(sim)
    runner.build(sources=sources, hdl_toplevel="fifo_sync", always=True)
    runner.test(
        hdl_toplevel="fifo_sync",
        test_module="test_fifo_hidden",
        waves=True,
    )

    assert results_xml.exists(), "Missing cocotb results.xml"
    failures, errors = _count_failures_errors(results_xml)
    assert failures == 0 and errors == 0, (
        f"Cocotb failures: failures={failures}, errors={errors}"
    )
