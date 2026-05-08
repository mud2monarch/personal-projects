use anyhow::{Context, Result, anyhow};
use csv::WriterBuilder;
use plotters::prelude::*;
use rust_bench::kuva_utils::{hist, line, scatter};
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

fn histogram(filepath: &str) -> Result<f64> {
    let values = hist(filepath)?;
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

    let root = BitMapBackend::new("plotters_histogram.png", OUTPUT_SIZE).into_drawing_area();
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

fn line_chart(filepath: &str) -> Result<f64> {
    let line_data = line(filepath)?;
    let ((min_x, max_x), (min_y, max_y)) = point_bounds(&line_data.points)?;

    let start = Instant::now();

    let root = BitMapBackend::new("plotters_line.png", OUTPUT_SIZE).into_drawing_area();
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

    chart.draw_series(LineSeries::new(line_data.points.iter().copied(), &BLUE))?;

    root.present()?;

    Ok(start.elapsed().as_secs_f64())
}

fn scatter_chart(filepath: &str) -> Result<f64> {
    let scatter_data = scatter(filepath)?;
    let labels = scatter_data
        .color_by
        .as_ref()
        .context("scatter plot labels are missing")?;
    let ((min_x, max_x), (min_y, max_y)) = point_bounds(&scatter_data.points)?;

    let start = Instant::now();

    let root = BitMapBackend::new("plotters_scatter.png", OUTPUT_SIZE).into_drawing_area();
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
        scatter_data
            .points
            .iter()
            .copied()
            .zip(labels.iter())
            .map(|((x, y), label)| {
                let idx = *palette_indexes.entry(label.as_str()).or_insert_with(|| {
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

fn main() -> Result<()> {
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("benchmark_results.csv")?;
    let mut writer = WriterBuilder::new().has_headers(true).from_writer(file);

    let hist_time = histogram("../data/clean/1m_histogram.parquet")?;
    writer.write_record(["plotters", "1m_histogram", &hist_time.to_string()])?;

    let line_time = line_chart("../data/clean/85k_timeseries.parquet")?;
    writer.write_record(["plotters", "85k_line", &line_time.to_string()])?;

    let scatter_time = scatter_chart("../data/clean/500k_scatter.parquet")?;
    writer.write_record(["plotters", "500k_scatter", &scatter_time.to_string()])?;

    writer.flush()?;

    Ok(())
}
