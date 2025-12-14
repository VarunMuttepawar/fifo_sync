# FIFO Sync (HUD Format)

This repository packages a synchronous FIFO RTL problem in the HUD-required layout. The design under test is a parameterizable synchronous FIFO (`fifo_sync`) with active-low asynchronous reset. The hidden cocotb tests live in `tests/`, while the Verilog sources are in `sources/`.

## Files
- `sources/fifo_sync.sv`: Golden RTL implementation.
- `sources/fifo_sync_broken.sv`: Intentionally broken RTL for the baseline branch.
- `tests/test_fifo_hidden.py`: Cocotb hidden tests with the required pytest runner wrapper.
- `docs/Specification.md`: Functional specification for the FIFO.
- `pyproject.toml`: Python dependencies for running the testbench.

## Branch mapping (for HUD)
- `*_baseline`: Replace `sources/fifo_sync.sv` with the broken version and remove the `tests/` directory.
- `*_test`: Start from baseline, add `tests/` back.
- `*_golden`: Start from baseline, keep `tests/` removed, replace `sources/fifo_sync.sv` with the golden implementation.

## Running tests (complete or test branch)
```bash
uv sync                   # installs deps declared in pyproject.toml
uv run pytest tests -v    # runs cocotb tests via pytest wrapper
```

The cocotb runner defaults to Icarus (`SIM=icarus`). Set `SIM=verilator` or `SIM=modelsim` if desired.


