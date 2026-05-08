from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import polars as pl

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
WIDTH = 1440
HEIGHT = 840
HIST_BINS = 60


def _load_dataset(filename: str) -> pl.DataFrame:
    return pl.read_parquet(DATA_DIR / filename)


def _duration_minutes_expr(column: str) -> pl.Expr:
    return pl.col(column).dt.total_milliseconds().cast(pl.Float64) / 60_000.0


def _write_png(fig, output_path: str | Path) -> Path:
    output = Path(output_path)
    fig.write_image(output, format="png", width=WIDTH, height=HEIGHT, scale=1)
    return output


def export_100k_histogram_png(output_path: str | Path) -> Path:
    df = _load_dataset("100k_histogram.parquet").select(
        _duration_minutes_expr("duration").alias("duration_minutes")
    )

    fig = go.Figure(
        data=[
            go.Histogram(
                x=df["duration_minutes"].to_list(),
                nbinsx=HIST_BINS,
                marker_color="#1f77b4",
            )
        ]
    )
    fig.update_layout(title="100k Histogram", xaxis_title="Duration (minutes)", yaxis_title="Count")
    return _write_png(fig, output_path)


def export_1m_histogram_png(output_path: str | Path) -> Path:
    df = _load_dataset("1m_histogram.parquet").select(
        _duration_minutes_expr("duration").alias("duration_minutes")
    )

    fig = go.Figure(
        data=[
            go.Histogram(
                x=df["duration_minutes"].to_list(),
                nbinsx=HIST_BINS,
                marker_color="#ff7f0e",
            )
        ]
    )
    fig.update_layout(title="1M Histogram", xaxis_title="Duration (minutes)", yaxis_title="Count")
    return _write_png(fig, output_path)


def _scatter_chart(filename: str, title: str, output_path: str | Path) -> Path:
    df = _load_dataset(filename).with_columns(
        _duration_minutes_expr("duration").alias("duration_minutes")
    )

    fig = go.Figure()
    for rideable_type, group in df.partition_by("rideable_type", as_dict=True).items():
        label = rideable_type[0] if isinstance(rideable_type, tuple) else rideable_type
        fig.add_trace(
            go.Scattergl(
                x=group["distance"].to_list(),
                y=group["duration_minutes"].to_list(),
                mode="markers",
                name=str(label),
                opacity=0.5,
                marker={"size": 4},
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Distance",
        yaxis_title="Duration (minutes)",
        legend_title="Rideable type",
    )
    return _write_png(fig, output_path)


def export_50k_scatter_png(output_path: str | Path) -> Path:
    return _scatter_chart("50k_scatter.parquet", "50k Scatter", output_path)


def export_500k_scatter_png(output_path: str | Path) -> Path:
    return _scatter_chart("500k_scatter.parquet", "500k Scatter", output_path)


def export_85k_timeseries_png(output_path: str | Path) -> Path:
    df = _load_dataset("85k_timeseries.parquet").sort("dt_minute")

    fig = go.Figure()
    for rideable_type, group in df.partition_by("rideable_type", as_dict=True).items():
        label = rideable_type[0] if isinstance(rideable_type, tuple) else rideable_type
        ordered = group.sort("dt_minute")
        fig.add_trace(
            go.Scatter(
                x=ordered["dt_minute"].to_list(),
                y=ordered["num_rides"].to_list(),
                mode="lines",
                name=str(label),
            )
        )
    fig.update_layout(
        title="85k Timeseries",
        xaxis_title="Datetime",
        yaxis_title="Number of rides",
        legend_title="Rideable type",
    )
    return _write_png(fig, output_path)


EXPORTS = {
    "100k_histogram": export_100k_histogram_png,
    "1m_histogram": export_1m_histogram_png,
    "50k_scatter": export_50k_scatter_png,
    "500k_scatter": export_500k_scatter_png,
    "85k_timeseries": export_85k_timeseries_png,
}
