use anyhow::{Result, anyhow};
use csv::WriterBuilder;
use plotters::prelude::*;
use polars::prelude::*;
use rust_bench::bench_data::{
    scaled_hist_df, scaled_line_df, scaled_scatter_df, sliced_hist_df, sliced_line_df,
    sliced_scatter_df,
};
use rust_bench::benchmark_io::{run_id, utc_timestamp};
use std::collections::HashMap;
use std::fs::OpenOptions;
use std::time::Instant;

const OUTPUT_SIZE: (u32, u32) = (1280, 720);

fn expand_range(min: f64, max: f64) -> (f64, f64) {
    if (max - min).abs() < f64::EPSILON {
        (min - 1.0, max + 1.0)
    } else {
        (min, max)
    }
}

fn point_bounds(points: &[(f64, f64)]) -> Result<((f64, f64), (f64, f64))> {
    let mut iter = points.iter().copied();
    let (first_x, first_y) = iter
        .next()
        .ok_or_else(|| anyhow!("point series is empty"))?;

    let (mut min_x, mut max_x) = (first_x, first_x);
    let (mut min_y, mut max_y) = (first_y, first_y);

    for (x, y) in iter {
        min_x = min_x.min(x);
        max_x = max_x.max(x);
        min_y = min_y.min(y);
        max_y = max_y.max(y);
    }

    Ok((expand_range(min_x, max_x), expand_range(min_y, max_y)))
}

fn histogram(df: &DataFrame, output_name: &str) -> Result<f64> {
    let values: Vec<f64> = df.column("seconds")?.f64()?.into_no_null_iter().collect();
    let bin_count = 60usize;

    let mut iter = values.iter().copied();
    let first = iter
        .next()
        .ok_or_else(|| anyhow!("histogram source is empty"))?;

    let (mut min_value, mut max_value) = (first, first);
    for value in iter {
        min_value = min_value.min(value);
        max_value = max_value.max(value);
    }

    let (min_value, max_value) = expand_range(min_value, max_value);
    let bin_width = (max_value - min_value) / bin_count as f64;
    let mut counts = vec![0u32; bin_count];

    for value in values {
        let raw_index = ((value - min_value) / bin_width).floor() as isize;
        let clamped_index = raw_index.clamp(0, (bin_count - 1) as isize) as usize;
        counts[clamped_index] += 1;
    }

    let max_count = counts.iter().copied().max().unwrap_or(0);

    let start = Instant::now();

    let root = BitMapBackend::new(output_name, OUTPUT_SIZE).into_drawing_area();
    root.fill(&WHITE)?;

    let mut chart = ChartBuilder::on(&root)
        .caption("Distribution of ride times", ("sans-serif", 30))
        .margin(20)
        .x_label_area_size(40)
        .y_label_area_size(50)
        .build_cartesian_2d(min_value..max_value, 0u32..max_count.max(1))?;

    chart
        .configure_mesh()
        .x_desc("duration (seconds)")
        .y_desc("count")
        .draw()?;

    chart.draw_series(counts.iter().enumerate().map(|(index, count)| {
        let x0 = min_value + index as f64 * bin_width;
        let x1 = x0 + bin_width;
        Rectangle::new([(x0, 0u32), (x1, *count)], BLUE.mix(0.7).filled())
    }))?;

    root.present()?;

    Ok(start.elapsed().as_secs_f64())
}

fn line_chart(df: &DataFrame, output_name: &str) -> Result<f64> {
    let points: Vec<(f64, f64)> = df
        .column("unix_s")?
        .f64()?
        .into_no_null_iter()
        .zip(
            df.column("num_rides")?
                .u32()?
                .into_no_null_iter()
                .map(|value| value as f64),
        )
        .collect();
    let ((min_x, max_x), (min_y, max_y)) = point_bounds(&points)?;

    let start = Instant::now();

    let root = BitMapBackend::new(output_name, OUTPUT_SIZE).into_drawing_area();
    root.fill(&WHITE)?;

    let mut chart = ChartBuilder::on(&root)
        .caption("Rides over time", ("sans-serif", 30))
        .margin(20)
        .x_label_area_size(40)
        .y_label_area_size(50)
        .build_cartesian_2d(min_x..max_x, min_y..max_y)?;

    chart
        .configure_mesh()
        .x_desc("UNIX seconds")
        .y_desc("Number of rides")
        .draw()?;

    chart.draw_series(LineSeries::new(points.iter().copied(), &BLUE))?;

    root.present()?;

    Ok(start.elapsed().as_secs_f64())
}

