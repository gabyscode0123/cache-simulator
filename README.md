# Virtual Memory and Cache Simulator

Python simulator for exploring basic computer architecture concepts: virtual memory page mapping, set-associative cache behavior, cache hit/miss rates, miss types, and CPI-style timing effects.

This project was originally built for a computer architecture course and has been cleaned up as a portfolio project. Course-provided trace files are not included, but a small synthetic trace is available in `examples/` so the project can run immediately.

## Highlights

- Command-line milestone scripts plus an optional Streamlit dashboard.
- Computes cache geometry: blocks, rows, tag/index/offset bits, overhead, implementation size, and cost.
- Models virtual memory with per-process page tables and 4 KB pages.
- Tracks page table hits, page faults, and pages allocated from free physical memory.
- Simulates set-associative cache behavior from trace memory addresses.
- Tracks accesses, hits, misses, compulsory misses, conflict misses, hit/miss rates, CPI, and unused cache space.
- Supports Round Robin (`RR`) and deterministic Random (`RND`) replacement policies.
- Includes regression tests with small synthetic traces.

## Project Layout

```text
.
├── app.py                 # Optional Streamlit interface
├── milestone1.py          # Cache and physical-memory calculations
├── milestone2.py          # Milestone 1 output plus virtual-memory simulation
├── milestone3.py          # Cache simulation output
├── simulator/             # Shared simulator package
├── tests/                 # Unit tests with synthetic traces
├── examples/              # Tiny runnable example trace
├── sample_outputs/        # Saved example outputs from prior runs
└── assets/                # Screenshots/GIFs for README demos
```

## Quick Start

Clone the repository and run the tests:

```bash
python3 -m unittest discover tests
```

Run the cache simulation with the sample trace:

```bash
python3 milestone3.py -s 64 -b 64 -a 2 -r RR -p 1024 -u 75 -n 10000 -f examples/sample_trace.trc
```

## Interactive Dashboard

The optional dashboard provides a friendlier way to experiment with simulator settings, paste trace input, upload trace files, and view charts.

Install the demo dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

The dashboard shows:

- Cache geometry and cost estimates
- Virtual memory page statistics
- Cache hit/miss totals
- Hit rate, miss rate, CPI, and miss breakdown charts

## Command-Line Usage

Run each milestone script from the project root.

```bash
python3 milestone1.py -s 64 -b 64 -a 2 -r RR -p 1024 -u 75 -n 10000 -f path/to/trace.trc
python3 milestone2.py -s 64 -b 64 -a 2 -r RR -p 1024 -u 75 -n 10000 -f path/to/trace.trc
python3 milestone3.py -s 64 -b 64 -a 2 -r RR -p 1024 -u 75 -n 10000 -f path/to/trace.trc
```

Use repeated `-f` arguments to simulate multiple trace files:

```bash
python3 milestone3.py -s 64 -b 64 -a 2 -r RND -p 1024 -u 75 -n 10000 \
  -f trace1.trc \
  -f trace2.trc
```

## Trace Format

The parser accepts lines whose final token is a decimal or hexadecimal address. It also recognizes instruction and data-access markers used by the course traces:

```text
EIP 0x00000000
srcM: 0x00001000
dstM: 0x00002000
```

Lines without parseable addresses are skipped.

## Example Output

Saved outputs from previous runs are included in `sample_outputs/`. The files show milestone-style text output with cache accesses, hit/miss totals, CPI, compulsory misses, conflict misses, and unused cache space.

## What I Learned

- How cache geometry values are derived from cache size, block size, associativity, and physical memory size.
- Why page faults, cache misses, and miss penalties can strongly affect CPI.
- How trace locality changes hit rate and memory behavior.
- How to separate reusable simulator logic from command-line entrypoints and tests.

## Future Improvements

- Add downloadable CSV output from the dashboard.
- Add side-by-side comparison mode for several cache configurations.
- Add more replacement policies such as LRU.
- Add more detailed charts for page table usage and cache utilization.

## Notes

- Virtual memory uses 4 KB pages.
- A page fault is counted when a virtual page is not already mapped, whether it is loaded from free memory or via replacement.
- Cache misses are categorized as compulsory when a block is first seen and conflict when a previously seen block is no longer present in the cache.
- `RND` replacement uses a fixed seed so runs are repeatable.
