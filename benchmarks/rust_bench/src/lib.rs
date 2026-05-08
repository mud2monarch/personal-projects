use std::ops::Div;

use anyhow::Result;
use polars::prelude::*;

// Kuva expects histogram as a Vec<f64>
pub fn kuva_hist(filepath: &str) -> Result<Vec<f64>> {
    let df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .select([col("duration")])
        .with_columns([col("duration")
            .dt()
            .total_seconds(true)
            .alias("duration_seconds")])
        .collect()?;

    let values: Vec<f64> = df
        .column("duration_seconds")?
        .f64()?
        .into_no_null_iter()
        .collect();

    Ok(values)
}

pub struct ScatterPlot {
    pub points: Vec<(f64, f64)>,
    pub color_by: Option<Vec<String>>,
}

pub fn kuva_scatter(filepath: &str) -> Result<ScatterPlot> {
    let df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .select([col("rideable_type"), col("distance"), col("duration")])
        .with_columns([
            col("duration")
                .dt()
                .total_seconds(true)
                .alias("duration_seconds"),
            col("rideable_type").cast(DataType::String),
        ])
        .collect()?;

    let points: Vec<(f64, f64)> = df
        .column("distance")?
        .f64()?
        .into_no_null_iter()
        .zip(df.column("duration_seconds")?.f64()?.into_no_null_iter())
        .collect();

    let values_labels: Vec<String> = df
        .column("rideable_type")?
        .str()?
        .into_no_null_iter()
        .map(|s| s.to_string())
        .collect();

    Ok(ScatterPlot {
        points,
        color_by: Some(values_labels),
    })
}

pub fn kuva_line(filepath: &str) -> Result<ScatterPlot> {
    let df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .select([col("dt_minute"), col("num_rides")])
        .with_columns([col("dt_minute")
            .dt()
            .timestamp(TimeUnit::Milliseconds)
            .cast(DataType::Float64)
            .div(lit(1000.0))
            .alias("unix_s")])
        .sort(
            ["unix_s"],
            SortMultipleOptions::new().with_order_descending(false),
        )
        .collect()?;

    let points: Vec<(f64, f64)> = df
        .column("unix_s")?
        .f64()?
        .into_no_null_iter()
        .zip(
            df.column("num_rides")?
                .u32()?
                .into_no_null_iter()
                .map(|f| f as f64),
        )
        .collect();

    Ok(ScatterPlot {
        points,
        color_by: None,
    })
}
