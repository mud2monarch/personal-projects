from __future__ import annotations

from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"


def _load_dataset(filename: str) -> pl.DataFrame:
    return pl.read_parquet(DATA_DIR / filename)


def _repeat_df(base_df: pl.DataFrame, scale: int, transform) -> pl.DataFrame:
    if scale < 1:
        raise ValueError("scale must be at least 1")

    frames = [transform(base_df.clone(), 0)]
    for idx in range(1, scale):
        frames.append(transform(base_df.clone(), idx))
    return pl.concat(frames, how="vertical")


def scaled_hist_df(filename: str, scale: int) -> pl.DataFrame:
    base_df = _load_dataset(filename).select(
        pl.col("duration").dt.total_seconds().cast(pl.Float64).alias("seconds")
    )
    return _repeat_df(base_df, scale, lambda df, _: df)


def sliced_hist_df(filename: str, size: int) -> pl.DataFrame:
    return _load_dataset(filename).select(
        pl.col("duration").dt.total_seconds().cast(pl.Float64).alias("seconds")
    ).slice(0, size)


def scaled_scatter_df(filename: str, scale: int) -> pl.DataFrame:
    base_df = _load_dataset(filename).select(
        pl.col("rideable_type").cast(pl.String),
        pl.col("distance"),
        pl.col("duration").dt.total_seconds().cast(pl.Float64).alias("duration_seconds"),
    )

    def transform(df: pl.DataFrame, idx: int) -> pl.DataFrame:
        offset = idx * 1e-6
        return df.with_columns(
            (pl.col("distance") + offset).alias("distance"),
            (pl.col("duration_seconds") + offset).alias("duration_seconds"),
        )

    return _repeat_df(base_df, scale, transform)


def sliced_scatter_df(filename: str, size: int) -> pl.DataFrame:
    return _load_dataset(filename).select(
        pl.col("rideable_type").cast(pl.String),
        pl.col("distance"),
        pl.col("duration").dt.total_seconds().cast(pl.Float64).alias("duration_seconds"),
    ).slice(0, size)


def scaled_line_df(filename: str, scale: int) -> pl.DataFrame:
    base_df = (
        _load_dataset(filename)
        .select(
            (
                pl.col("dt_minute").dt.epoch("ms").cast(pl.Float64) / 1000.0
            ).alias("unix_s"),
            pl.col("num_rides"),
        )
        .sort("unix_s")
    )

    min_x = base_df["unix_s"].min()
    max_x = base_df["unix_s"].max()
    if min_x is None or max_x is None:
        raise ValueError("line dataframe is empty")
    span = (max_x - min_x) + 60.0

    def transform(df: pl.DataFrame, idx: int) -> pl.DataFrame:
        shift = span * idx
        return df.with_columns((pl.col("unix_s") + shift).alias("unix_s"))

    return _repeat_df(base_df, scale, transform).sort("unix_s")


def sliced_line_df(filename: str, size: int) -> pl.DataFrame:
    return (
        _load_dataset(filename)
        .select(
            (
                pl.col("dt_minute").dt.epoch("ms").cast(pl.Float64) / 1000.0
            ).alias("unix_s"),
            pl.col("num_rides"),
        )
        .sort("unix_s")
        .slice(0, size)
    )
