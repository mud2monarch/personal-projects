from __future__ import annotations

from functools import partial
from pathlib import Path

import altair as alt
import polars as pl

from bench_data import (
    scaled_hist_df,
    scaled_line_df,
    scaled_scatter_df,
    sliced_hist_df,
    sliced_line_df,
    sliced_scatter_df,
)

WIDTH = 1200
HEIGHT = 700
HIST_BINS = 60
SCATTER_COLORS = ["blue", "orange"]


def _save_chart(chart: alt.Chart, output_path: str | Path) -> Path:
    output = Path(output_path)
    chart.save(output)
    return output


def export_histogram_png(scale: int, output_path: str | Path) -> Path:
    df = scaled_hist_df("1m_histogram.parquet", scale)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("seconds:Q", bin=alt.Bin(maxbins=HIST_BINS), title="duration (seconds)"),
            y=alt.Y("count():Q", title="count"),
        )
        .properties(
            width=WIDTH,
            height=HEIGHT,
            title="Distribution of ride times",
        )
    )
    return _save_chart(chart, output_path)


def export_histogram_slice_png(size: int, output_path: str | Path) -> Path:
    df = sliced_hist_df("1m_histogram.parquet", size)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("seconds:Q", bin=alt.Bin(maxbins=HIST_BINS), title="duration (seconds)"),
            y=alt.Y("count():Q", title="count"),
        )
        .properties(
            width=WIDTH,
            height=HEIGHT,
            title="Distribution of ride times",
        )
    )
    return _save_chart(chart, output_path)


def export_line_png(scale: int, output_path: str | Path) -> Path:
    df = scaled_line_df("85k_timeseries.parquet", scale)
    chart = (
        alt.Chart(df)
        .mark_line(color="#1f77b4")
        .encode(
            x=alt.X("unix_s:Q", title="UNIX seconds"),
            y=alt.Y("num_rides:Q", title="Number of rides"),
        )
        .properties(
            width=WIDTH,
            height=HEIGHT,
            title="Rides over time",
        )
    )
    return _save_chart(chart, output_path)


def export_line_slice_png(size: int, output_path: str | Path) -> Path:
    df = sliced_line_df("85k_timeseries.parquet", size)
    chart = (
        alt.Chart(df)
        .mark_line(color="#1f77b4")
        .encode(
            x=alt.X("unix_s:Q", title="UNIX seconds"),
            y=alt.Y("num_rides:Q", title="Number of rides"),
        )
        .properties(
            width=WIDTH,
            height=HEIGHT,
            title="Rides over time",
        )
    )
    return _save_chart(chart, output_path)


def export_scatter_png(scale: int, output_path: str | Path) -> Path:
    df = scaled_scatter_df("500k_scatter.parquet", scale)
    chart = (
        alt.Chart(df)
        .mark_circle(size=9, opacity=0.6)
        .encode(
            x=alt.X("distance:Q", title="distance"),
            y=alt.Y("duration_seconds:Q", title="duration (seconds)"),
            color=alt.Color(
                "rideable_type:N",
                scale=alt.Scale(range=SCATTER_COLORS),
                title="rideable_type",
            ),
        )
        .properties(
            width=WIDTH,
            height=HEIGHT,
            title="Rides over time",
        )
    )
    return _save_chart(chart, output_path)


def export_scatter_slice_png(size: int, output_path: str | Path) -> Path:
    df = sliced_scatter_df("500k_scatter.parquet", size)
    chart = (
        alt.Chart(df)
        .mark_circle(size=9, opacity=0.6)
        .encode(
            x=alt.X("distance:Q", title="distance"),
            y=alt.Y("duration_seconds:Q", title="duration (seconds)"),
            color=alt.Color(
                "rideable_type:N",
                scale=alt.Scale(range=SCATTER_COLORS),
                title="rideable_type",
            ),
        )
        .properties(
            width=WIDTH,
            height=HEIGHT,
            title="Rides over time",
        )
    )
    return _save_chart(chart, output_path)


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
