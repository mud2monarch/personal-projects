from __future__ import annotations

from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
FIGSIZE = (12, 7)
DPI = 150
HIST_BINS = 60
SCATTER_ALPHA = 0.5
SCATTER_SIZE = 8


def _load_dataset(filename: str) -> pl.DataFrame:
    return pl.read_parquet(DATA_DIR / filename)


def _duration_minutes_expr(column: str) -> pl.Expr:
    return pl.col(column).dt.total_milliseconds().cast(pl.Float64) / 60_000.0


def _load_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def export_100k_histogram_png(output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = _load_dataset("100k_histogram.parquet").select(
        _duration_minutes_expr("duration").alias("duration_minutes")
    )

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.hist(df["duration_minutes"].to_list(), bins=HIST_BINS, color="#1f77b4", edgecolor="white")
    ax.set_title("100k Histogram")
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Count")
    ax.grid(alpha=0.2)

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def export_1m_histogram_png(output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = _load_dataset("1m_histogram.parquet").select(
        _duration_minutes_expr("duration").alias("duration_minutes")
    )

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.hist(df["duration_minutes"].to_list(), bins=HIST_BINS, color="#ff7f0e", edgecolor="white")
    ax.set_title("1M Histogram")
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Count")
    ax.grid(alpha=0.2)

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def _scatter_chart(filename: str, title: str, output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = _load_dataset(filename).with_columns(
        _duration_minutes_expr("duration").alias("duration_minutes")
    )

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    for rideable_type, group in df.partition_by("rideable_type", as_dict=True).items():
        label = rideable_type[0] if isinstance(rideable_type, tuple) else rideable_type
        ax.scatter(
            group["distance"].to_list(),
            group["duration_minutes"].to_list(),
            s=SCATTER_SIZE,
            alpha=SCATTER_ALPHA,
            label=str(label),
        )

    ax.set_title(title)
    ax.set_xlabel("Distance")
    ax.set_ylabel("Duration (minutes)")
    ax.grid(alpha=0.2)
    ax.legend()

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def export_50k_scatter_png(output_path: str | Path) -> Path:
    return _scatter_chart("50k_scatter.parquet", "50k Scatter", output_path)


def export_500k_scatter_png(output_path: str | Path) -> Path:
    return _scatter_chart("500k_scatter.parquet", "500k Scatter", output_path)


def export_85k_timeseries_png(output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = _load_dataset("85k_timeseries.parquet").sort("dt_minute")

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    for rideable_type, group in df.partition_by("rideable_type", as_dict=True).items():
        label = rideable_type[0] if isinstance(rideable_type, tuple) else rideable_type
        ordered = group.sort("dt_minute")
        ax.plot(
            ordered["dt_minute"].to_list(),
            ordered["num_rides"].to_list(),
            linewidth=1.4,
            label=str(label),
        )

    ax.set_title("85k Timeseries")
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Number of rides")
    ax.grid(alpha=0.2)
    ax.legend()

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


EXPORTS = {
    "100k_histogram": export_100k_histogram_png,
    "1m_histogram": export_1m_histogram_png,
    "50k_scatter": export_50k_scatter_png,
    "500k_scatter": export_500k_scatter_png,
    "85k_timeseries": export_85k_timeseries_png,
}
