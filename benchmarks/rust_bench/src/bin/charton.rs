use anyhow::Result;
use charton::prelude::*;
use csv::WriterBuilder;
use rust_bench::bench_data::{
    scaled_hist_df, scaled_line_df, scaled_scatter_df, sliced_hist_df, sliced_line_df,
    sliced_scatter_df,
};
use rust_bench::benchmark_io::{run_id, utc_timestamp};
use std::{fs::OpenOptions, time::Instant};

fn hist(filepath: &str, scale: usize, output_name: &str) -> Result<f64> {
    let df = scaled_hist_df(filepath, scale)?;
    let start = Instant::now();
    let ds = load_polars_df!(df)?;

    Chart::build(ds)?
        .mark_hist()?
        .encode((alt::x("seconds").with_bins(60), alt::y("count")))?
        .save(output_name)?;

    let elapsed = start.elapsed().as_secs_f64();

    Ok(elapsed)
}

fn line(filepath: &str, scale: usize, output_name: &str) -> Result<f64> {
    let df = scaled_line_df(filepath, scale)?;
    let start = Instant::now();
    let ds = load_polars_df!(df)?;

    Chart::build(ds)?
        .mark_line()?
        .encode((alt::x("unix_s"), alt::y("num_rides")))?
        .save(output_name)?;

    let elapsed = start.elapsed().as_secs_f64();

    Ok(elapsed)
}

fn scatter(filepath: &str, scale: usize, output_name: &str) -> Result<f64> {
    let df = scaled_scatter_df(filepath, scale)?;
    let start = Instant::now();
    let ds = load_polars_df!(df)?;

    Chart::build(ds)?
        .mark_point()?
        .configure_point(|c| c.with_size(0.5))
        .encode((
            alt::y("duration_seconds"),
            alt::x("distance"),
            alt::color("rideable_type"),
        ))?
        .save(output_name)?;

    let elapsed = start.elapsed().as_secs_f64();

    Ok(elapsed)
}

fn write_result(
    writer: &mut csv::Writer<std::fs::File>,
    run_id: &str,
    library: &str,
    benchmark: &str,
    result: Result<f64>,
) -> Result<()> {
    let ts = utc_timestamp()?;
    match result {
        Ok(elapsed) => writer.write_record([
            run_id,
            ts.as_str(),
            library,
            benchmark,
            "ok",
            &elapsed.to_string(),
            "",
        ])?,
        Err(err) => writer.write_record([
            run_id,
            ts.as_str(),
            library,
            benchmark,
            "error",
            "",
            &err.to_string(),
        ])?,
    }

    Ok(())
}

fn main() -> Result<()> {
    let run_id = run_id();
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("benchmark_results.csv")?;
    let mut writer = WriterBuilder::new().has_headers(true).from_writer(file);

    let line_slice_cases = [("1k_line", 1_000usize), ("5k_line", 5_000usize)];
    for (label, size) in line_slice_cases {
        let result = sliced_line_df("../data/clean/85k_timeseries.parquet", size).and_then(|df| {
            let start = Instant::now();
            let ds = load_polars_df!(df)?;

            Chart::build(ds)?
                .mark_line()?
                .encode((alt::x("unix_s"), alt::y("num_rides")))?
                .save(&format!("output/charton_{label}.png"))?;

            Ok(start.elapsed().as_secs_f64())
        });
        write_result(&mut writer, run_id.as_str(), "charton", label, result)?;
    }

    let line_cases = [
        ("85k_line", 1usize),
        ("170k_line", 2usize),
        ("850k_line", 10usize),
    ];
    for (label, scale) in line_cases {
        let result = line(
            "../data/clean/85k_timeseries.parquet",
            scale,
            &format!("output/charton_{label}.png"),
        );
        write_result(&mut writer, run_id.as_str(), "charton", label, result)?;
    }

    let hist_slice_cases = [("2k_histogram", 2_000usize), ("10k_histogram", 10_000usize)];
    for (label, size) in hist_slice_cases {
        let result = sliced_hist_df("../data/clean/1m_histogram.parquet", size).and_then(|df| {
            let start = Instant::now();
            let ds = load_polars_df!(df)?;

            Chart::build(ds)?
                .mark_hist()?
                .encode((alt::x("seconds").with_bins(60), alt::y("count")))?
                .save(&format!("output/charton_{label}.png"))?;

            Ok(start.elapsed().as_secs_f64())
        });
        write_result(&mut writer, run_id.as_str(), "charton", label, result)?;
    }

    let hist_cases = [("1m_histogram", 1usize), ("10m_histogram", 10usize)];
    for (label, scale) in hist_cases {
        let result = hist(
            "../data/clean/1m_histogram.parquet",
            scale,
            &format!("output/charton_{label}.png"),
        );
        write_result(&mut writer, run_id.as_str(), "charton", label, result)?;
    }

    let scatter_slice_cases = [("1k_scatter", 1_000usize), ("5k_scatter", 5_000usize)];
    for (label, size) in scatter_slice_cases {
        let result = sliced_scatter_df("../data/clean/500k_scatter.parquet", size).and_then(|df| {
            let start = Instant::now();
            let ds = load_polars_df!(df)?;

            Chart::build(ds)?
                .mark_point()?
                .configure_point(|c| c.with_size(0.5))
                .encode((
                    alt::y("duration_seconds"),
                    alt::x("distance"),
                    alt::color("rideable_type"),
                ))?
                .save(&format!("output/charton_{label}.png"))?;

            Ok(start.elapsed().as_secs_f64())
        });
        write_result(&mut writer, run_id.as_str(), "charton", label, result)?;
    }

    let scatter_cases = [("500k_scatter", 1usize), ("5m_scatter", 10usize)];
    for (label, scale) in scatter_cases {
        let result = scatter(
            "../data/clean/500k_scatter.parquet",
            scale,
            &format!("output/charton_{label}.png"),
        );
        write_result(&mut writer, run_id.as_str(), "charton", label, result)?;
    }

    writer.flush()?;

    Ok(())
}