fn scatter_chart(df: &DataFrame, output_name: &str) -> Result<f64> {
    let labels = df
        .column("rideable_type")?
        .str()?
        .into_no_null_iter()
        .collect::<Vec<_>>();
    let points: Vec<(f64, f64)> = df
        .column("distance")?
        .f64()?
        .into_no_null_iter()
        .zip(df.column("duration_seconds")?.f64()?.into_no_null_iter())
        .collect();
    let ((min_x, max_x), (min_y, max_y)) = point_bounds(&points)?;

    let start = Instant::now();

    let root = BitMapBackend::new(output_name, OUTPUT_SIZE).into_drawing_area();
    root.fill(&WHITE)?;

    let mut chart = ChartBuilder::on(&root)
        .caption("Rides over time", ("sans-serif", 30))
        .margin(20)
        .x_label_area_size(40)
        .y_label_area_size(50)
        .build_cartesian_2d(min_x..max_x, min_y..max_y)?;

    chart
        .configure_mesh()
        .x_desc("distance")
        .y_desc("duration (seconds)")
        .draw()?;

    let mut palette_indexes: HashMap<&str, usize> = HashMap::new();
    let mut next_index = 0usize;

    chart.draw_series(
        points
            .iter()
            .copied()
            .zip(labels.iter())
            .map(|((x, y), label)| {
                let idx = *palette_indexes.entry(*label).or_insert_with(|| {
                    let current = next_index;
                    next_index += 1;
                    current
                });

                Circle::new((x, y), 1, Palette99::pick(idx).filled())
            }),
    )?;

    root.present()?;

    Ok(start.elapsed().as_secs_f64())
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
        let result = sliced_line_df("../data/clean/85k_timeseries.parquet", size)
            .and_then(|df| line_chart(&df, &format!("output/plotters_{label}.png")));
        write_result(&mut writer, run_id.as_str(), "plotters", label, result)?;
    }

    let line_cases = [
        ("85k_line", 1usize),
        ("170k_line", 2usize),
        ("850k_line", 10usize),
    ];
    for (label, scale) in line_cases {
        let result = scaled_line_df("../data/clean/85k_timeseries.parquet", scale)
            .and_then(|df| line_chart(&df, &format!("output/plotters_{label}.png")));
        write_result(&mut writer, run_id.as_str(), "plotters", label, result)?;
    }

    let hist_slice_cases = [("2k_histogram", 2_000usize), ("10k_histogram", 10_000usize)];
    for (label, size) in hist_slice_cases {
        let result = sliced_hist_df("../data/clean/1m_histogram.parquet", size)
            .and_then(|df| histogram(&df, &format!("output/plotters_{label}.png")));
        write_result(&mut writer, run_id.as_str(), "plotters", label, result)?;
    }

    let hist_cases = [("1m_histogram", 1usize), ("10m_histogram", 10usize)];
    for (label, scale) in hist_cases {
        let result = scaled_hist_df("../data/clean/1m_histogram.parquet", scale)
            .and_then(|df| histogram(&df, &format!("output/plotters_{label}.png")));
        write_result(&mut writer, run_id.as_str(), "plotters", label, result)?;
    }

    let scatter_slice_cases = [("1k_scatter", 1_000usize), ("5k_scatter", 5_000usize)];
    for (label, size) in scatter_slice_cases {
        let result = sliced_scatter_df("../data/clean/500k_scatter.parquet", size)
            .and_then(|df| scatter_chart(&df, &format!("output/plotters_{label}.png")));
        write_result(&mut writer, run_id.as_str(), "plotters", label, result)?;
    }

    let scatter_cases = [("500k_scatter", 1usize), ("5m_scatter", 10usize)];
    for (label, scale) in scatter_cases {
        let result = scaled_scatter_df("../data/clean/500k_scatter.parquet", scale)
            .and_then(|df| scatter_chart(&df, &format!("output/plotters_{label}.png")));
        write_result(&mut writer, run_id.as_str(), "plotters", label, result)?;
    }

    writer.flush()?;

    Ok(())
}
