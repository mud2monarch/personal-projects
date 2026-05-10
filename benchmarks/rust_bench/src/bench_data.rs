use std::ops::Div;

use anyhow::{Result, anyhow};
use polars::prelude::*;

fn repeat_df<F>(base_df: &DataFrame, scale: usize, mut transform: F) -> Result<DataFrame>
where
    F: FnMut(LazyFrame, usize) -> LazyFrame,
{
    if scale == 0 {
        return Err(anyhow!("scale must be at least 1"));
    }

    let mut stacked = transform(base_df.clone().lazy(), 0).collect()?;
    for idx in 1..scale {
        let next = transform(base_df.clone().lazy(), idx).collect()?;
        stacked.vstack_mut(&next)?;
    }

    Ok(stacked)
}

pub fn scaled_hist_df(filepath: &str, scale: usize) -> Result<DataFrame> {
    let base_df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .with_columns([col("duration").dt().total_seconds(true).alias("seconds")])
        .select([col("seconds")])
        .collect()?;

    repeat_df(&base_df, scale, |lf, _| lf)
}

pub fn sliced_hist_df(filepath: &str, size: usize) -> Result<DataFrame> {
    Ok(
        LazyFrame::scan_parquet(filepath.into(), Default::default())?
            .with_columns([col("duration").dt().total_seconds(true).alias("seconds")])
            .select([col("seconds")])
            .slice(0, size as IdxSize)
            .collect()?,
    )
}

pub fn scaled_scatter_df(filepath: &str, scale: usize) -> Result<DataFrame> {
    let base_df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .select([col("rideable_type"), col("distance"), col("duration")])
        .with_columns([
            col("duration")
                .dt()
                .total_seconds(true)
                .alias("duration_seconds"),
            col("rideable_type").cast(DataType::String),
        ])
        .select([
            col("rideable_type"),
            col("distance"),
            col("duration_seconds"),
        ])
        .collect()?;

    repeat_df(&base_df, scale, |lf, idx| {
        let offset = idx as f64 * 1e-6;
        lf.with_columns([
            (col("distance") + lit(offset)).alias("distance"),
            (col("duration_seconds") + lit(offset)).alias("duration_seconds"),
        ])
    })
}

pub fn sliced_scatter_df(filepath: &str, size: usize) -> Result<DataFrame> {
    Ok(
        LazyFrame::scan_parquet(filepath.into(), Default::default())?
            .select([col("rideable_type"), col("distance"), col("duration")])
            .with_columns([
                col("duration")
                    .dt()
                    .total_seconds(true)
                    .alias("duration_seconds"),
                col("rideable_type").cast(DataType::String),
            ])
            .select([
                col("rideable_type"),
                col("distance"),
                col("duration_seconds"),
            ])
            .slice(0, size as IdxSize)
            .collect()?,
    )
}

pub fn scaled_line_df(filepath: &str, scale: usize) -> Result<DataFrame> {
    let base_df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .select([col("dt_minute"), col("num_rides")])
        .with_columns([col("dt_minute")
            .dt()
            .timestamp(TimeUnit::Milliseconds)
            .cast(DataType::Float64)
            .div(lit(1000.0))
            .alias("unix_s")])
        .select([col("unix_s"), col("num_rides")])
        .sort(
            ["unix_s"],
            SortMultipleOptions::new().with_order_descending(false),
        )
        .collect()?;

    let unix_s = base_df.column("unix_s")?.f64()?;
    let min_x = unix_s
        .min()
        .ok_or_else(|| anyhow!("line dataframe is empty"))?;
    let max_x = unix_s
        .max()
        .ok_or_else(|| anyhow!("line dataframe is empty"))?;
    let span = (max_x - min_x) + 60.0;

    Ok(repeat_df(&base_df, scale, |lf, idx| {
        let shift = span * idx as f64;
        lf.with_columns([(col("unix_s") + lit(shift)).alias("unix_s")])
    })?
    .lazy()
    .sort(
        ["unix_s"],
        SortMultipleOptions::new().with_order_descending(false),
    )
    .collect()?)
}

pub fn sliced_line_df(filepath: &str, size: usize) -> Result<DataFrame> {
    Ok(
        LazyFrame::scan_parquet(filepath.into(), Default::default())?
            .select([col("dt_minute"), col("num_rides")])
            .with_columns([col("dt_minute")
                .dt()
                .timestamp(TimeUnit::Milliseconds)
                .cast(DataType::Float64)
                .div(lit(1000.0))
                .alias("unix_s")])
            .select([col("unix_s"), col("num_rides")])
            .sort(
                ["unix_s"],
                SortMultipleOptions::new().with_order_descending(false),
            )
            .slice(0, size as IdxSize)
            .collect()?,
    )
}
