from __future__ import annotations

from functools import partial
from pathlib import Path

import polars as pl

from bench_data import (
    scaled_hist_df,
    scaled_line_df,
    scaled_scatter_df,
    sliced_hist_df,
    sliced_line_df,
    sliced_scatter_df,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
FIGSIZE = (12, 7)
DPI = 150
HIST_BINS = 60
SCATTER_COLORS = {
    "classic_bike": "blue",
    "electric_bike": "orange",
}


def _load_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _load_dataset(filename: str) -> pl.DataFrame:
    return pl.read_parquet(DATA_DIR / filename)


def _duration_minutes_expr(column: str) -> pl.Expr:
    return pl.col(column).dt.total_milliseconds().cast(pl.Float64) / 60_000.0


def export_histogram_png(scale: int, output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = scaled_hist_df("1m_histogram.parquet", scale)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.hist(df["seconds"].to_list(), bins=HIST_BINS, color="#1f77b4", edgecolor="white")
    ax.set_title("Distribution of ride times")
    ax.set_xlabel("duration (seconds)")
    ax.set_ylabel("count")
    ax.grid(alpha=0.2)

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def export_histogram_slice_png(size: int, output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = sliced_hist_df("1m_histogram.parquet", size)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.hist(df["seconds"].to_list(), bins=HIST_BINS, color="#1f77b4", edgecolor="white")
    ax.set_title("Distribution of ride times")
    ax.set_xlabel("duration (seconds)")
    ax.set_ylabel("count")
    ax.grid(alpha=0.2)

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def export_line_png(scale: int, output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = scaled_line_df("85k_timeseries.parquet", scale)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.plot(df["unix_s"].to_list(), df["num_rides"].to_list(), linewidth=1.4, color="#1f77b4")
    ax.set_title("Rides over time")
    ax.set_xlabel("UNIX seconds")
    ax.set_ylabel("Number of rides")
    ax.grid(alpha=0.2)

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def export_line_slice_png(size: int, output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = sliced_line_df("85k_timeseries.parquet", size)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.plot(df["unix_s"].to_list(), df["num_rides"].to_list(), linewidth=1.4, color="#1f77b4")
    ax.set_title("Rides over time")
    ax.set_xlabel("UNIX seconds")
    ax.set_ylabel("Number of rides")
    ax.grid(alpha=0.2)

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def export_scatter_png(scale: int, output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = scaled_scatter_df("500k_scatter.parquet", scale)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    for rideable_type in ("classic_bike", "electric_bike"):
        group = df.filter(df["rideable_type"] == rideable_type)
        ax.scatter(
            group["distance"].to_list(),
            group["duration_seconds"].to_list(),
            s=1,
            label=rideable_type,
            color=SCATTER_COLORS[rideable_type],
        )

    ax.set_title("Rides over time")
    ax.set_xlabel("distance")
    ax.set_ylabel("duration (seconds)")
    ax.grid(alpha=0.2)
    ax.legend()

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


def export_scatter_slice_png(size: int, output_path: str | Path) -> Path:
    plt = _load_matplotlib()
    df = sliced_scatter_df("500k_scatter.parquet", size)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    for rideable_type in ("classic_bike", "electric_bike"):
        group = df.filter(df["rideable_type"] == rideable_type)
        ax.scatter(
            group["distance"].to_list(),
            group["duration_seconds"].to_list(),
            s=1,
            label=rideable_type,
            color=SCATTER_COLORS[rideable_type],
        )

    ax.set_title("Rides over time")
    ax.set_xlabel("distance")
    ax.set_ylabel("duration (seconds)")
    ax.grid(alpha=0.2)
    ax.legend()

    output = Path(output_path)
    fig.tight_layout()
    fig.savefig(output, format="png")
    plt.close(fig)
    return output


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


def _scatter_dataset_chart(filename: str, title: str, output_path: str | Path) -> Path:
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
            s=8,
            alpha=0.5,
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
    return _scatter_dataset_chart("50k_scatter.parquet", "50k Scatter", output_path)


def export_500k_scatter_png(output_path: str | Path) -> Path:
    return _scatter_dataset_chart("500k_scatter.parquet", "500k Scatter", output_path)


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
    "1k_line": partial(export_line_slice_png, 1_000),
    "5k_line": partial(export_line_slice_png, 5_000),
    "85k_line": partial(export_line_png, 1),
    "170k_line": partial(export_line_png, 2),
    "850k_line": partial(export_line_png, 10),
    "2k_histogram": partial(export_histogram_slice_png, 2_000),
    "10k_histogram": partial(export_histogram_slice_png, 10_000),
    "1m_histogram": partial(export_histogram_png, 1),
    "10m_histogram": partial(export_histogram_png, 10),
    "1k_scatter": partial(export_scatter_slice_png, 1_000),
    "5k_scatter": partial(export_scatter_slice_png, 5_000),
    "500k_scatter": partial(export_scatter_png, 1),
    "5m_scatter": partial(export_scatter_png, 10),
}
