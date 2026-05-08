use anyhow::Result;
use charton::prelude::*;
use csv::WriterBuilder;
use polars::prelude::*;
use std::{fs::OpenOptions, time::Instant};

fn hist(filepath: &str) -> Result<f64> {
    let df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .with_columns([col("duration").dt().total_seconds(true).alias("seconds")])
        .select([col("seconds")])
        .collect()?;

    let ds = load_polars_df!(df)?;

    let start = Instant::now();

    Chart::build(ds)?
        .mark_hist()?
        .encode((alt::x("seconds").with_bins(60), alt::y("count")))?
        .save("charton_histogram.png")?;

    let elapsed = start.elapsed().as_secs_f64();

    Ok(elapsed)
}

fn line(filepath: &str) -> Result<f64> {
    let df = LazyFrame::scan_parquet(filepath.into(), Default::default())?
        .select([col("dt_minute"), col("num_rides")])
        .sort(
            ["dt_minute"],
            SortMultipleOptions::new().with_order_descending(false),
        )
        .collect()?;

    let ds = load_polars_df!(df)?;

    let start = Instant::now();
    Chart::build(ds)?
        .mark_line()?
        .encode((alt::x("dt_minute"), alt::y("num_rides")))?
        .save("charton_line.png")?;

    let elapsed = start.elapsed().as_secs_f64();

    Ok(elapsed)
}

fn scatter(filepath: &str) -> Result<f64> {
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

    let ds = load_polars_df!(df)?;

    let start = Instant::now();
    Chart::build(ds)?
        .mark_point()?
        .configure_point(|c| c.with_size(0.5))
        .encode((
            alt::y("duration_seconds"),
            alt::x("distance"),
            alt::color("rideable_type"),
        ))?
        .save("charton_scatter.png")?;

    let elapsed = start.elapsed().as_secs_f64();

    Ok(elapsed)
}

fn main() -> Result<()> {
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("benchmark_results.csv")?;
    let mut writer = WriterBuilder::new().has_headers(true).from_writer(file);

    let hist_time = hist("../data/clean/1m_histogram.parquet")?;
    _ = writer.write_record(["charton", "1m_histogram", &hist_time.to_string()])?;

    let line_time = line("../data/clean/85k_timeseries.parquet")?;
    _ = writer.write_record(["charton", "85k_line", &line_time.to_string()])?;

    let scatter_time = scatter("../data/clean/500k_scatter.parquet")?;
    _ = writer.write_record(["charton", "500k_scatter", &scatter_time.to_string()])?;

    _ = writer.flush()?;

    Ok(())
}
