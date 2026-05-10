Python benchmark runners for Altair, Plotly, and Matplotlib.

Run from this directory with `uv`.

**Commands**

| Command | What it does |
| --- | --- |
| `uv run bench-all` | Runs all dataset benchmarks for `altair`, `matplotlib`, and `plotly`, with `4` runs each. |
| `uv run bench-altair` | Runs all dataset benchmarks for `altair`, with `4` runs. |
| `uv run bench-matplotlib` | Runs all dataset benchmarks for `matplotlib`, with `4` runs. |
| `uv run bench-plotly` | Runs all dataset benchmarks for `plotly`, with `4` runs. |
| `uv run bench-python` | Runs the Python CLI directly, so you can control libraries, datasets, and run count with flags. |

**CLI Flags**

| Flag | Values | Default | What it does |
| --- | --- | --- | --- |
| `--library` | `all`, `altair`, `matplotlib`, `plotly` | `all` | Selects which plotting library to benchmark. |
| `--runs` | Integer `>= 1` | `4` | Repeats the measured benchmark set this many times after one unrecorded warm-up pass. Each measured repetition appends more rows to the CSV output. |
| `--dataset` | `1k_line`, `5k_line`, `85k_line`, `170k_line`, `850k_line`, `2k_histogram`, `10k_histogram`, `1m_histogram`, `10m_histogram`, `1k_scatter`, `5k_scatter`, `500k_scatter`, `5m_scatter` | All datasets | Limits the run to one dataset per flag occurrence. Pass it multiple times to select multiple datasets. |

Each invocation writes PNGs into `outputs/`, performs one unrecorded warm-up pass, and appends measured benchmark results into `benchmark_runs.csv`.
