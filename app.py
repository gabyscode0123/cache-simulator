from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from simulator.cache import simulate_cache
from simulator.memory import calculate_cache, calculate_physical_memory, simulate_virtual_memory
from simulator.models import SimulationConfig


SAMPLE_TRACE = Path("examples/sample_trace.trc")


st.set_page_config(
    page_title="Cache Simulator",
    page_icon="🧠",
    layout="wide",
)


@st.cache_data
def load_sample_trace() -> str:
    if SAMPLE_TRACE.exists():
        return SAMPLE_TRACE.read_text(encoding="utf-8")
    return "EIP 0x0000\nEIP 0x0004\nsrcM: 0x0010\ndstM: 0x0020\n"


def write_trace_files(trace_text: str, uploaded_files) -> list[str]:
    paths: list[str] = []

    if trace_text.strip():
        handle = tempfile.NamedTemporaryFile("w", suffix=".trc", delete=False, encoding="utf-8")
        handle.write(trace_text)
        handle.close()
        paths.append(handle.name)

    for uploaded_file in uploaded_files or []:
        handle = tempfile.NamedTemporaryFile("wb", suffix=".trc", delete=False)
        handle.write(uploaded_file.getbuffer())
        handle.close()
        paths.append(handle.name)

    return paths


def build_config(trace_paths: list[str]) -> SimulationConfig:
    return SimulationConfig(
        cache_size_kb=st.session_state.cache_size_kb,
        block_size=st.session_state.block_size,
        associativity=st.session_state.associativity,
        replacement_policy=st.session_state.replacement_policy,
        physical_memory_mb=st.session_state.physical_memory_mb,
        system_memory_percent=st.session_state.system_memory_percent,
        instructions_per_time_slice=st.session_state.instructions_per_time_slice,
        trace_files=tuple(trace_paths),
    )


def metric_row(values: list[tuple[str, str, str | None]]) -> None:
    columns = st.columns(len(values))
    for column, (label, value, help_text) in zip(columns, values):
        column.metric(label, value, help=help_text)


st.title("Virtual Memory and Cache Simulator")
st.caption(
    "Explore page-table behavior, set-associative cache misses, hit rate, and CPI from memory trace input."
)

with st.sidebar:
    st.header("Configuration")
    st.number_input("Cache size (KB)", min_value=1, value=64, step=1, key="cache_size_kb")
    st.selectbox("Block size (bytes)", [16, 32, 64, 128], index=2, key="block_size")
    st.selectbox("Associativity", [1, 2, 4, 8], index=1, key="associativity")
    st.radio("Replacement policy", ["RR", "RND"], horizontal=True, key="replacement_policy")
    st.number_input("Physical memory (MB)", min_value=1, value=1024, step=128, key="physical_memory_mb")
    st.slider("System memory usage (%)", min_value=0.0, max_value=100.0, value=75.0, step=1.0, key="system_memory_percent")
    st.number_input("Instructions per time slice", min_value=1, value=10000, step=100, key="instructions_per_time_slice")

st.subheader("Trace Input")
trace_text = st.text_area(
    "Paste trace lines",
    value=load_sample_trace(),
    height=180,
    help="Each line should end with a decimal or hex address. EIP/srcM/dstM markers are recognized when present.",
)
uploaded_files = st.file_uploader("Or upload one or more trace files", type=["trc", "txt"], accept_multiple_files=True)

if st.button("Run Simulation", type="primary"):
    trace_paths = write_trace_files(trace_text, uploaded_files)
    if not trace_paths:
        st.error("Add pasted trace text or upload at least one trace file.")
        st.stop()

    try:
        config = build_config(trace_paths)
        cache_geometry = calculate_cache(config)
        physical_memory = calculate_physical_memory(config)
        vm_stats, page_tables = simulate_virtual_memory(config, physical_memory)
        cache_stats = simulate_cache(config, vm_stats)
    except Exception as exc:  # UI boundary: show readable validation/runtime failure.
        st.error(f"Simulation failed: {exc}")
        st.stop()

    st.success("Simulation complete")

    st.subheader("Cache Geometry")
    metric_row(
        [
            ("Total blocks", f"{cache_geometry.total_blocks:,}", None),
            ("Rows", f"{cache_geometry.rows:,}", None),
            ("Tag bits", str(cache_geometry.tag_bits), None),
            ("Index bits", str(cache_geometry.index_bits), None),
            ("Offset bits", str(cache_geometry.offset_bits), None),
        ]
    )
    metric_row(
        [
            ("Overhead", f"{cache_geometry.overhead_bytes:,} bytes", None),
            ("Implementation size", f"{cache_geometry.implementation_kb:.2f} KB", None),
            ("Estimated cost", f"${cache_geometry.cost:.2f}", "$0.07 per KB"),
        ]
    )

    st.subheader("Virtual Memory")
    metric_row(
        [
            ("Physical pages", f"{physical_memory.physical_pages:,}", None),
            ("System pages", f"{physical_memory.system_pages:,}", None),
            ("Mapped references", f"{vm_stats.virtual_pages_mapped:,}", None),
            ("Page hits", f"{vm_stats.page_hits:,}", None),
            ("Page faults", f"{vm_stats.page_faults:,}", None),
        ]
    )

    per_process = pd.DataFrame(
        {
            "process": [f"P{i}" for i in range(len(page_tables))],
            "mapped_pages": [len(table) for table in page_tables],
        }
    )
    st.bar_chart(per_process, x="process", y="mapped_pages", color="#2A9D8F")

    st.subheader("Cache Results")
    metric_row(
        [
            ("Accesses", f"{cache_stats.accesses:,}", None),
            ("Hits", f"{cache_stats.hits:,}", None),
            ("Misses", f"{cache_stats.misses:,}", None),
            ("Hit rate", f"{cache_stats.hit_rate:.2f}%", None),
            ("CPI", f"{cache_stats.cpi:.2f}", None),
        ]
    )

    misses = pd.DataFrame(
        {
            "miss_type": ["Compulsory", "Conflict"],
            "count": [cache_stats.compulsory_misses, cache_stats.conflict_misses],
        }
    )
    rates = pd.DataFrame(
        {
            "metric": ["Hit Rate", "Miss Rate"],
            "percent": [cache_stats.hit_rate, cache_stats.miss_rate],
        }
    )

    left, right = st.columns(2)
    left.write("Miss Breakdown")
    left.bar_chart(misses, x="miss_type", y="count", color="#6E56CF")
    right.write("Hit vs. Miss Rate")
    right.bar_chart(rates, x="metric", y="percent", color="#2F6FED")

    with st.expander("Raw result details"):
        st.json(
            {
                "cache": cache_stats.__dict__,
                "virtual_memory": vm_stats.__dict__,
                "physical_memory": physical_memory.__dict__,
                "cache_geometry": cache_geometry.__dict__,
            }
        )
else:
    st.info("Adjust the settings, paste or upload trace input, then run the simulation.")
